"""Provide `RotationFilter` filter."""
from typing import Optional

import cv2
import numpy
from av import VideoFrame

from filters.filter import Filter
from filters import FilterDict


class RotationFilter(Filter):
    """Filter example rotating a video track."""

    rotation: int

    def __init__(
            self, config: FilterDict, audio_track_handler: Optional[any] = None,
            video_track_handler: Optional[any] = None, participant_id = None
    ) -> None:
        super().__init__(config, audio_track_handler, video_track_handler)
        direction = 1
        if config["config"]["direction"]["value"] == "clockwise":
            direction = -1
        angle = config["config"]["angle"]["value"]
        self.rotation = angle * direction

    @staticmethod
    def name() -> str:
        return "ROTATION"

    @staticmethod
    def type() -> str:
        return "SESSION"

    @staticmethod
    def channel() -> str:
        return "video"

    @staticmethod
    def default_config() -> dict:
        return {
            "direction": {
                "defaultValue": ["clockwise", "anti-clockwise"],
                "value": "clockwise",
                "requiresOtherFilter": False,
            },
            "angle": {
                "min": 1,
                "max": 180,
                "step": 1,
                "value": 45,
                "defaultValue": 45,
            },
        }

    async def process(self, original: Optional[VideoFrame] = None, ndarray: numpy.ndarray = None,
                      **kwargs) -> numpy.ndarray:
        """Unified rotation processing method that can use either video time or frame index to determine the angle.

        Args:
            original (VideoFrame, optional): The original video frame.
            ndarray (numpy.ndarray): The ndarray representing the video frame to be rotated.
            **kwargs: Arbitrary keyword arguments. Can include 'frame_index'.

        Returns:
            numpy.ndarray: The rotated frame as a numpy array.
        """
        if original:
            angle = original.time * self.rotation
        elif 'frame_index' in kwargs:
            frame_index = kwargs.get('frame_index', 0)
            angle = frame_index * 1
        else:
            raise ValueError("No valid time or frame index provided for rotation calculation.")

        rows, cols, _ = ndarray.shape
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle % 360, 1)
        return cv2.warpAffine(ndarray, M, (cols, rows))
