"""This module provides the Session class"""

from __future__ import annotations
from typing import Callable, Optional, Any
import json
from copy import deepcopy

from modules.util import generate_unique_id

from custom_types.session import SessionDict
from custom_types.participant import ParticipantDict
from custom_types.note import NoteDict


class Session:
    """Session data with update handling.

    Will forward any updates to the sessionmanager, making sure all changes are
    persistent.

    Attributes
    ----------
    asdict
    id
    title
    description
    date
    time_limit
    record
    participants
    start_time
    end_time
    notes
    log
    """

    _data: SessionDict
    _on_update: Callable[[Session], None]

    def __init__(self, session: SessionDict, on_update: Callable[[Session], None]):
        """Initialize new Session.

        Parameters
        ----------
        session : custom_types.session.SessionDict
            Session data the session represents.
        on_update : function (Session) -> None
            Function that informs the session manager if changes occurred.
        """
        self._data = session
        self._on_update = on_update

    def update(self, session: SessionDict | Session):
        """Update the whole Session.

        Parameters
        ----------
        session : custom_types.session.SessionDict or Session
            Updated data, either a Session or custom_types.session.SessionDict.

        Raises
        ------
        ValueError
            If `session` is of invalid type or has a different session_id than this
            Session.
        """
        if isinstance(session, Session):
            new_data = session.asdict
        elif isinstance(session, dict):  # check for SessionDict
            new_data = session
        else:
            raise ValueError(
                "Incorrect type for session argument. Expected: SessionDict or Session,"
                f"got: {type(session)}"
            )

        if new_data.get("id") is not self.id:
            raise ValueError("Session.update can not change the ID of a Session")

        self._data = new_data
        self._on_update(self)

    def __str__(self) -> str:
        """Get indented json string for this Session"""
        return json.dumps(self.asdict, indent=4)

    def __repr__(self) -> str:
        """Get representation of this Session obj.  Format: `Session(<id>)`."""
        return f"Session({self.id})"

    @property
    def asdict(self) -> SessionDict:
        """Get session as SessionDict dictionary.

        Returns
        -------
        custom_types.session.SessionDict
            Session dictionary containing a copy of the data for this Session.
        """
        return deepcopy(self._data)

    @property
    def id(self) -> str | None:
        """Get Session ID, or None if it does not exist."""
        return self._data.get("id")

    @property
    def title(self) -> str:
        """Get Session title."""
        return self._data.get("title")

    @title.setter
    def title(self, value: str):
        """Update session title."""
        self._data["title"] = value
        self._on_update(self)

    @property
    def description(self) -> str:
        """Get Session description."""
        return self._data.get("description")

    @description.setter
    def description(self, value: str):
        """Update Session description"""
        self._data["description"] = value
        self._on_update(self)

    @property
    def date(self) -> int:
        """Get Session date in milliseconds since January 1, 1970, 00:00:00 (UTC)."""
        return self._data.get("date")

    @date.setter
    def date(self, value: int):
        """Update Session date in milliseconds since January 1, 1970, 00:00:00 (UTC)."""
        self._data["date"] = value
        self._on_update(self)

    @property
    def time_limit(self) -> int:
        """Get Session time limit in milliseconds."""
        return self._data.get("time_limit")

    @time_limit.setter
    def time_limit(self, value: int):
        """Update Session time limit in milliseconds."""
        self._data["time_limit"] = value
        self._on_update(self)

    @property
    def record(self) -> bool:
        """Get Session record parameter."""
        return self._data.get("record")

    @record.setter
    def record(self, value: bool):
        """Update Session record parameter."""
        self._data["record"] = value
        self._on_update(self)

    @property
    def participants(self) -> list[ParticipantDict]:
        """Get Session participants list."""
        return self._data.get("participants")

    def add_participant(self, participant: ParticipantDict):
        """Add a participant to the Session.

        Generates an unique id for the participant and adds it to the participants list.

        Parameters
        ----------
        participant : custom_types.participant.ParticipantDict
            Participant that should be added to the Session.  Must be a valid
            custom_types.participant.ParticipantDict (no checks) and not contain any id.
        """
        participant_ids = [p.get("id", "") for p in self._data.get("participants")]
        id = generate_unique_id(participant_ids)
        participant["id"] = id
        self._data["participants"].append(participant)
        self._on_update(self)

    def remove_participant(self, participant_id: str):
        """Remove a participant from the Session.

        If the participant is found, it will be removed. Otherwise nothing happens.

        Parameters
        ----------
        participant_id : str
            ID of the participant that should be removed.
        """
        participant_ids = [p.get("id", "") for p in self._data.get("participants")]

        try:
            index = participant_ids.index(participant_id)
        except ValueError:
            print(
                f"[SESSION]: participant with id {participant_id} was not found in",
                "participants",
            )
            return

        self._data["participants"].pop(index)

    @property
    def start_time(self) -> Optional[int]:
        """Get Session start time in milliseconds since January 1, 1970, 00:00:00 (UTC)."""
        return self._data.get("start_time")

    @start_time.setter
    def start_time(self, value: int):
        """Update Session start time in milliseconds since January 1, 1970, 00:00:00
        (UTC).
        """
        self._data["start_time"] = value
        self._on_update(self)

    @property
    def end_time(self) -> Optional[int]:
        """Get Session end time in milliseconds since January 1, 1970, 00:00:00 (UTC)."""
        return self._data.get("end_time")

    @end_time.setter
    def end_time(self, value: int):
        """Update Session end time in milliseconds since January 1, 1970, 00:00:00 (UTC)
        .
        """
        self._data["end_time"] = value
        self._on_update(self)

    @property
    def notes(self) -> list[NoteDict]:
        """Get Session Notes list."""
        return self._data.get("notes")

    def add_note(self, note: NoteDict):
        """Add a Note to the Session."""
        self._data["notes"].append(note)
        self._on_update(self)

    @property
    def log(self) -> Optional[Any]:
        """TODO Document - log still wip"""
        return self._data.get("log")
