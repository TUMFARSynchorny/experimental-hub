"""Provide the `ParticipantSummaryDict` TypedDict.

Use for type hints and static type checking without any overhead during runtime.
"""

from typing import TypedDict

from session.data.size import SizeDict
from session.data.position import PositionDict
from custom_types.chat_message import ChatMessageDict
from custom_types.canvas_element import CanvasElementDict


class ParticipantSummaryDict(TypedDict):
    """TypedDict for api messages.  All messages send should be a MessageDict.

    The `ParticipantSummaryDict` is used to send non-sensitive information about an
    participant to the client.  In comparison to
    custom_types.participant.ParticipantDict, `ParticipantSummaryDict` contains only the
    information the client requires and no sensitive information, e.g. the participant
    id.

    Attributes
    ----------
    participant_name : str
        Name of the participant.
    position : custom_types.position.PositionDict
        Position of the participant's stream on the canvas.
    size : custom_types.size_types.SizeDict
        Size of the participant's stream on the canvas.
    chat : list of custom_types.chat_log.ChatLogDict
        Chat log between experimenter and participant.
    view : list of custom_types.canvas_element.CanvasElementDict
        Asymmetric view of the participant
    canvas_id : str
        Unique id for the placement of the participant stream

    See Also
    --------
    ParticipantDict :
        custom_types.participant.ParticipantDict
    Data Types Wiki :
        https://github.com/TUMFARSynchorny/experimental-hub/wiki/Data-Types#participantsummary
    """

    id: str
    participant_name: str
    position: PositionDict
    size: SizeDict
    chat: list[ChatMessageDict]
    view: list[CanvasElementDict]
    canvas_id: str
    asymmetric_filters_id: str

