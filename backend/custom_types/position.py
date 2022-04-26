"""Provide the `PositionDict` TypedDict.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import TypedDict


class PositionDict(TypedDict):
    """3D position for a user on a canvas.

    Attributes
    ----------
    x : int
        X coordinate.
    y : int
        Y coordinate.
    z : int
        Z coordinate.

    See Also
    --------
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#Participant
    """

    x: int
    y: int
    z: int
