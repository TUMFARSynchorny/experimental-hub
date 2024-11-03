"""Provide the `Experimenter` class and `experimenter_factory` factory function.

Notes
-----
Use experimenter_factory for creating new Experimenters to ensure that they have a valid
hub.connection.Connection.
"""

from __future__ import annotations
import asyncio
import logging
import os
from typing import Any, Coroutine

from filters import filter_utils, filter_factory
from group_filters import group_filter_utils, group_filter_factory
from filters.filters_data_dict import FiltersDataDict
from group_filters.group_filter_factory import create_group_filter
from post_processing.filter_mapping import FILTER_CONFIG_MAPPING
from post_processing.video.analyticsvideoprocessor import AnalyticsVideoProcessor
from post_processing.video.manipulationvideoprocessor import ManipulationVideoProcessor
from post_processing.video.video_post_processor import VideoPostProcessor
from session.data.session import is_valid_session
from custom_types.chat_message import is_valid_chatmessage
from custom_types.kick import is_valid_kickrequest
from custom_types.message import MessageDict
from custom_types.success import SuccessDict
from custom_types.note import is_valid_note
from custom_types.mute import is_valid_mute_request
from custom_types.session_id_request import is_valid_session_id_request
from custom_types.post_processing import is_valid_postprocessingrequest

from connection.connection_state import ConnectionState
from hub.exceptions import ErrorDictException
from post_processing.post_processing_data import PostProcessingData
from post_processing.video.post_processing import VideoPostProcessing
from users.user import User
from users.participant import Participant
import experiment.experiment as _exp
import hub.hub as _h


