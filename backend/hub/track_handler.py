"""Provide TrackHandler for handing and distributing tracks."""

from __future__ import annotations
from hub.exceptions import ErrorDictException
import numpy
import asyncio
import logging
from typing import Coroutine, Literal, TYPE_CHECKING
from aiortc.mediastreams import (
    MediaStreamTrack,
    MediaStreamError,
    AudioStreamTrack,
    VideoStreamTrack,
)
from av import VideoFrame, AudioFrame
from aiortc.contrib.media import MediaRelay

from filters import (
    filter_factory,
    FilterDict,
    Filter,
    MuteAudioFilter,
    MuteVideoFilter,
    FilterDataDict,
)
from group_filters import GroupFilter, group_filter_factory, group_filter_utils
from time import time

if TYPE_CHECKING:
    from connection.connection import Connection
    from filter_api import FilterAPIInterface


class TrackHandler(MediaStreamTrack):
    """Handles and distributes an incoming audio track to multiple subscribers."""

    kind = Literal["unknown", "audio", "video"]
    connection: Connection
    filter_api: FilterAPIInterface

    _muted: bool
    _track: MediaStreamTrack
    _relay: MediaRelay
    _mute_filter: MuteAudioFilter | MuteVideoFilter
    _filters: dict[str, Filter]
    _group_filters: dict[str, GroupFilter]
    _execute_filters: bool
    _execute_group_filters: bool
    _logger: logging.Logger
    __lock: asyncio.Lock

    def __init__(
        self,
        kind: Literal["audio", "video"],
        connection: Connection,
        filter_api: FilterAPIInterface,
        track: MediaStreamTrack | None = None,
        muted: bool = False,
    ) -> None:
        """Initialize new TrackHandler for `track`.

        Parameters
        ----------
        kind : str, "audio" or "video"
            Kind of MediaStreamTrack this handler handles.
        connection : hub.connection.Connection
            Connection this track handler belongs to.
        filter_api : subclass of hub.filter_api_interface.FilterAPIInterface
            Filter API for filters.
        track : aiortc.mediastreams.MediaStreamTrack
            Track this handler should manage and distribute.  None if track is set
            later.
        muted : bool, default False
            Whether this track should be muted.

        Raises
        ------
        ValueError
            If kind is not "audio" or "video".

        Notes
        -----
        Make sure to call `complete_setup` after initialization, when `incoming_audio`
        and `incoming_video` of connection are initialized.
        """
        super().__init__()
        self.filter_api = filter_api
        self._logger = logging.getLogger(f"{kind.capitalize()}TrackHandler")
        self.__lock = asyncio.Lock()
        self.kind = kind
        if track is not None:
            self._track = track
        elif kind == "video":
            self._track = VideoStreamTrack()
        elif kind == "audio":
            self._track = AudioStreamTrack()
        else:
            raise ValueError(
                f'Invalid kind: "{kind}". Accepted values: "audio" or "video"'
            )

        self._muted = muted
        self.connection = connection
        self._relay = MediaRelay()
        self._execute_filters = True
        self._filters = {}
        self._execute_group_filters = True
        self._group_filters = {}

        # Forward the ended event to this handler.
        self._track.add_listener("ended", self.stop)

    async def complete_setup(
        self, filters: list[FilterDict], group_filters: list[FilterDict]
    ) -> None:
        """Complete setup of TrackHandler.

        Initializes filter used to mute track and sets filter pipeline according to
        `filters and `group_filters`.

        Parameters
        ----------
        filters : list of filters.FilterDict
        group_filters : list of filters.FilterDict
        """

        self._mute_filter = filter_factory.init_mute_filter(
            self.kind, self.connection.incoming_audio, self.connection.incoming_video
        )

        group_filter_ports = []
        for _ in group_filters:
            group_filter_ports.append(
                (
                    group_filter_utils.find_an_available_port(),  # To send individual data to the aggragator
                    group_filter_utils.find_an_available_port(),  # To send the aggregation result to each participant
                )
            )

        await self.set_filters(filters)
        await self.set_group_filters(group_filters, group_filter_ports)

    @property
    def track(self) -> MediaStreamTrack:
        """Get source track for this TrackHandler.

        Notes
        -----
        Use `subscribe` to add a subscriber to this track.
        """
        return self._track

    @property
    def filters(self) -> dict[str, Filter]:
        """Get filters used by this TrackHandler."""
        return self._filters

    @property
    def group_filters(self) -> dict[str, GroupFilter]:
        """Get group filters used by this TrackHandler."""
        return self._group_filters

    @property
    def muted(self) -> bool:
        """Get muted state of TrackHandler."""
        return self._muted

    @muted.setter
    def muted(self, value: bool) -> None:
        """Set muted state of TrackHandler."""
        self._muted = value
        self.reset_execute_filters()

    async def stop(self) -> None:
        """Stop TrackHandler and associated track."""
        super().stop()
        coros = [
            f.cleanup()
            for f in list(self._filters.values()) + list(self._group_filters.values())
        ]
        await asyncio.gather(*coros)

    async def set_track(self, value: MediaStreamTrack):
        """Replace source track for this TrackHandler.

        Parameters
        ----------
        value : MediaStreamTrack
            New source track for this TrackHandler.  `kind` of value must match the kind
            of this TrackHandler.

        Raises
        ------
        ValueError
            If `kind` of value doesn't match the kind of this TrackHandler.
        """
        if value.kind != self.kind:
            raise ValueError(
                f"Source track for TrackHandler must be of kind: {self.kind}"
            )

        async with self.__lock:
            previous = self._track
            previous.remove_listener("ended", self.stop)
            self._track = value
            self._track.add_listener("ended", self.stop)
            previous.stop()

    def subscribe(self) -> MediaStreamTrack:
        """Subscribe to the track managed by this handler.

        Creates a new proxy which relays the track.  This is required to add multiple
        subscribers to one track.

        Returns
        -------
        aiortc.mediastreams.MediaStreamTrack
            Proxy track for the track this TrackHandler manages.

        Notes
        -----
        If this track needs to be used somewhere, always use subscribe to create an
        proxy!  If this TrackHandler is used directly, the framerate will be divided
        between the new consumer and all existing subscribers.
        """
        return self._relay.subscribe(self, False)

    async def set_filters(self, filter_configs: list[FilterDict]) -> None:
        """Set or update filters to `filter_configs`.

        Parameters
        ----------
        filter_configs : list of filters.FilterDict
            List of filter configs used to modify filters for this TrackHandler.
        """
        async with self.__lock:
            await self._set_filters(filter_configs)

    async def _set_filters(self, filter_configs: list[FilterDict]) -> None:
        """Internal version of `set_filters`, without lock.

        See `set_filters` for docs.
        """

        old_filters = self._filters

        self._filters = {}
        for config in filter_configs:
            filter_id = config["id"]
            # Reuse existing filter for matching id and name.
            if (
                filter_id in old_filters
                and old_filters[filter_id].config["name"] == config["name"]
            ):
                self._filters[filter_id] = old_filters[filter_id]
                self._filters[filter_id].set_config(config)
                continue

            # Create a new filter for configs with empty id.
            self._filters[filter_id] = filter_factory.create_filter(
                config, self.connection.incoming_audio, self.connection.incoming_video
            )

        coroutines: list[Coroutine] = []
        # Cleanup old filters
        for filter_id, old_filter in old_filters.items():
            if filter_id not in self._filters:
                coroutines.append(old_filter.cleanup())

        # Complete setup for new filters
        for new_filter in self._filters.values():
            coroutines.append(new_filter.complete_setup())

        await asyncio.gather(*coroutines)
        self.reset_execute_filters()

    def reset_execute_filters(self):
        """Reset `self._execute_filters`.

        `self._execute_filters` indicates if the filter pipeline should be executed.
        The pipeline is only executed filters exists and this TrackHandler is not muted
        or any of the filters should be executed even if muted.
        """
        self._execute_filters = len(self._filters) > 0 and (
            not self._muted or any([f.run_if_muted for f in self._filters.values()])
        )

    async def set_group_filters(
        self, group_filter_configs: list[FilterDict], ports: list[tuple[int, int]]
    ) -> None:
        async with self.__lock:
            await self._set_group_filters(group_filter_configs, ports)

    async def _set_group_filters(
        self, group_filter_configs: list[FilterDict], ports: list[tuple[int, int]]
    ) -> None:
        old_group_filters = self._group_filters

        self._group_filters = {}
        for config, port_tuple in zip(group_filter_configs, ports):
            filter_id = config["id"]
            # Reuse existing filter for matching id and type.
            if (
                filter_id in old_group_filters
                and old_group_filters[filter_id].config["name"] == config["name"]
            ):
                self._group_filters[filter_id] = old_group_filters[filter_id]
                self._group_filters[filter_id].set_config(config)
                continue

            # Create a new filter for configs with empty id.
            self._group_filters[filter_id] = group_filter_factory.create_group_filter(
                config, self.connection._log_name_suffix[2:]
            )
            self._group_filters[filter_id].connect_aggregator(*port_tuple)

        coroutines: list[Coroutine] = []
        # Cleanup old filters
        for filter_id, old_group_filter in old_group_filters.items():
            if filter_id not in self._group_filters:
                coroutines.append(old_group_filter.cleanup())

        # Complete setup for new filters
        for new_filter in self._group_filters.values():
            coroutines.append(new_filter.complete_setup())

        await asyncio.gather(*coroutines)
        self.reset_execute_group_filters()

    def reset_execute_group_filters(self):
        self._execute_group_filters = len(self._group_filters) > 0

    async def get_filters_data(self, id, name) -> list[FilterDataDict]:
        """Get data for filters."""
        async with self.__lock:
            return await self._get_filters_data(id, name)

    async def _get_filters_data(self, id, name) -> list[FilterDataDict]:
        """Internal version of `get_filters_data`, without lock."""
        filters_data: list[FilterDataDict] = []
        for filter in self._filters.values():
            if filter.name() == name:
                if id == "all":
                    filters_data.append(await filter.get_filter_data())
                elif id == filter.id:
                    filters_data.append(await filter.get_filter_data())
                    break
                else:
                    raise ErrorDictException(
                        code=404,
                        type="UNKNOWN_FILTER_ID",
                        description=f'Unknown filter ID: "{id}".',
                    )
        return filters_data

    async def recv(self) -> AudioFrame | VideoFrame:
        """Receive the next av.AudioFrame from this track and apply filter pipeline.

        Checks if this track is muted and returns silence if so.

        Returns
        -------
        av.AudioFrame or av.VideoFrame
            Next frame from the track this TrackHandler manages.  Return type depends
            on `kind` of this TrackHandler.

        Raises
        ------
        MediaStreamError
            If `self.readyState` is not "live"
        """
        if self.readyState != "live":
            raise MediaStreamError

        frame = await self.track.recv()

        if self._execute_group_filters:
            if self.kind == "video":
                frame = await self._run_video_group_filters(frame)
            else:
                frame = await self._run_audio_group_filters(frame)

        if self._execute_filters:
            if self.kind == "video":
                frame = await self._apply_video_filters(frame)
            else:
                frame = await self._apply_audio_filters(frame)

        if self._muted:
            muted_frame = await self._mute_filter.process(frame)
            return muted_frame

        return frame

    async def _apply_video_filters(self, frame: VideoFrame):
        """Parse video frame and pass it to `_apply_filters`."""
        ndarray = frame.to_ndarray(format="bgr24")
        ndarray = await self._apply_filters(frame, ndarray)

        new_frame = self.__create_video_frame_from_ndarray(ndarray, frame)
        return new_frame

    async def _apply_audio_filters(self, frame: AudioFrame):
        """Parse audio frame and pass it to `_apply_filters`."""
        ndarray = frame.to_ndarray()
        ndarray = await self._apply_filters(frame, ndarray)

        new_frame = self.__create_audio_frame_from_ndarray(ndarray, frame)
        return new_frame

    async def _apply_filters(
        self, original: VideoFrame | AudioFrame, ndarray: numpy.ndarray
    ) -> numpy.ndarray:
        """Execute filter pipeline."""
        async with self.__lock:
            # Run all filters if not self._muted.
            if not self._muted:
                for active_filter in self._filters.values():
                    ndarray = await active_filter.process(original, ndarray)
                return ndarray

            # Muted. Only execute filters where run_if_muted is True.
            for active_filter in self._filters.values():
                if active_filter.run_if_muted:
                    ndarray = await active_filter.process(original, ndarray)

        return ndarray

    def __create_video_frame_from_ndarray(self, ndarray: numpy.ndarray, frame: VideoFrame):
        new_frame = VideoFrame.from_ndarray(ndarray, format="bgr24")
        new_frame.time_base = frame.time_base
        new_frame.pts = frame.pts
        return new_frame

    def __create_audio_frame_from_ndarray(self, ndarray: numpy.ndarray, frame: AudioFrame):
        new_frame = AudioFrame.from_ndarray(ndarray)
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        new_frame.sample_rate = frame.sample_rate
        return new_frame

    async def _run_video_group_filters(self, frame: VideoFrame) -> numpy.ndarray:
        ndarray = frame.to_ndarray(format="bgr24")
        ndarray = await self._run_group_filters(frame, ndarray)

        new_frame = self.__create_video_frame_from_ndarray(ndarray, frame)
        return new_frame

    async def _run_audio_group_filters(self, frame: AudioFrame) -> numpy.ndarray:
        ndarray = frame.to_ndarray()
        ndarray = await self._run_group_filters(frame, ndarray)

        new_frame = self.__create_audio_frame_from_ndarray(ndarray, frame)
        return new_frame

    async def _run_group_filters(
        self, original: VideoFrame | AudioFrame, ndarray: numpy.ndarray
    ) -> numpy.ndarray:
        """Execute group filter individual frame processing pipeline."""
        async with self.__lock:
            frame_timestamp = time()
            for active_group_filter in self._group_filters.values():
                ndarray = (
                    await active_group_filter.process_individual_frame_and_send_data_to_aggregator(
                        original, ndarray, frame_timestamp
                    )
                )
            return ndarray
