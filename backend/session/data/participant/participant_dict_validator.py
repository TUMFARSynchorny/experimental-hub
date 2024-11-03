from typing import TypeGuard

from custom_types import util
from custom_types.chat_message import is_valid_chatmessage
from custom_types.canvas_element import is_valid_canvas_element
from custom_types.asymmetric_filter import is_valid_asymmetric_filter
from filters import filter_utils
from group_filters import group_filter_utils
from session.data.participant.participant_dict import ParticipantDict
from session.data.position import is_valid_position
from session.data.size import is_valid_size


def is_valid_participant(data, recursive: bool = True) -> TypeGuard[ParticipantDict]:
    """Check if `data` is a valid ParticipantDict.

    Checks if all required and no unknown keys exist in data as well as the data types
    of the values.

    Parameters
    ----------
    data : any
        Data to perform check on.
    recursive : bool, default True
        If true, filters, chat, position and size will be checked recursively.

    Returns
    -------
    bool
        True if `data` is a valid ParticipantDict.
    """
    if not util.check_valid_typeddict_keys(data, ParticipantDict):
        return False

    # Shallow checks for variables with recursive types
    if (
        not isinstance(data["audio_filters"], list)
        or not isinstance(data["video_filters"], list)
        or not isinstance(data["chat_filters"], list)
        or not isinstance(data["audio_group_filters"], list)
        or not isinstance(data["video_group_filters"], list)
        or not isinstance(data["chat"], list)
        or not isinstance(data["position"], dict)
        or not isinstance(data["size"], dict)
        or not isinstance(data["view"], list)
        or not isinstance(data["asymmetric_filters"], list)
    ):
        return False

    if recursive:
        for filter in data["audio_filters"]:
            if not filter_utils.is_valid_filter_dict(filter):
                return False
        for filter in data["video_filters"]:
            if not filter_utils.is_valid_filter_dict(filter):
                return False
        for filter in data["audio_group_filters"]:
            if not group_filter_utils.is_valid_filter_dict(filter):
                return False
        for filter in data["video_group_filters"]:
            if not group_filter_utils.is_valid_filter_dict(filter):
                return False
        for message in data["chat"]:
            if not is_valid_chatmessage(message):
                return False
        for canvas_element in data["view"]:
            if not is_valid_canvas_element(canvas_element):
                return False
        for asymmetric_filter in data["asymmetric_filters"]:
            if not is_valid_asymmetric_filter(asymmetric_filter):
                return False
        if not is_valid_size(data["size"]) or not is_valid_position(data["position"]):
            return False

    return (
        isinstance(data["id"], str)
        and isinstance(data["participant_name"], str)
        and isinstance(data["muted_video"], bool)
        and isinstance(data["lastMessageSentTime"], int)
        and isinstance(data["lastMessageReadTime"], int)
        and isinstance(data["chat_filters"], list)
        and isinstance(data["muted_audio"], bool)
        and isinstance(data["local_stream"], bool)
        and isinstance(data["banned"], bool)
        and isinstance(data["canvas_id"], str)
        and isinstance(data["asymmetric_filters_id"], str)
    )
