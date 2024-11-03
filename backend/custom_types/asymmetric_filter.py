"""Provide the `AsymmetricFilterDict` TypedDict`.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import Any, TypeGuard, TypedDict

import custom_types.util as util

from filters import FilterDict
from filters import filter_utils


class AsymmetricFilterDict(TypedDict):
    """TypedDict for sending canvas element between client and server.

    Attributes
    ----------
    id : str
        id of the participant
    participant_name: str
        name of the participant
    audio_filters : list of filters.FilterDict
        Active audio filters for a participant.
    video_filters : list of filters.FilterDict
        Active video filters for a participant.

    """

    id: str
    participant_name: str
    audio_filters: list[FilterDict]
    video_filters: list[FilterDict]


def is_valid_asymmetric_filter(data: Any) -> TypeGuard[AsymmetricFilterDict]:
    """Check if `data` is a valid AsymmetricFilterDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.

    Returns
    -------
    bool
        True if `data` is a valid AsymmetricFilterDict.
    """

    if not util.check_valid_typeddict_keys(data, AsymmetricFilterDict):
        return False

    if not isinstance(data["audio_filters"], list) or not isinstance(data["video_filters"], list):
        return False

    for filter in data["audio_filters"]:
        if not filter_utils.is_valid_filter_dict(filter):
            return False

    for filter in data["video_filters"]:
        if not filter_utils.is_valid_filter_dict(filter):
            return False

    return isinstance(data["id"], str) and isinstance(data["participant_name"], str)