class Experimenter(User):
    """Experimenter is a type of hub.user.User with experimenter rights.

    Has access to a different set of API endpoints than other Users.  API endpoints for
    experimenters are defined here.

    See Also
    --------
    experimenter_factory : Instantiate connection with a new Experimenter based on
        WebRTC `offer`.  Use factory instead of instantiating Experimenter directly.
    """

    _experiment: _exp.Experiment | None
    _hub: _h.Hub

    def __init__(self, experimenter_id: str, hub: _h.Hub) -> None:
        """Instantiate new Experimenter instance.

        Parameters
        ----------
        experimenter_id : str
            Unique identifier for this Experimenter.
        hub : modules.hub.Hub
            Hub this Experimenter is part of.  Used for api calls.

        See Also
        --------
        experimenter_factory : Instantiate connection with a new Experimenter based on
            WebRTC `offer`.  Use factory instead of instantiating Experimenter directly.
        """
        super(Experimenter, self).__init__(experimenter_id)
        self._logger = logging.getLogger(f"Experimenter-{experimenter_id}")
        self._hub = hub
        self._experiment = None

        # Add API endpoints
        self.on_message("GET_SESSION_LIST", self._handle_get_session_list)
        self.on_message("SAVE_SESSION", self._handle_save_session)
        self.on_message("DELETE_SESSION", self._handle_delete_session)
        self.on_message("CREATE_EXPERIMENT", self._handle_create_experiment)
        self.on_message("JOIN_EXPERIMENT", self._handle_join_experiment)
        self.on_message("LEAVE_EXPERIMENT", self._handle_leave_experiment)
        self.on_message("START_EXPERIMENT", self._handle_start_experiment)
        self.on_message("STOP_EXPERIMENT", self._handle_stop_experiment)
        self.on_message("ADD_NOTE", self._handle_add_note)
        self.on_message("CHAT", self._handle_chat)
        self.on_message("KICK_PARTICIPANT", self._handle_kick)
        self.on_message("BAN_PARTICIPANT", self._handle_ban)
        self.on_message("MUTE", self._handle_mute)
        self.on_message("SET_FILTERS", self._handle_set_filters)
        self.on_message("POST_PROCESSING_VIDEO", self._handle_post_processing_video)
        self.on_message("GET_RECORDING_LIST", self._handle_get_recording_list)
        self.on_message("GET_VIDEO_LIST", self._handle_get_video_list)
        self.on_message("APPLY_FILTER_TO_VIDEO", self._handle_apply_filter_video)
        self.on_message("CHECK_POST_PROCESSING", self._handle_check_post_processing)
        self.on_message("SET_GROUP_FILTERS", self._handle_set_group_filters)
        self.on_message("GET_FILTERS_DATA", self._handle_get_filters_data)
        self.on_message(
            "GET_FILTERS_DATA_SEND_TO_PARTICIPANT",
            self._handle_get_filters_data_send_to_participant,
        )
        self.on_message("GET_SESSION", self._handle_get_session)
        self.on_message("UPDATE_READ_MESSAGE_TIME", self._handle_message_read_time)
        self.on_message("GET_FILTERS_CONFIG", self._handle_get_filters_config)

    def __str__(self) -> str:
        """Get string representation of this experimenter.

        Currently, returns value of `__repr__`.
        """
        return f"id={self.id}, experiment={str(self._experiment)}"

    def __repr__(self) -> str:
        """Get representation of this experimenter."""
        return f"Experimenter({str(self)})"

    async def _handle_connection_state_change(self, state: ConnectionState) -> None:
        """Handler for connection "state_change" event.

        Implements the abstract `_handle_connection_state_change` function in
        hub.user.User.

        Parameters
        ----------
        state : hub.connection_state.ConnectionState
            New state of the connection this Experimenter has with the client.
        """
        self._logger.debug(f"Handle state change. State: {state}")
        if state is ConnectionState.CONNECTED:
            self._logger.info(f"Experimenter connected. {str(self)}")
            await self._subscribe_to_participants_streams()

    async def _subscribe_to_participants_streams(self) -> None:
        """Subscribe to all participants in `self._experiment`."""
        if self._experiment is not None:
            coroutines: list[Coroutine] = []
            for p in self._experiment.participants.values():
                if p is self:
                    continue
                coroutines.append(p.add_subscriber(self))
            await asyncio.gather(*coroutines)

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

    async def _handle_save_session(self, data: Any) -> MessageDict:
        """Handle requests with type `SAVE_SESSION`.

        Checks if received data is a valid SessionDict.  Try to update existing session,
        if `id` in data is not an empty string, otherwise try to create new session.

        As a response, `SAVED_SESSION` is sent to the caller.  Additionally,
        `SESSION_CHANGE` is sent to all other experimenters connected to the hub.

        Parameters
        ----------
        data : any or session.data.session.SessionDict
            Message data, can be anything.  Everything other than
            custom_types.session_id_request.SessionIdRequestDict will raise a
            hub.exceptions.ErrorDictException.

        Raises
        ------
        ErrorDictException
            If data is not a valid SessionDict or session id is not known (cannot update
            unknown session).
        """
        # Data check
        if not is_valid_session(data):
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
            session_dict = session.asdict()
            message = MessageDict(type="SESSION_CHANGE", data=session_dict)
            await self._hub.send_to_experimenters(message, self)
            return MessageDict(type="SAVED_SESSION", data=session_dict)

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
                type="EXPERIMENT_ALREADY_STARTED",
                description="Cannot edit session, session has already started.",
            )

        # Check if read only parameters where changed
        # Checks for participant IDs are included in session.update()
        if data["creation_time"] != session.creation_time:
            raise ErrorDictException(
                code=409,
                type="INVALID_PARAMETER",
                description=(
                    'Cannot change session "creation_time", field is read only.'
                ),
            )

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
        session_dict = session.asdict()
        message = MessageDict(type="SESSION_CHANGE", data=session_dict)
        await self._hub.send_to_experimenters(message, self)

        return MessageDict(type="SAVED_SESSION", data=session_dict)

    async def _handle_delete_session(self, data: Any) -> None:
        """Handle requests with type `DELETE_SESSION`.

        Check if data is a valid custom_types.session_id_request.SessionIdRequestDict.
        If found, delete session with the `session_id` in `data`.

        After deletion, a `DELETED_SESSION` message is send to all experimenters.

        Parameters
        ----------
        data : any or custom_types.session_id_request.SessionIdRequestDict
            Message data, can be anything.  Everything other than
            custom_types.session_id_request.SessionIdRequestDict will raise a
            hub.exceptions.ErrorDictException.

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
        await self._hub.send_to_experimenters(message)

    async def _handle_create_experiment(self, data: Any) -> MessageDict:
        """Handle requests with type `CREATE_EXPERIMENT`.

        Check if data is a valid custom_types.session_id_request.SessionIdRequestDict.
        If found, try to create a new hub.experiment.Experiment based on the session
        with the `session_id` in `data`.

        Experimenters are notified using a `EXPERIMENT_CREATED` message by the hub.

        Parameters
        ----------
        data : any or custom_types.session_id_request.SessionIdRequestDict
            Message data, can be anything.  Everything other than
            custom_types.session_id_request.SessionIdRequestDict will raise a
            hub.exceptions.ErrorDictException.

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

        self._experiment = await self._hub.create_experiment(data["session_id"])
        self._experiment.add_experimenter(self)
        self._logger.info(f"sending ws message. {str(self)}")

        await self._hub.notify_participants_experimenter_joined({"type": "EXPERIMENTER_JOINED"})

        # Subscribe to participants in experiment
        await self._subscribe_to_participants_streams()

        # Notify caller that he joined the experiment
        success = SuccessDict(
            type="JOIN_EXPERIMENT",
            description="Successfully started and joined experiment.",
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_join_experiment(self, data: Any) -> MessageDict:
        """Handle requests with type `JOIN_EXPERIMENT`.

        Check if data is a valid custom_types.session_id_request.SessionIdRequestDict.
        If found, try to join an existing hub.experiment.Experiment with the
        `session_id` in `data`.

        Parameters
        ----------
        data : any or custom_types.session_id_request.SessionIdRequestDict
            Message data, can be anything.  Everything other than
            custom_types.session_id_request.SessionIdRequestDict will raise a
            hub.exceptions.ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `JOIN_EXPERIMENT`.

        Raises
        ------
        ErrorDictException
            If data is not a valid dict with a `session_id` str or if there is no
            Experiment with `session_id`. Also raises if this experimenter is already
            part of an experiment.
        """
        if not is_valid_session_id_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SessionIdRequest.",
            )

        if self._experiment is not None:
            raise ErrorDictException(
                code=409,
                type="ALREADY_JOINED_EXPERIMENT",
                description=(
                    "Can not join an experiment while already connected to an "
                    "experiment."
                ),
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
        self._logger.info(f"sending ws message. {str(self)}")

        await self._hub.notify_participants_experimenter_joined({"type": "EXPERIMENTER_JOINED"})

        # Subscribe to participants in experiment
        await self._subscribe_to_participants_streams()

        success = SuccessDict(
            type="JOIN_EXPERIMENT", description="Successfully joined experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_leave_experiment(self, _) -> MessageDict:
        """Handle requests with type `LEAVE_EXPERIMENT`.

        If part of an experiment, remove self from experiment and set `self._experiment`
        to None.

        Raises
        ------
        ErrorDictException
            If this Experimenter is not connected to a hub.experiment.Experiment.
        """
        experiment = self.get_experiment_or_raise("Failed to leave experiment.")
        experiment.remove_experimenter(self)

        for participant in experiment.participants.values():
            await participant.remove_subscriber(self)

        self._experiment = None

        success = SuccessDict(
            type="LEAVE_EXPERIMENT", description="Successfully left experiment."
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
            If this Experimenter is not connected to a hub.experiment.Experiment or
            the Experiment has already started.
        """
        experiment = self.get_experiment_or_raise("Cannot start experiment.")
        await experiment.start()


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
            If this Experimenter is not connected to a hub.experiment.Experiment or
            the Experiment has already ended.
        """
        experiment = self.get_experiment_or_raise("Cannot stop experiment.")
        await experiment.stop()

        success = SuccessDict(
            type="STOP_EXPERIMENT", description="Successfully stopped experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_add_note(self, data: Any) -> MessageDict:
        """Handle requests with type `ADD_NOTE`.

        Check if data is a valid custom_types.note.NoteDict and adds the note to the
        hub.experiment.Experiment the Experimenter is connected to.

        Parameters
        ----------
        data : any or custom_types.note.NoteDict
            Message data, can be anything.  Everything other than
            custom_types.note.NoteDict will raise a
            hub.exceptions.ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `ADD_NOTE`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.note.NoteDict or if this Experimenter is
            not connected to a hub.experiment.Experiment.
        """
        if not is_valid_note(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid Note.",
            )

        experiment = self.get_experiment_or_raise("Cannot add note.")
        experiment.session.notes.append(data)

        success = SuccessDict(type="ADD_NOTE", description="Successfully added note.")
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_chat(self, data: Any) -> MessageDict:
        """Handle requests with type `CHAT`.

        Check if data is a valid custom_types.chat_message.ChatMessageDict, `target` is
        "experimenter" and pass the request to the experiment.

        Parameters
        ----------
        data : any or custom_types.chat_message.ChatMessageDict
            Message data, can be anything.  Everything other than
            custom_types.chat_message.ChatMessageDict will raise an ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `CHAT`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.chat_message.ChatMessageDict,
            `target` is not "experimenter" or this Experimenter is not connected to a
            hub.experiment.Experiment.
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

        experiment = self.get_experiment_or_raise("Cannot send chat message.")
        await experiment.handle_chat_message(data)

        success = SuccessDict(
            type="CHAT", description="Successfully send chat message."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_kick(self, data: Any) -> MessageDict:
        """Handle requests with type `KICK`.

        Check if data is a valid custom_types.kick.KickRequestDict and pass the request
        to the experiment.

        Parameters
        ----------
        data : any or custom_types.kick.KickRequestDict
            Message data, can be anything.  Everything other than
            custom_types.kick.KickRequestDict will raise an ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `KICK`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.kick.KickRequestDict or if this
            Experimenter is not connected to a hub.experiment.Experiment.
        """
        if not is_valid_kickrequest(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid KickRequest.",
            )

        experiment = self.get_experiment_or_raise("Cannot kick participant.")
        await experiment.kick_participant(data["participant_id"], data["reason"])

        success = SuccessDict(
            type="KICK_PARTICIPANT", description="Successfully kicked participant."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_ban(self, data: Any) -> MessageDict:
        """Handle requests with type `BAN`.

        Check if data is a valid custom_types.kick.KickRequestDict and pass the request
        to the experiment.

        Parameters
        ----------
        data : any or custom_types.kick.KickRequestDict
            Message data, can be anything.  Everything other than
            custom_types.kick.KickRequestDict will raise an ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `BAN`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.kick.KickRequestDict or if this
            Experimenter is not connected to a hub.experiment.Experiment.
        """
        if not is_valid_kickrequest(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid KickRequest.",
            )

        experiment = self.get_experiment_or_raise("Cannot ban participant.")
        await experiment.ban_participant(data["participant_id"], data["reason"])

        success = SuccessDict(
            type="BAN_PARTICIPANT", description="Successfully banned participant."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_mute(self, data: Any) -> MessageDict:
        """Handle requests with type `MUTE`.

        Check if data is a valid custom_types.mute.MuteRequestDict, parse and pass the
        request to the experiment.

        Parameters
        ----------
        data : any or custom_types.mute.MuteRequestDict
            Message data, can be anything.  Everything other than
            custom_types.mute.MuteRequestDict will raise an ErrorDictException.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `MUTE`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.mute.MuteRequestDict or if this
            Experimenter is not connected to a hub.experiment.Experiment.
        """
        if not is_valid_mute_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid MuteRequest.",
            )

        experiment = self.get_experiment_or_raise("Failed to mute participant.")
        await experiment.mute_participant(
            data["participant_id"], data["mute_video"], data["mute_audio"]
        )

        success = SuccessDict(
            type="MUTE", description="Successfully changed muted state for participant."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_set_filters(self, data: Any) -> MessageDict:
        """Handle requests with type `SET_FILTERS`.

        Check if data is a valid custom_types.filters.SetFiltersRequestDict.

        Parameters
        ----------
        data : any or filters.SetFiltersRequestDict
            Message data.  Checks if data is a valid SetFiltersRequestDict and raises
            an ErrorDictException if not.

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
        if not filter_utils.is_valid_set_filters_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SetFiltersRequest.",
            )

        participant_id = data["participant_id"]
        video_filters = data["video_filters"]
        audio_filters = data["audio_filters"]
        experiment = self.get_experiment_or_raise("Failed to set filters.")
        coroutines = []

        if participant_id == "all":
            # Update participant data
            for p_data in experiment.session.participants.values():
                p_data.video_filters = video_filters
                p_data.audio_filters = audio_filters

            # Update connected Participants
            for p in experiment.participants.values():
                if p.connection is not None:
                    coroutines.append(p.set_video_filters(video_filters))
                    coroutines.append(p.set_audio_filters(audio_filters))

        elif participant_id in experiment.session.participants:
            # Update participant data
            p_data = experiment.session.participants[participant_id]
            p_data.video_filters = video_filters
            p_data.audio_filters = audio_filters

            # Update connected Participant
            p = experiment.participants.get(participant_id)
            if p is not None:
                coroutines.append(p.set_video_filters(video_filters))
                coroutines.append(p.set_audio_filters(audio_filters))
        else:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_PARTICIPANT",
                description=f'Unknown participant ID: "{participant_id}".',
            )
        await asyncio.gather(*coroutines)

        # Notify Experimenters connected to the hub about the data change
        message = MessageDict(type="SESSION_CHANGE", data=experiment.session.asdict())
        await self._hub.send_to_experimenters(message)

        # Respond with success message
        success = SuccessDict(
            type="SET_FILTERS", description="Successfully changed filters."
        )
        return MessageDict(type="SUCCESS", data=success)


    async def _handle_post_processing_video(self, data: Any) -> MessageDict:
        """Handle requests with type `POST_PROCESSING_VIDEO`.

        Check if data is a valid custom_types.post_processing.PostProcessingDict.

        Parameters
        ----------
        data : any or post_processing.PostProcessingDict
            Message data.  Checks if data is a valid PostProcessingDict and raises
            an ErrorDictException if not.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `SUCCESS`, data: custom_types.success.SuccessDict and
            SuccessDict type: `POST_PROCESSING_VIDEO`.

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.post_processing.PostProcessingDict or if the
            result directory of post-processing already exists or if current session folder is
            not found.
        """

        if not is_valid_postprocessingrequest(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid PostProcessingDict.",
            )

        video_post_processing = VideoPostProcessing()
        status = video_post_processing.check_existing_process()

        if status["is_processing"]:
            raise ErrorDictException(
                code=102,
                type="STILL_PROCESSING",
                description="There is a running FeatureExtraction subprocess. Please wait until it is complete."
            )

        session_id = data["session_id"]
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sessions",
                                    session_id,
                                    "processed")

        if os.path.exists(out_dir):
            raise ErrorDictException(
                code=409,
                type="FILE_ALREADY_EXISTS",
                description=f'File already exists: {out_dir}. The post-processing of this session is done.'
            )

        video_list = []
        recording_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sessions")
        try:
            recorded_list = os.listdir(os.path.join(recording_path, session_id))
        except FileNotFoundError:
            raise ErrorDictException(
                code=404,
                type="FILE_NOT_FOUND",
                description=f'File not found: {os.path.join(recording_path, session_id)}.'
            )
        for i in range(len(recorded_list)):
            filename = recorded_list[i]
            _, file_extension = os.path.splitext(filename)
            if file_extension == ".mp4":
                participant_id = filename.split("_")[0]
                video_list.append(PostProcessingData("video", filename, session_id, participant_id))
            else:
                continue

        if (len(video_list) == 0):
            raise ErrorDictException(
                code=404,
                type="FILE_NOT_FOUND",
                description=f'No video recordings available for session {session_id}.'
            )

        video_post_processing.recording_list = video_list
        video_post_processing.execute()

        return MessageDict(type="POST_PROCESSING_VIDEO", data=f"Start video post-processing. Result directory: {out_dir}")

    async def _handle_get_recording_list(self, _) -> MessageDict:
        """Handle requests with type `GET_RECORDING_LIST`.

        Loads all video and audio from sessions folder.  Responds with type:
        `RECORDING_LIST`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `RECORDING_LIST`.
        """
        recording_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sessions")
        recordings = [ item for item in os.listdir(recording_path)
                      if os.path.isdir(os.path.join(recording_path, item)) ]
        result = []
        for session_id in recordings:
            try:
                session_response = await self._handle_get_session({"session_id": session_id})
            except ErrorDictException:
                # Skip unknown folder
                continue
            session_data = session_response.get("data")
            past_experiment_path = os.path.join(recording_path, session_id)
            recorded_list = os.listdir(past_experiment_path)
            participants = []
            videos = []
            audios = []
            prev_participant_id = ""
            curr_participant_id = ""

            for i in range(len(recorded_list)):
                filename = recorded_list[i]
                _, file_extension = os.path.splitext(filename)
                if file_extension not in [".mp4", ".mp3"]:
                    self._logger.debug("Not an audio or video file: " + filename)
                    continue
                elif file_extension == ".mp4":
                    videos.append(filename)
                elif file_extension == ".mp3":
                    audios.append(filename)


                curr_participant_id = filename.split("_")[0]
                if (i == 0):
                    prev_participant_id = curr_participant_id

                if prev_participant_id != curr_participant_id:
                    participants.append({
                        "participant_id": prev_participant_id,
                        "video": videos,
                        "audio": audios
                    })
                    prev_participant_id = curr_participant_id
                    videos = []
                    audios = []


            if len(videos) > 0 or len(audios) > 0:
                participants.append({
                    "participant_id": prev_participant_id,
                    "video": videos,
                    "audio": audios
                })
                videos = []
                audios = []

            result.append({
                "session_id": session_id,
                "session_title": session_data.get("title"),
                "session_description": session_data.get("description"),
                "participants": participants
            })

        return MessageDict(type="RECORDING_LIST", data=result)

    async def _handle_get_video_list(self, message: MessageDict) -> MessageDict:
        """Handle requests with type `GET_VIDEO_LIST`.

        Fetches all video files from a specified session directory.

        Parameters
        ----------
        message : MessageDict
            Contains session_id to fetch videos.

        Returns
        -------
        MessageDict
            MessageDict with type: `VIDEO_LIST` and data containing video files.
        """
        self._logger.debug("Handling GET_VIDEO_LIST message")

        session_id = message.get("session_id")
        if not session_id:
            self._logger.error("Session ID missing from message")
            return MessageDict(type="ERROR", data={"message": "Session ID is required."})

        sessions_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sessions")
        session_path = os.path.join(sessions_path, session_id)
        self._logger.debug(f"Constructed session path: {session_path}")

        try:
            video_files = [file for file in os.listdir(session_path) if file.endswith('.mp4')]
            self._logger.info(f"Found {len(video_files)} video files in session: {session_id}")
            return MessageDict(type="VIDEO_LIST", data={"videos": video_files})
        except FileNotFoundError:
            self._logger.error(f"Session directory does not exist: {session_path}")
            return MessageDict(type="ERROR", data={"message": "Session directory does not exist."})
        except Exception as e:
            self._logger.exception(f"An error occurred while trying to list video files in session: {session_id}")
            return MessageDict(type="ERROR", data={"message": str(e)})

    async def _handle_check_post_processing(self, _) -> MessageDict:
        """Handle requests with type `CHECK_POST_PROCESSING`.

        Check whether there is FeatureExtraction process running in the background.
        Responds with type: `CHECK_POST_PROCESSING`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `CHECK_POST_PROCESSING`.
        """
        video_post_processing = VideoPostProcessing()
        status = video_post_processing.check_existing_process()

        result = {
            "description": status["message"],
            "is_processing": status["is_processing"]
        }

        if not result["is_processing"] and result["description"] != "":
            success = SuccessDict(
                type="POST_PROCESSING_VIDEO", description=result["description"]
            )
            return MessageDict(type="SUCCESS", data=success)

        return MessageDict(type="CHECK_POST_PROCESSING", data=result)

    async def _handle_set_group_filters(self, data: Any) -> MessageDict:
        if not group_filter_utils.is_valid_set_group_filters_request(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid SetGroupFiltersRequest.",
            )

        video_group_filters = data["video_group_filters"]
        video_group_filter_ports = []
        for _ in video_group_filters:
            video_group_filter_ports.append(
                (
                    group_filter_utils.find_an_available_port(),  # To send individual data to the aggragator
                    group_filter_utils.find_an_available_port(),  # To send the aggregation result to each participant
                )
            )

        audio_group_filters = data["audio_group_filters"]
        audio_group_filter_ports = []
        for _ in audio_group_filters:
            audio_group_filter_ports.append(
                (
                    group_filter_utils.find_an_available_port(),  # To send individual data to the aggragator
                    group_filter_utils.find_an_available_port(),  # To send the aggregation result to each participant
                )
            )

        experiment = self.get_experiment_or_raise("Failed to set filters.")
        coroutines = []

        # Update experiment with group filter aggregator
        coroutines.append(
            experiment.set_video_group_filter_aggregators(
                video_group_filters, video_group_filter_ports
            )
        )
        coroutines.append(
            experiment.set_audio_group_filter_aggregators(
                audio_group_filters, audio_group_filter_ports
            )
        )

        # Update participant data
        for p_data in experiment.session.participants.values():
            p_data.video_group_filters = video_group_filters
            p_data.audio_group_filters = audio_group_filters

        # Update connected Participants
        for p in experiment.participants.values():
            if p.connection is not None:
                coroutines.append(
                    p.set_video_group_filters(
                        video_group_filters, video_group_filter_ports
                    )
                )
                coroutines.append(
                    p.set_audio_group_filters(
                        audio_group_filters, audio_group_filter_ports
                    )
                )
        await asyncio.gather(*coroutines)

        # Notify Experimenters connected to the hub about the data change
        message = MessageDict(type="SESSION_CHANGE", data=experiment.session.asdict())
        await self._hub.send_to_experimenters(message)

        # Respond with success message
        success = SuccessDict(
            type="SET_GROUP_FILTERS", description="Successfully changed group filters."
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_get_filters_data(self, data: Any) -> MessageDict:
        """Handle requests with type `GET_FILTERS_DATA`.

        Check if data is a valid GetFiltersDataRequestDict and return filter data for
        all participants.

        Parameters
        ----------
        data : any or filters.GetFiltersDataRequestDict
            Message data.  Checks if data is a valid GetFiltersDataRequestDict and raises
            an ErrorDictException if not.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `FILTERS_DATA`, data: dict[str, FiltersDataDict]

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.filters.GetFiltersDataRequestDict.
            Or if values of data are incorrect.
        """
        if not filter_utils.is_valid_get_filters_data_dict(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid GetFiltersData.",
            )

        res = await self.get_filters_data_for_all_participants(data)
        return MessageDict(type="FILTERS_DATA", data=res)

    def get_participant_or_raise(self, participant_id: str) -> Participant:
        """Get Participant with ID `participant_id` or raise ErrorDictException.

        Use to check if a Participant with `participant_id` exists.

        Parameters
        ----------
        participant_id : str
            ID of the participant to get.

        Raises
        ------
        ErrorDictException
            If `self._experiment` is None or if `participant_id` is not in
            `self._experiment.participants`.
        """
        experiment = self.get_experiment_or_raise("Failed to get filters data.")
        if participant_id not in experiment.participants:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_PARTICIPANT",
                description=f'Participant with id "{participant_id}" not found.',
            )
        return experiment.participants[participant_id]

    async def _handle_get_filters_data_send_to_participant(
        self, data: Any
    ) -> MessageDict:
        """Handle requests with type `GET_FILTERS_DATA_SEND_TO_PARTICIPANT`.

        Check if data is a valid GetFiltersDataSendToParticipantRequestDict and return filter test
        statuses for all participants or specific participant.

        Parameters
        ----------
        data : any or filters.GetFiltersDataSendToParticipantRequestDict
            Message data.  Checks if data is a valid GetFiltersDataSendToParticipantRequestDict and
            raises an ErrorDictException if not.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `FILTERS_DATA`, data: dict[str, FiltersDataDict]

        Raises
        ------
        ErrorDictException
            If data is not a valid custom_types.filters.GetFiltersDataSendToParticipantRequestDict.
            Or if values of data are incorrect.
        """
        if not filter_utils.is_valid_get_filters_data_send_to_participant_dict(data):
            raise ErrorDictException(
                code=400,
                type="INVALID_DATATYPE",
                description="Message data is not a valid GET_FILTERS_DATA_SEND_TO_PARTICIPANT.",
            )

        participant_id = data.pop("participant_id")

        if participant_id == "all":
            res = await self.get_filters_data_for_all_participants(data)
            # send message to all participants
            participant_id = "participants"
        else:
            participant = self.get_participant_or_raise(participant_id)
            res: dict[str, FiltersDataDict] = {}

            res[
                participant_id
            ] = await participant.get_filters_data_for_one_participant(data)

        answer = MessageDict(type="FILTERS_DATA", data=res)
        await self._experiment.send(participant_id, answer)

        success = SuccessDict(
            type="SEND_TO_PARTICIPANT",
            description="Successfully sent GET_FILTERS_DATA to participant.",
        )
        return MessageDict(type="SUCCESS", data=success)

    async def _handle_get_session(self, data: Any) -> MessageDict:
        """Handle requests with type `GET_SESSION`.

        Loads session with given id from session manager.  Responds with type:
        `GET_SESSION`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict with type: `SESSION` and data: custom_types.session.SessionDict.
        """
        session = self._hub.session_manager.get_session(data["session_id"])
        if session is None:
            raise ErrorDictException(
                code=404,
                type="UNKNOWN_SESSION",
                description=f"No session with the given ID found: {data['session_id']}.",
            )
        session_dict = session.asdict()
        return MessageDict(type="SESSION", data=session_dict)

    async def _handle_get_filters_config(self, _) -> MessageDict:
        """Handle requests with type `GET_FILTERS_CONFIG`.

        Responds with type: `FILTERS_CONFIG`.

        Parameters
        ----------
        _ : any
            Message data.  Ignored / not required.

        Returns
        -------
        custom_types.message.MessageDict with type: `FILTERS_CONFIG` and data:
         custom_types.filter_config.FilterConfigDict.
        """
        return MessageDict(
            type="FILTERS_CONFIG", data=filter_utils.get_filters_config()
        )

    async def _handle_message_read_time(self, data: Any) -> None:
        experiment = self.get_experiment_or_raise("Failed to mute participant.")
        await experiment.set_message_read_time(
            data["participant_id"], data["lastMessageReadTime"]
        )

    async def _handle_apply_filter_video(self, data: Any) -> MessageDict:
        """Handle requests with type `APPLY_FILTER_VIDEO`.

        Parameters
        ----------
        data : Any
            Expected to contain 'session_id', and 'videos', which is a list of dictionaries with 'video_filename' and 'filter_configs'.

        Returns
        -------
        MessageDict
            Returns a success message upon completion or raises an error if issues are found.

        Raises
        ------
        ErrorDictException
            Raised for various errors including invalid data or processing errors.
        """
        self._logger.info(data)

        if "session_id" not in data or "videoFilterRequests" not in data:
            raise ErrorDictException(
                code=400,
                type="INVALID_REQUEST",
                description="Missing required fields: session_id or videos."
            )

        session_id = data["session_id"]
        video_requests = data["videoFilterRequests"]

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sessions_path = os.path.join(base_dir, "sessions")
        output_dir = os.path.join(sessions_path, session_id, "processed")
        os.makedirs(output_dir, exist_ok=True)

        results = []
        video_post_processor = VideoPostProcessor([])

        for request in video_requests:
            video_filenames = request.get("video_filenames")
            filter_configs = request.get("filter_configs")

            if not video_filenames or not filter_configs:
                raise ErrorDictException(
                    code=400,
                    type="INVALID_REQUEST",
                    description="Each video request must contain 'video_filenames' and 'filter_configs'."
                )

            processor_type, external_process = self._get_processor_type(filter_configs)
            video_processor = self._create_video_processor(processor_type, filter_configs, session_id, video_filenames,
                                                           sessions_path, output_dir, external_process)

            video_post_processor.video_processors.append(video_processor)

        await video_post_processor.execute()

        for filename in video_filenames:
            results.append({
                 "video_filename": filename,
                 "output_path": os.path.join(output_dir,
                                            filename) if processor_type == "manipulation" else os.path.join(
                 output_dir, f"{filename}.csv"),
                 "status": "success"
                })

        # Return a summary of the processing
        return MessageDict(
            type="SUCCESS",
            data={"results": results}
        )

    def _get_processor_type(self, filter_configs):
        """Determine the processor type (manipulative or analysis) based on the filter configs."""
        processor_types = set(FILTER_CONFIG_MAPPING[cfg.get("name")]["type"] for cfg in filter_configs)
        if len(processor_types) != 1:
            raise ErrorDictException(
                code=400,
                type="INVALID_FILTER",
                description="All filters must be of the same processor type."
            )

        external_process = any(FILTER_CONFIG_MAPPING[cfg.get("name")]["externalProcess"] for cfg in filter_configs)

        return processor_types.pop(), external_process

    def _create_video_processor(self, processor_type, filter_configs, session_id, video_filenames, sessions_path,
                                output_dir, external_process):
        """Create a VideoProcessor based on the processor type."""
        filters = [filter_factory.create_filter(cfg) for cfg in filter_configs if not cfg.get('groupFilter')]
        group_filters = [create_group_filter(cfg, session_id) for cfg in filter_configs if cfg.get('groupFilter')]

        if processor_type == "manipulation":
            return ManipulationVideoProcessor(session_id, video_filenames, sessions_path, output_dir, filters,
                                              group_filters, external_process)
        elif processor_type == "analysis":
            return AnalyticsVideoProcessor(session_id, video_filenames, sessions_path, output_dir, filters,
                                           group_filters, external_process)
        else:
            raise ErrorDictException(
                code=400,
                type="INVALID_FILTER",
                description=f"Unknown processor type: {processor_type}"
            )