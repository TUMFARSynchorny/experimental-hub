"""Provide `DelayFilter` filter."""
from typing import TypeGuard

import numpy
from queue import Queue
from av import VideoFrame, AudioFrame

from custom_types import util
from filters.filter import Filter
from filters.filter import FilterDict


class DelayFilter(Filter):
    """Filter delaying the input by a set amount of frames.

    Works for audio or video input.
    """

    buffer: Queue[numpy.ndarray]

    def __init__(
        self, config: FilterDict, audio_track_handler, video_track_handler
    ) -> None:
        """Initialize new MuteVideoFilter.

        Load the muted frame image `/images/muted.png` and store it as av.VideoFrame as
        well as numpy.ndarray for quick access in `process`.

        Parameters
        ----------
        See base class: filters.filter.Filter.
        """
        super().__init__(config, audio_track_handler, video_track_handler)
        self.buffer = Queue(config["config"]["size"]["value"])

    @staticmethod
    def name(self) -> str:
        return "DELAY"

    @staticmethod
    def get_filter_json(self) -> object:
        # For docstring see filters.filter.Filter or hover over function declaration
        name = self.name(self)
        id = name.lower()
        id = id.replace("_", "-")
        return {
            "type": name,
            "id": id,
            "channel": "both",
            "groupFilter": False,
            "config": {
                "size": {
                    "min": 0,
                    "max": 120,
                    "step": 1,
                    "value": 60,
                    "defaultValue": 60,
                },
            },
        }

    async def process(
        self, _: VideoFrame | AudioFrame, ndarray: numpy.ndarray
    ) -> numpy.ndarray:
        self.buffer.put(ndarray)
        if self.buffer.full():
            return self.buffer.get()
        return self.buffer.queue[0]
