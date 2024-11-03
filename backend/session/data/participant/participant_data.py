from __future__ import annotations

from typing import TYPE_CHECKING

from chat_filters import ChatFilterDict

if TYPE_CHECKING:
    from session.data.participant import ParticipantDict, ParticipantSummaryDict

from dataclasses import dataclass, field

from custom_types.chat_message import ChatMessageDict
from custom_types.canvas_element import CanvasElementDict
from custom_types.asymmetric_filter import AsymmetricFilterDict
from filters import FilterDict
from session.data.base_data import BaseData

from session.data.position.position_data import PositionData
from session.data.size.size_data import SizeData


@dataclass(slots=True)
class ParticipantData(BaseData):
    """participant data with update handling.

    Will forward any updates to the parent SessionData, making sure all changes are
    persistent.

    Attributes
    ----------
    id : str
    participant_name : str
    banned : bool
    size : SizeData
    muted_video : bool
    muted_audio : bool
    local_stream : bool
    position : PositionData
    chat : list or custom_types.chat_message.ChatMessageDict
    filters : list or filters.FilterDict
    view : list or custom_types.chat_message.CanvasElementDict
    canvas_id : str
    asymmetric_filters : list or custom_types.asymmetric_filter.AsymmetricFilterDict
    asymmetric_filters_id : str

    Methods
    -------
    asdict()
        Get ParticipantData as dictionary.

    See Also
    --------
    participant_data_factory : create ParticipantData based on a ParticipantDict.

    Note
    ----
    Special methods, such as __str__, __repr__ and equality checks are generated
    automatically by dataclasses.dataclass.
    """

    id: str
    """Participant ID."""

    participant_name: str
    """Name of this participant."""

    banned: bool = field(repr=False)
    """Whether this participant is banned."""

    size: SizeData = field(repr=False)
    """Size of participant on the canvas (frontend).

    Notes
    -----
    Replacing the size may break event listeners / emitters.  In case such functionality
    is required in the future, the following must be ensured: when size is replaced,
    this ParticipantData must listen and forward all SizeData "update" events.  Event
    listeners from the previous SizeData should also be removed.
    """

    muted_video: bool = field(repr=False)
    """Whether the participants' video is forcefully muted by the experimenter."""

    muted_audio: bool = field(repr=False)
    """Whether the participants' audio is forcefully muted by the experimenter."""

    local_stream: bool = field(repr=False)
    """Whether the participants' view is using a local stream."""

    position: PositionData = field(repr=False)
    """Position of the participant on the canvas (frontend).

    Notes
    -----
    Replacing the position may break event listeners / emitters.  In case such
    functionality is required in the future, the following must be ensured: when
    position is replaced, this ParticipantData must listen and forward all PositionData
    "update" events.  Event listeners from the previous PositionData should also be
    removed.
    """

    chat: list[ChatMessageDict] = field(repr=False)
    """Chat log between participant and experimenter."""

    audio_filters: list[FilterDict] = field(repr=False)
    """Active audio filters for participant."""

    video_filters: list[FilterDict] = field(repr=False)
    """Active video filters for participant."""

    chat_filters: list[ChatFilterDict] = field(repr=False)
    """Active chat filters for participant"""

    audio_group_filters: list[FilterDict] = field(repr=False)
    """Active audio group filters for participant."""

    video_group_filters: list[FilterDict] = field(repr=False)
    """Active video group filters for participant."""

    lastMessageSentTime: int = field(repr=False)
    """Last message sent time"""

    lastMessageReadTime: int = field(repr=False)
    """Last message read time"""

    view: list[CanvasElementDict] = field(repr=False)
    """Asymmetric view of the participant."""

    canvas_id: str = field(repr=False)
    """Unique id for the placement of the participant stream"""

    asymmetric_filters: list[AsymmetricFilterDict] = field(repr=False)
    """Active asymmetric filters for participant."""

    asymmetric_filters_id: str = field(repr=False)
    """Unique id for the asymmetric filters"""

    def __post_init__(self) -> None:
        """Add event listener to size and position."""
        super(ParticipantData, self).__post_init__()
        self.size.add_listener("update", self._emit_update_event)
        self.position.add_listener("update", self._emit_update_event)

    def asdict(self) -> ParticipantDict:
        """Get ParticipantData as dictionary.

        Returns
        -------
        custom_types.participant.ParticipantDict
            ParticipantDict with the data in this ParticipantData.
        """
        return {
            "id": self.id,
            "participant_name": self.participant_name,
            "banned": self.banned,
            "size": self.size.asdict(),
            "muted_video": self.muted_video,
            "muted_audio": self.muted_audio,
            "local_stream": self.local_stream,
            "position": self.position.asdict(),
            "chat": self.chat,
            "audio_filters": self.audio_filters,
            "video_filters": self.video_filters,
            "chat_filters": self.chat_filters,
            "audio_group_filters": self.audio_group_filters,
            "video_group_filters": self.video_group_filters,
            "lastMessageSentTime": self.lastMessageSentTime,
            "lastMessageReadTime": self.lastMessageReadTime,
            "view": self.view,
            "canvas_id": self.canvas_id,
            "asymmetric_filters": self.asymmetric_filters,
            "asymmetric_filters_id": self.asymmetric_filters_id,
        }

    def as_summary_dict(self) -> ParticipantSummaryDict:
        """Get non-sensitive key information from ParticipantData as dictionary.

        Returns
        -------
        custom_types.participant_summary.ParticipantSummaryDict
            ParticipantSummaryDict with some of the data in this ParticipantData.
        """
        return {
            "id": self.id,
            "participant_name": self.participant_name,
            "size": self.size.asdict(),
            "position": self.position.asdict(),
            "chat": self.chat,
            "view": self.view,
            "canvas_id": self.canvas_id,
            "asymmetric_filters_id": self.asymmetric_filters_id,
        }
