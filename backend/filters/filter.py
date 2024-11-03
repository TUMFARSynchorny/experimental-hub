"""Provide abstract `Filter`, `VideoFilter` and `AudioFilter` classes."""

from __future__ import annotations

import numpy
from typing import TYPE_CHECKING, TypeGuard, Optional
from abc import ABC, abstractmethod
from av import VideoFrame, AudioFrame

from custom_types import util
from .filter_dict import FilterDict
from .filter_data_dict import FilterDataDict

if TYPE_CHECKING:
    # Import TrackHandler only for type checking to avoid circular import error
    from hub.track_handler import TrackHandler


class Filter(ABC):
    """Abstract base class for all filters.

    Attributes
    ----------
    audio_track_handler
    video_track_handler
    run_if_muted
    config
    """

    audio_track_handler: TrackHandler
    """Audio hub.track_handler.TrackHandler for the stream this filter is part of.

    Use to communicate with audio filters running on the same stream.  Depending on the
    type of this filter, the filter is either managed by `audio_track_handler` or
    `video_track_handler`.
    """

    video_track_handler: TrackHandler
    """Video hub.track_handler.TrackHandler for the stream this filter is part of.

    Use to communicate with video filters running on the same stream.  Depending on the
    type of this filter, the filter is either managed by `audio_track_handler` or
    `video_track_handler`.
    """

    run_if_muted: bool
    """Whether this filter should be executed if the TrackHandler is muted.

    Call `TrackHandler.reset_execute_filters()` in case the value is changed manually
    after initialization.
    """

    _config: FilterDict

    _id: str

    def __init__(
        self,
        config: FilterDict,
        audio_track_handler: Optional[TrackHandler] = None,
        video_track_handler: Optional[TrackHandler] = None,
    ) -> None:
        """Initialize new Filter.

        Parameters
        ----------
        config : custom_types.filter.FilterDict
            Configuration for filter.  `config["name"]` must match the filter
            implementation.
        audio_track_handler : modules.track_handler.TrackHandler
            Audio TrackHandler for the stream this filter is part of.
        video_track_handler : modules.track_handler.TrackHandler
            Video TrackHandler for the stream this filter is part of.

        Notes
        -----
        If other filters need to be accessed or the initiation contains an asynchronous
        part, use `complete_setup`. The other filters may not be initialized when
        __init__ is called. However, filters must be ready to be accessed by other
        filters after __init__ (if they are designed to be).
        """
        self.run_if_muted = False
        self._config = config
        self.audio_track_handler = audio_track_handler
        self.video_track_handler = video_track_handler
        self._id = self._config["id"]
    @property
    def config(self) -> FilterDict:
        """Get Filter config."""
        return self._config

    def set_config(self, config: FilterDict) -> None:
        """Update filter config.

        Notes
        -----
        Provide a custom implementation for this function in a subclass in case the
        filter should react to config changes.
        """
        self._config = config

    @property
    def id(self) -> str:
        """Get Filter id."""
        return self._id

    def set_id(self, id: str) -> None:
        """Update filter id.

        Notes
        -----
        Provide a custom implementation for this function in a subclass in case the
        filter should react to id changes.
        """
        self._id = id

    async def complete_setup(self) -> None:
        """Complete setup, allowing for asynchronous setup and accessing other filters.

        If the initiation / setup of a filter requires anything asynchronous or other
        filters must be accessed, it should be done in `complete_setup`.
        `complete_setup` is called when all filters have been set up, therefore other
        filters will be available (may not be the case in __init__, depending on the
        position in the filter pipeline).
        """
        return

    async def cleanup(self) -> None:
        """Cleanup, in case filter will no longer be used.

        Called before the filter is deleted.  In case the filter spawned any
        asyncio.Task tasks they should be stopped & awaited in a custom implementation
        overriding this function.
        """
        return

    async def get_filter_data(self) -> None | FilterDataDict:
        """Get the data of a filter"""
        return

    @staticmethod
    @abstractmethod
    def name() -> str:
        """Provide name of the filter.

        The given name must be unique among all filters.
        The given name is used as the unique ID for communicating the active filters
        between frontend and backend.
        """
        raise NotImplementedError(
            f"{__name__} is missing it's implementation of the static abstract name()"
            " method."
        )

    @staticmethod
    @abstractmethod
    def type() -> str:
        """Provide the type of the filter.

        It can be either "TEST" or "SESSION"
        "NONE" type is used for mute filters
        This is used to build the filters_data JSON object
        """
        raise NotImplementedError(
            f"{__name__} is missing it's implementation of the static abstract name()"
            " method."
        )

    @staticmethod
    @abstractmethod
    def channel() -> str:
        """Provide the channel of the filter.

        It can be either "video", "audio" or "both"
        This is used to build the filters_data JSON object
        """
        raise NotImplementedError(
            f"{__name__} is missing it's implementation of the static abstract channel()"
            " method."
        )

    @staticmethod
    def default_config() -> dict:
        """Provide the default config for the filter.

        By default, the default config is an empty dictionary, overwrite this in the
        filter class to provide a custom config in the filters_data JSON object.
        This is used to build the filters_data JSON object
        """
        return {}

    @abstractmethod
    async def process(
        self, original: VideoFrame | AudioFrame, ndarray: numpy.ndarray
    ) -> numpy.ndarray:
        """Process audio/video frame.  Apply filter to frame.

        Parameters
        ----------
        original: av.VideoFrame or av.AudioFrame
            Original frame with metadata that can be useful to the filter.  Can be
            ignored if metadata is not of interest.
        ndarray : numpy.ndarray
            Frame as numpy.ndarray.  If the filter modifies the frame, it should modify
            and return `ndarray`.

        Returns
        -------
        numpy.ndarray
            Original or modified `ndarray`, based on input parameter.

        Notes
        -----
        If the filter does not modify the frame, it should return `ndarray`.
        If the filter modifies the frame, it should be based on `ndarray`.  Using
        `original` will ignore filters executed before this filter.
        Analysis of the frame contents should also be based on `ndarray`.
        """
        pass

    @staticmethod
    def validate_dict(data) -> TypeGuard[FilterDict]:
        return util.check_valid_typeddict_keys(data, FilterDict)

    def __repr__(self) -> str:
        """Get string representation for this filter."""
        return (
            f"{self.__class__.__name__}(run_if_muted={self.run_if_muted},"
            f" config={self.config})"
        )
