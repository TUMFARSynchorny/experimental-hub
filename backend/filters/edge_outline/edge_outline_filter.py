"""Provide `EdgeOutlineFilter` filter."""
from typing import Optional

import cv2
import numpy
from av import VideoFrame

from filters.filter import Filter


class EdgeOutlineFilter(Filter):
    """Filter example outlining corners using Canny edge detector algorithm.

    See Also
    --------
    cv2.Canny : Canny edge detector algorithm.
    https://en.wikipedia.org/wiki/Canny_edge_detector : Canny edge detector.
    """

    @staticmethod
    def name() -> str:
        return "EDGE_OUTLINE"

    @staticmethod
    def type() -> str:
        return "SESSION"

    @staticmethod
    def channel() -> str:
        return "video"

    async def process(self, _: Optional[VideoFrame]=None, ndarray: numpy.ndarray=None,  **kwargs) -> numpy.ndarray:
        # For docstring see filters.filter.Filter or hover over function declaration
        # Example based on https://github.com/aiortc/aiortc/tree/main/examples/server
        ndarray = cv2.cvtColor(cv2.Canny(ndarray, 100, 200), cv2.COLOR_GRAY2BGR)
        return ndarray
