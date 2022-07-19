"""Provide abstract `Filter`, `VideoFilter` and `AudioFilter` classes."""


from __future__ import annotations

import numpy
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from av import VideoFrame, AudioFrame

from custom_types.filters import FilterDict

if TYPE_CHECKING:
    from modules.track_handler import TrackHandler


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
    """Audio modules.track_handler.TrackHandler for the stream this filter is part of.

    Use to communicate with audio filters running on the same stream.  Depending on the
    type of this filter, the filter is either managed by `audio_track_handler` or
    `video_track_handler`.
    """

    video_track_handler: TrackHandler
    """Video modules.track_handler.TrackHandler for the stream this filter is part of.

    Use to communicate with video filters running on the same stream.  Depending on the
    type of this filter, the filter is either managed by `video_track_handler` or
    `video_track_handler`.
    """

    run_if_muted: bool
    """Whether this filter should be executed if the TrackHandler is muted.

    Call `TrackHandler.reset_execute_filters()` in case the value is changed manually
    after initialization.
    """

    _config: FilterDict

    def __init__(
        self,
        config: FilterDict,
        audio_track_handler: TrackHandler,
        video_track_handler: TrackHandler,
    ) -> None:
        """Initialize new Filter.

        Parameters
        ----------
        config : custom_types.filter.FilterDict
            Configuration for filter.  `config["type"]` must match the filter
            implementation.
        audio_track_handler : modules.track_handler.TrackHandler
            Audio TrackHandler for the stream this filter is part of.
        video_track_handler : modules.track_handler.TrackHandler
            Video TrackHandler for the stream this filter is part of.
        """
        self.run_if_muted = False
        self._config = config
        self.audio_track_handler = audio_track_handler
        self.video_track_handler = video_track_handler

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

    async def cleanup(self) -> None:
        """Cleanup, in case filter will no longer be used.

        Called before the filter is deleted.  In case the filter spawned any
        asyncio.Task tasks they should be stopped & awaited in a custom implementation
        overriding this function.
        """
        return

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

    def __repr__(self) -> str:
        """Get string representation for this filter."""
        return f"{self.__class__.__name__}(run_if_muted={self.run_if_muted}, config={self.config})"
