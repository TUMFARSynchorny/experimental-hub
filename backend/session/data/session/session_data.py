from dataclasses import dataclass, field
from typing import Any

from custom_types.note import NoteDict
from hub.exceptions import ErrorDictException
from session.data.base_data import BaseData
from session.data.participant import ParticipantData, participant_data_factory
from session.data.session.session_dict import SessionDict
from session.data.session.session_data_functions import (
    _generate_participant_ids,
    get_filtered_participant_ids,
    has_duplicate_participant_ids,
)


@dataclass(slots=True)
class SessionData(BaseData):
    """Session data with update handling.

    Will forward any updates to the SessionManager, making sure all changes are
    persistent.

    Attributes
    ----------
    id : str
    title : str
    date : int
    record : bool
    time_limit : int
    description : str
    notes : list of custom_types.note.NoteDict
    participants : dict
    log : Any or None
    creation_time : int or None
    end_time : int or None
    start_time : int or None

    Methods
    -------
    update(session_dict)
        Update the whole Session with the data in `session_dict`.
    asdict()
        Get SessionData as dictionary.

    See Also
    --------
    session_data_factory : create SessionData based on a SessionDict.

    Note
    ----
    Special methods, such as __str__, __repr__ and equality checks are generated
    automatically by dataclasses.dataclass.
    """

    id: str
    """Session ID."""

    title: str
    """Session title"""

    date: int = field(repr=False)
    """Planned session date in milliseconds since January 1, 1970, 00:00:00 (UTC)."""

    record: bool = field(repr=False)
    """Whether the session will be recorded."""

    time_limit: int = field(repr=False)
    """Session time limit in milliseconds."""

    description: str = field(repr=False)
    """Session description"""

    notes: list[NoteDict] = field(repr=False)
    """Notes taken by a Experimenter during the experiment."""

    participants: dict[str, ParticipantData] = field(repr=False)
    """Participants invited to this session.

    Notes
    -----
    Note that this is a dict, while the participants in custom_types.session.SessionDict
    are a list.

    Replacing or modifying this dict may break event listeners / emitters.  In case such
    functionality is required in the future, the following must be ensured: when
    participants changes, this SessionData must listen and forward all ParticipantData
    "update" events.  When a participant is removed, event listeners must be removed as
    well.
    """

    # Variables with default values:
    log: Any = field(repr=False, default_factory=list)
    """TODO Document - log still wip"""

    creation_time: int = field(repr=False, default=0)
    """Time an experiment for this session was created.

    0 indicates that no experiment for this session is running.  Time is given in
    milliseconds since January 1, 1970, 00:00:00 (UTC).
    """

    end_time: int = field(repr=False, default=0)
    """Session end time in milliseconds since January 1, 1970, 00:00:00 (UTC)."""

    start_time: int = field(repr=False, default=0)
    """Session start time in milliseconds since January 1, 1970, 00:00:00 (UTC)."""

    def __post_init__(self):
        """Add event listener to participants."""
        super(SessionData, self).__post_init__()
        for participant in self.participants.values():
            participant.add_listener("update", self._emit_update_event)

    def update(self, session_dict: SessionDict):
        """Update the whole Session with the data in `session_dict`.

        Parameters
        ----------
        session_dict : session.data.session.SessionDict
            New data that will be parsed into this SessionData.

        Raises
        ------
        ValueError
            If `session_dict` is of invalid type, has a different or missing (session)
            id than this SessionData.
        ErrorDictException
            If a participant with an ID unknown to the server exists in `session`.
            IDs must be generated by the backend.  In case this error occurs, the client
            tried to generate an ID.
            Also occurs if a duplicate participant ID was found.
        """
        # Data checks.
        if session_dict["id"] != self.id:
            raise ValueError("Session.update can not change the ID of a Session")

        if self._has_unknown_participant_ids(session_dict):
            raise ErrorDictException(
                code=409,
                type="UNKNOWN_ID",
                description="Unknown participant ID found in session data.",
            )

        if has_duplicate_participant_ids(session_dict):
            raise ErrorDictException(
                code=400,
                type="DUPLICATE_ID",
                description="Duplicate participant ID found in session data.",
            )

        self._set_variables(session_dict)
        self._emit_update_event()

    def asdict(self) -> SessionDict:
        """Get SessionData as dictionary.

        Returns
        -------
        session.data.session.SessionDict
            SessionDict with the data in this SessionData.
        """
        session_dict: SessionDict = {
            "id": self.id,
            "title": self.title,
            "date": self.date,
            "record": self.record,
            "time_limit": self.time_limit,
            "description": self.description,
            "creation_time": self.creation_time,
            "end_time": self.end_time,
            "start_time": self.start_time,
            "notes": self.notes,
            "participants": [p.asdict() for p in self.participants.values()],
            "log": self.log,
        }

        return session_dict

    def _set_variables(
        self, session_dict: SessionDict, final_emit_updates_value: bool = True
    ) -> None:
        """Set the variables of this data to the contents of `session_dict`.

        Parameters
        ----------
        session_dict : session.data.session.SessionDict
            Session dictionary containing the data that should be set / parsed into this
            SessionData.
        final_emit_updates_value : bool, default True
            Value `self._emit_updates` should have after this function.

        Raises
        ------
        ValueError
            If `id` in `session_dict` is an empty string.

        See Also
        --------
        _handle_updates() :
            Handle updates in data. See for information about `self._trigger_updates`.
        """
        if session_dict["id"] == "":
            raise ValueError('Missing "id" in session dict.')

        self._emit_updates = False

        # Save simple variables
        self.id = session_dict["id"]
        self.title = session_dict["title"]
        self.date = session_dict["date"]
        self.record = session_dict["record"]
        self.time_limit = session_dict["time_limit"]
        self.description = session_dict["description"]
        self.notes = session_dict["notes"]
        self.log = session_dict["log"]
        self.creation_time = session_dict["creation_time"]
        self.end_time = session_dict["end_time"]
        self.start_time = session_dict["start_time"]

        # Remove event listeners from current participants (before deleting them)
        for old_participant in self.participants.values():
            old_participant.remove_all_listeners()

        # Parse participants
        _generate_participant_ids(session_dict)
        self.participants = {}
        for participant_dict in session_dict["participants"]:
            p = participant_data_factory(participant_dict)
            p.add_listener("update", self._emit_update_event)
            self.participants[p.id] = p

        self._emit_updates = final_emit_updates_value

    def _has_unknown_participant_ids(self, session_dict: SessionDict) -> bool:
        """Check if `session_dict` has participant IDs not known to this Session.

        Parameters
        ----------
        session_dict : session.data.session.SessionDict
            Session dictionary that should be checked for unknown, and therefore
            invalid, participant IDs.  Ignores missing IDs.

        Returns
        -------
        bool
            True if there are unknown IDs, False if no unknown IDs where found.
        """
        participant_ids = get_filtered_participant_ids(session_dict)
        known_ids = self.participants.keys()

        for id in participant_ids:
            if id != "" and id not in known_ids:
                return True

        return False
