"""Provide the `Experimenter` class and `experimenter_factory` factory function.

Notes
-----
Use experimenter_factory for creating new Experimenters to ensure that they have a valid
modules.connection.Connection.
"""

from __future__ import annotations
from typing import Any
from aiortc import RTCSessionDescription

from custom_types.error import ErrorDict
from custom_types.filters import SetFiltersRequestDict, is_valid_set_filters_request
from custom_types.session import SessionDict, is_valid_session
from custom_types.chat_message import ChatMessageDict, is_valid_chatmessage
from custom_types.kick import KickRequestDict, is_valid_kickrequest
from custom_types.message import MessageDict
from custom_types.success import SuccessDict
from custom_types.note import NoteDict, is_valid_note
from custom_types.mute import MuteRequestDict, is_valid_mute_request
from custom_types.session_id_request import (
    SessionIdRequestDict,
    is_valid_session_id_request,
)

from modules.connection import connection_factory
from modules.exceptions import ErrorDictException
from modules.user import User
import modules.experiment as _experiment
import modules.hub as _hub


class Experimenter(User):
    """Experimenter is a type of modules.user.User with experimenter rights.

    Has access to a different set of API endpoints than other Users.  API endpoints for
    experimenters are defined here.

    See Also
    --------
    experimenter_factory : Instantiate connection with a new Experimenter based on
        WebRTC `offer`.  Use factory instead of instantiating Experimenter directly.
    """

    _experiment: _experiment.Experiment | None
    _hub: _hub.Hub

    def __init__(self, id: str, hub: _hub.Hub) -> None:
        """Instantiate new Experimenter instance.

        Parameters
        ----------
        id : str
            Unique identifier for this Experimenter.
        hub : modules.hub.Hub
            Hub this Experimenter is part of.  Used for api calls.

        See Also
        --------
        experimenter_factory : Instantiate connection with a new Experimenter based on
            WebRTC `offer`.  Use factory instead of instantiating Experimenter directly.
        """
        super().__init__(id)
        self._hub = hub
        self._experiment = None

        # Add API endpoints
        self.on("GET_SESSION_LIST", self._handle_get_session_list)
        self.on("SAVE_SESSION", self._handle_save_session)
        self.on("DELETE_SESSION", self._handle_delete_session)
        self.on("CREATE_EXPERIMENT", self._handle_create_experiment)
        self.on("JOIN_EXPERIMENT", self._handle_join_experiment)
        self.on("START_EXPERIMENT", self._handle_start_experiment)
        self.on("STOP_EXPERIMENT", self._handle_stop_experiment)
        self.on("ADD_NOTE", self._handle_add_note)
        self.on("CHAT", self._handle_chat)
        self.on("KICK_PARTICIPANT", self._handle_kick)
        self.on("BAN_PARTICIPANT", self._handle_ban)
        self.on("MUTE", self._handle_mute)
        self.on("SET_FILTERS", self._handle_set_filters)

    async def _handle_get_session_list(self, _) -> MessageDict:
        """Handle requests with type `GET_SESSION_LIST`.

        Loads all known sessions from session manager.  Responds with type:
        `SESSION_LIST`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SESSION_LIST` and data: list of
            custom_types.session.SessionDict.
        """
        sessions = self._hub.session_manager.get_session_dict_list()
        return MessageDict(type="SESSION_LIST", data=sessions)

    async def _handle_save_session(self, data: SessionDict | Any) -> None:
        """Handle requests with type `SAVE_SESSION`.

        Checks if received data is a valid SessionDict.  Try to update existing session,
        if `id` in data is not a empty string, otherwise try to create new session.

        If the session was newly created, an `CREATED_SESSION` message is send to all
        experimenters.  Otherwise, if the session was updated, an `UPDATED_SESSION` is
        send to all experimenters.

        Parameters
        ----------
        data : any or custom_types.session.SessionDict
            Message data.  Checks if data is valid custom_types.session.SessionDict.

        Raises
        ------
        ErrorDictException
            If data is not a valid SessionDict or session id is not known (cannot update
            unknown session).
        """
        # Data check
        if not is_valid_session(data, True):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid Session object.",
            )

        sm = self._hub.session_manager
        if data["id"] == "":
            # Create new session
            session = sm.create_session(data)

            # Notify all experimenters about the change
            message = MessageDict(type="CREATED_SESSION", data=session.asdict())
            self._hub.send_to_experimenters(message)
            return

        # Update existing session
        session = sm.get_session(data["id"])
        if session is None:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_SESSION",
                description="No session with the given ID found to update.",
            )

        # Check if session has already started and should not be edited anymore
        if session.start_time != 0:
            raise ErrorDictException(
                code=409,
                type="SESSION_ALREADY_STARTED",
                description="Cannot edit session, session has already started.",
            )

        # Check if read only parameters where changed
        # Checks for participant IDs are included in session.update()
        if data["start_time"] != session.start_time:
            raise ErrorDictException(
                code=409,
                type="INVALID_PARAMETER",
                description='Cannot change session "start_time", field is read only.',
            )

        if data["end_time"] != session.end_time:
            raise ErrorDictException(
                code=409,
                type="INVALID_PARAMETER",
                description='Cannot change session "end_time", field is read only.',
            )

        session.update(data)

        # Notify all experimenters about the change
        message = MessageDict(type="UPDATED_SESSION", data=session.asdict())
        self._hub.send_to_experimenters(message)

    async def _handle_delete_session(self, data: SessionIdRequestDict | Any) -> None:
        """Handle requests with type `DELETE_SESSION`.

        Check if data is a valid custom_types.session_id_request.SessionIdRequestDict.
        If found, delete session with the `session_id` in `data`.

        After deletion, a `DELETED_SESSION` message is send to all experimenters.

        Parameters
        ----------
        data : any or custom_types.session_id_request.SessionIdRequestDict
            Message data.

        Raises
        ------
        ErrorDictException
            If data is not a valid dict with an `session_id` str or if `session_id` is
            not known.
        """
        if not is_valid_session_id_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SessionIdRequest.",
            )

        session_id = data["session_id"]
        # Check if there is an experiment running with this session_id
        if session_id in self._hub.experiments:
            raise ErrorDictException(
                code=400,
                type="EXPERIMENT_RUNNING",
                description="Cannot delete session with running experiment.",
            )

        self._hub.session_manager.delete_session(session_id)

        # Notify all experimenters about the change
        message = MessageDict(type="DELETED_SESSION", data=session_id)
        self._hub.send_to_experimenters(message)

    async def _handle_create_experiment(
        self, data: SessionIdRequestDict | Any
    ) -> MessageDict:
        """Handle requests with type `CREATE_EXPERIMENT`.

        Check if data is a valid custom_types.session_id_request.SessionIdRequestDict.
        If found, try to create a new modules.experiment.Experiment based on the session
        with the `session_id` in `data`.

        Sends a `CREATED_EXPERIMENT` message to all experimenters, if experiment was
        successfully started.

        Parameters
        ----------
        data : any or custom_types.session_id_request.SessionIdRequestDict
            Message data.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `JOIN_EXPERIMENT`.

        Raises
        ------
        ErrorDictException
            If data is not a valid dict with an `session_id` str, if `session_id` is not
            known or if there is already an Experiment with `session_id`.
        """
        if not is_valid_session_id_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SessionIdRequest.",
            )

        self._experiment = self._hub.create_experiment(data["session_id"])
        self._experiment.add_experimenter(self)

        # Notify all experimenters about the new experiment
        message = MessageDict(type="CREATED_EXPERIMENT", data=data)
        self._hub.send_to_experimenters(message)

        # Notify caller that he joined the experiment
        success = SuccessDict(
            type="JOIN_EXPERIMENT",
            description="Successfully started and joined experiment.",
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_join_experiment(
        self, data: SessionIdRequestDict | Any
    ) -> MessageDict:
        """Handle requests with type `JOIN_EXPERIMENT`.

        Check if data is a valid custom_types.session_id_request.SessionIdRequestDict.
        If found, try to join an existing modules.experiment.Experiment with the
        `session_id` in `data`.

        Parameters
        ----------
        data : any or custom_types.session_id_request.SessionIdRequestDict
            Message data.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `JOIN_EXPERIMENT`.

        Raises
        ------
        ErrorDictException
            If data is not a valid dict with a `session_id` str or if there is no
            Experiment with `session_id`.
        """
        if not is_valid_session_id_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SessionIdRequest.",
            )

        experiment = self._hub.experiments.get(data["session_id"])

        if experiment is None:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_EXPERIMENT",
                description="There is no experiment with the given ID.",
            )

        self._experiment = experiment
        self._experiment.add_experimenter(self)

        success = SuccessDict(
            type="JOIN_EXPERIMENT", description="Successfully joined experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_start_experiment(self, _) -> MessageDict:
        """Handle requests with type `START_EXPERIMENT`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `START_EXPERIMENT`.

        Raises
        ------
        ErrorDictException
            If this Experimenter is not connected to an modules.experiment.Experiment or
            the Experiment has already started.
        """
        if not self._experiment:
            raise ErrorDictException(
                code=409,
                type="INVALID_REQUEST",
                description=(
                    "Cannot start experiment. Experimenter is not connected to an "
                    "experiment."
                ),
            )

        self._experiment.start()

        success = SuccessDict(
            type="START_EXPERIMENT", description="Successfully started experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_stop_experiment(self, _) -> MessageDict:
        """Handle requests with type `STOP_EXPERIMENT`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `STOP_EXPERIMENT`.

        Raises
        ------
        ErrorDictException
            If this Experimenter is not connected to an modules.experiment.Experiment or
            the Experiment has already ended.
        """
        experiment = self._get_experiment_or_raise("Cannot stop experiment.")
        experiment.stop()

        success = SuccessDict(
            type="STOP_EXPERIMENT", description="Successfully stopped experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_add_note(self, data: NoteDict | Any) -> MessageDict:
        """Handle requests with type `ADD_NOTE`.

        Check if data is a valid custom_types.note.NoteDict and adds the note to the
        modules.experiment.Experiment the Experimenter is connected to.

        Parameters
        ----------
        data : any or custom_types.note.NoteDict
            Message data.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `ADD_NOTE`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.note.NoteDict or if this Experimenter is
            not connected to an modules.experiment.Experiment.
        """
        if not is_valid_note(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid Note.",
            )

        experiment = self._get_experiment_or_raise("Cannot add note.")
        experiment.session.notes.append(data)

        success = SuccessDict(type="ADD_NOTE", description="Successfully added note.")
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_chat(self, data: ChatMessageDict | Any) -> MessageDict:
        """Handle requests with type `CHAT`.

        Check if data is a valid custom_types.chat_message.ChatMessageDict, `target` is
        "experimenter" and pass the request to the experiment.

        Parameters
        ----------
        data : any or custom_types.chat_message.ChatMessageDict
            Message data.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `CHAT`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.chat_message.ChatMessageDict,
            `target` is not "experimenter" or this Experimenter is not connected to an
            modules.experiment.Experiment.
        """
        if not is_valid_chatmessage(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid ChatMessage.",
            )

        if data["author"] != "experimenter":
            raise ErrorDictException(
                code=400,
                type="INVALID_REQUEST",
                description="Author of message must be experimenter.",
            )

        experiment = self._get_experiment_or_raise("Cannot chat.")
        experiment.handle_chat_message(data)

        success = SuccessDict(
            type="CHAT", description="Successfully send chat message."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_kick(self, data: KickRequestDict | Any) -> MessageDict:
        """Handle requests with type `KICK`.

        Check if data is a valid custom_types.kick.KickRequestDict and pass the request
        to the experiment.

        Parameters
        ----------
        data : any or custom_types.kick.KickRequestDict
            Message data.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `KICK`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.kick.KickRequestDict or if this
            Experimenter is not connected to an modules.experiment.Experiment.
        """
        if not is_valid_kickrequest(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid KickRequest.",
            )

        experiment = self._get_experiment_or_raise("Cannot kick participant.")
        await experiment.kick_participant(data["participant_id"], data["reason"])

        success = SuccessDict(
            type="KICK_PARTICIPANT", description="Successfully kicked participant."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_ban(self, data: KickRequestDict | Any) -> MessageDict:
        """Handle requests with type `BAN`.

        Check if data is a valid custom_types.kick.KickRequestDict and pass the request
        to the experiment.

        Parameters
        ----------
        data : any or custom_types.kick.KickRequestDict
            Message data.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `BAN`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.kick.KickRequestDict or if this
            Experimenter is not connected to an modules.experiment.Experiment.
        """
        if not is_valid_kickrequest(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid KickRequest.",
            )

        experiment = self._get_experiment_or_raise("Cannot ban participant.")
        await experiment.ban_participant(data["participant_id"], data["reason"])

        success = SuccessDict(
            type="BAN_PARTICIPANT", description="Successfully banned participant."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_mute(self, data: MuteRequestDict | Any) -> MessageDict:
        """Handle requests with type `MUTE`.

        Check if data is a valid custom_types.mute.MuteRequestDict, parse and pass the
        request to the experiment.

        Parameters
        ----------
        data : any or custom_types.mute.MuteRequestDict
            Message data.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `MUTE`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.mute.MuteRequestDict or if this
            Experimenter is not connected to an modules.experiment.Experiment.
        """
        if not is_valid_mute_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid MuteRequest.",
            )

        experiment = self._get_experiment_or_raise("Failed to mute participant.")
        experiment.mute_participant(
            data["participant_id"], data["mute_video"], data["mute_audio"]
        )

        success = SuccessDict(
            type="MUTE", description="Successfully changed muted state for participant."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_set_filters(
        self, data: SetFiltersRequestDict | Any
    ) -> MessageDict:
        """Handle requests with type `SET_FILTERS`.

        Check if data is a valid custom_types.filters.SetFiltersRequestDict.

        Handling not yet implemented.

        Parameters
        ----------
        data : any or custom_types.filters.SetFiltersRequestDict
            Message data.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `ERROR`, data: custom_types.error.ErrorDict and
            ErrorType type: `NOT_IMPLEMENTED`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.filters.SetFiltersRequestDict.
        """
        if not is_valid_set_filters_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SetFiltersRequest.",
            )

        # TODO implement handling for SET_FILTERS requests.

        response = ErrorDict(
            type="NOT_IMPLEMENTED",
            code=501,
            description="Received valid filters, but feature is not yet implemented.",
        )
        return MessageDict(type="ERROR", data=response)

    def _get_experiment_or_raise(
        self, action_prefix: str = ""
    ) -> _experiment.Experiment:
        """Get `self._experiment` or raise ErrorDictException if it is None.

        Use to check if this Experimenter is connected to an
        modules.experiment.Experiment.

        Parameters
        ----------
        action_prefix : str, optional
            Prefix for the error message.  If not set / default (empty string), the
            error message is: *Experimenter is not connected to an experiment.*,
            otherwise: *<action_prefix> Experimenter is not connected to an experiment.*
            .

        Raises
        ------
        ErrorDictException
            If `self._experiment` is None
        """
        if self._experiment is not None:
            return self._experiment

        if action_prefix == "":
            desc = "Experimenter is not connected to an experiment."
        else:
            desc = f"{action_prefix} Experimenter is not connected to an experiment."

        raise ErrorDictException(
            code=409, type="NOT_CONNECTED_TO_EXPERIMENT", description=desc
        )


async def experimenter_factory(
    offer: RTCSessionDescription, id: str, hub: _hub.Hub
) -> tuple[RTCSessionDescription, Experimenter]:
    """Instantiate connection with a new Experimenter based on WebRTC `offer`.

    Instantiate new modules.experimenter.Experimenter, handle offer using
    modules.connection.connection_factory and set connection for the Experimenter.

    This sequence must be donne for all experimenters.  Instantiating an Experimenter
    directly will likely lead to problems, since it wont have a Connection.

    Parameters
    ----------
    offer : aiortc.RTCSessionDescription
        WebRTC offer for building the connection to the client.
    id : str
        Unique identifier for Experimenter.
    hub : modules.hub.Hub
        Hub the Experimenter will be part of.  Used for api calls.

    Returns
    -------
    tuple with aiortc.RTCSessionDescription, modules.experimenter.Experimenter
        WebRTC answer that should be send back to the client and Experimenter
        representing the client.
    """
    experimenter = Experimenter(id, hub)
    answer, connection = await connection_factory(offer, experimenter.handle_message)
    experimenter.set_connection(connection)
    return (answer, experimenter)
