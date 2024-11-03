"""Provide the `ParticipantDict` TypedDict.

Use for type hints and static type checking without any overhead during runtime.
"""
from typing import TypedDict

from custom_types.chat_message import ChatMessageDict
from custom_types.canvas_element import CanvasElementDict
from custom_types.asymmetric_filter import AsymmetricFilterDict
from filters import FilterDict
from chat_filters import ChatFilterDict
from session.data.position import PositionDict
from session.data.size import SizeDict


class ParticipantDict(TypedDict):
    """TypedDict representing a participant.

    Contains sensitive information that should not be sent to non-experimenter clients.

    Attributes
    ----------
    id: str, default ""
        Unique id for this participant in a Session.  When creating a new Participant in
        a Session, this field is initially set to an empty string.
    participant_name : str
        Name of the participant.
    muted_video : bool
        Whether the participants' video is forcefully muted by the experimenter.
    muted_audio : bool
        Whether the participants' audio is forcefully muted by the experimenter.
    local_stream : bool
        Whether the participants' view is using a local stream.
    audio_filters : list of filters.FilterDict
        Active audio filters for this participant.
    video_filters : list of filters.FilterDict
        Active video filters for this participant.
    chat_filters: list of chat_filters.ChatFilterDict
        Active chat filters for this participant.
    audio_group_filters : list of filters.FilterDict
        Active audio group filters for this participant.
    video_group_filters : list of filters.FilterDict
        Active video group filters for this participant.
    position : custom_types.position.PositionDict
        Position of the participant's stream on the canvas.
    size : custom_types.size_types.SizeDict
        Size of the participant's stream on the canvas.
    chat : list of custom_types.chat_log.ChatLogDict
        Chat log between experimenter and participant.
    banned : bool
        Whether this participant is banned from the experiment.
    lastMessageSentTime: int
        Last message sent time.
    lastMessageReadTime: int
        Last message read time by experimenter.
    view : list of custom_types.canvas_element.CanvasElementDict
        Asymmetric view of the participant
    canvas_id: str
        Unique id for the placement of the participant stream
    asymmetric_filters : list of custom_types.asymmetric_filter.AsymmetricFilterDict
        Active asymmetric filters for this participant.
        asymmetric_filters_id : str
        Unique id for the asymmetric filters

    See Also
    --------
    ParticipantSummaryDict :
        custom_types.participant_summary.ParticipantSummaryDict used to send a summary
        of a participant to the client.
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#Participant
    """

    id: str
    participant_name: str
    muted_video: bool
    muted_audio: bool
    local_stream: bool
    audio_filters: list[FilterDict]
    video_filters: list[FilterDict]
    chat_filters: list[ChatFilterDict]
    audio_group_filters: list[FilterDict]
    video_group_filters: list[FilterDict]
    position: PositionDict
    size: SizeDict
    chat: list[ChatMessageDict]
    banned: bool
    lastMessageSentTime: int
    lastMessageReadTime: int
    view: list[CanvasElementDict]
    canvas_id: str
    asymmetric_filters: list[AsymmetricFilterDict]
    asymmetric_filters_id: str
