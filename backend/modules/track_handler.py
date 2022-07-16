"""Provide TrackHandler for handing and distributing tracks."""

from __future__ import annotations
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

from modules.exceptions import ErrorDictException

from custom_types.filters import FilterDict
from filters.rotate import RotationFilter
from filters.edge_outline import EdgeOutlineFilter
from filters.filter import Filter
from filters.mute import MuteVideoFilter, MuteAudioFilter
from filters.api_test import FilterAPITestFilter

if TYPE_CHECKING:
    from modules.connection import Connection
    from modules.filter_api_interface import FilterAPIInterface


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
    _execute_filters: bool
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

        TODO update docs

        Parameters
        ----------
        kind : str, "audio" or "video"
            Kind of MediaStreamTrack this handler handles.
        track : aiortc.mediastreams.MediaStreamTrack
            Track this handler should manage and distribute.  None if track is set
            later.
        muted : bool, default False
            Whether this track should be muted.

        Raises
        ------
        ValueError
            If kind is not "audio" or "video".
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

        # Forward the ended event to this handler.
        self._track.add_listener("ended", self.stop)

    async def complete_setup(self, filters: list[FilterDict]):
        """TODO document"""
        if self.kind == "audio":
            self._mute_filter = MuteAudioFilter(
                "0",
                {"id": "0", "type": "MUTE_AUDIO"},
                self.connection.incoming_audio,
                self.connection.incoming_video,
            )
        else:
            self._mute_filter = MuteVideoFilter(
                "0",
                {"id": "0", "type": "MUTE_VIDEO"},
                self.connection.incoming_audio,
                self.connection.incoming_video,
            )
        await self.set_filters(filters)

    @property
    def track(self) -> MediaStreamTrack:
        """Get source track for this TrackHandler.

        Notes
        -----
        Use `subscribe` to add a subscriber to this track.
        """
        return self._track

    @property
    def muted(self) -> bool:
        """TODO document"""
        return self._muted

    @muted.setter
    def muted(self, value: bool) -> None:
        """TODO document"""
        self._muted = value
        self.reset_execute_filters()

    async def stop(self) -> None:
        """TODO document"""
        super().stop()
        coros = [f.cleanup() for f in self._filters.values()]
        await asyncio.gather(*coros)

    async def set_track(self, value: MediaStreamTrack):
        """Set source track for this TrackHandler.

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
        """TODO document"""
        async with self.__lock:
            await self._set_filters(filter_configs)

    async def _set_filters(self, filter_configs: list[FilterDict]) -> None:
        """TODO document"""

        new_filters: dict[str, Filter] = {}
        for config in filter_configs:
            id = config["id"]
            # Reuse existing filter for matching id and type.
            if (
                id in self._filters
                and self._filters[id].config["type"] == config["type"]
            ):
                new_filters[id] = self._filters[id]
                new_filters[id].set_config(config)
                continue

            # Create a new filter for configs with empty id.
            new_filters[id] = self._create_filter(id, config)

        coros: list[Coroutine] = []
        for id, filter in self._filters.items():
            if id not in new_filters:
                coros.append(filter.cleanup())
        await asyncio.gather(*coros)

        self._filters = new_filters
        self.reset_execute_filters()

    def _create_filter(self, id: str, filter_config: FilterDict) -> Filter:
        """TODO document"""
        type = filter_config["type"]
        audio = self.connection.incoming_audio
        video = self.connection.incoming_video

        match type:
            case "ROTATION":
                return RotationFilter(id, filter_config, audio, video)
            case "EDGE_OUTLINE":
                return EdgeOutlineFilter(id, filter_config, audio, video)
            case "FILTER_API_TEST":
                return FilterAPITestFilter(id, filter_config, audio, video)
            case _:
                raise ErrorDictException(
                    code=404,
                    type="UNKNOWN_FILTER_TYPE",
                    description=f'Unknown filter type "{type}".',
                )

    def reset_execute_filters(self):
        """TODO document"""
        self._execute_filters = len(self._filters) > 0 and (
            not self._muted or any([f.run_if_muted for f in self._filters.values()])
        )

    async def recv(self) -> AudioFrame | VideoFrame:
        """Receive the next av.AudioFrame from this track.

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
        """TODO document"""
        ndarray = frame.to_ndarray(format="bgr24")
        ndarray = await self._apply_filters(frame, ndarray)

        new_frame = VideoFrame.from_ndarray(ndarray, format="bgr24")
        new_frame.time_base = frame.time_base
        new_frame.pts = frame.pts
        return new_frame

    async def _apply_audio_filters(self, frame: AudioFrame):
        """TODO document"""
        ndarray = frame.to_ndarray()
        ndarray = await self._apply_filters(frame, ndarray)

        new_frame = AudioFrame.from_ndarray(ndarray)
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        new_frame.sample_rate = frame.sample_rate
        return new_frame

    async def _apply_filters(
        self, original: VideoFrame | AudioFrame, ndarray: numpy.ndarray
    ) -> numpy.ndarray:
        """TODO document"""
        async with self.__lock:
            # Run all filters if not self._muted.
            if not self._muted:
                for filter in self._filters.values():
                    ndarray = await filter.process(original, ndarray)
                return ndarray

            # Muted. Only execute filters where run_if_muted is True.
            for filter in self._filters.values():
                if filter.run_if_muted:
                    ndarray = await filter.process(original, ndarray)

        return ndarray
