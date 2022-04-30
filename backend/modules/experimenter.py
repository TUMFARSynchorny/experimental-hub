"""TODO document"""

from __future__ import annotations
from aiortc import RTCSessionDescription

from custom_types.message import MessageDict
from custom_types.session import SessionDict
from custom_types.success import SuccessDict
from custom_types.note import NoteDict

from modules.util import check_valid_typed_dict
from modules.connection import connection_factory
from modules.exceptions import ErrorDictException
import modules.experiment as _experiment
import modules.hub as _hub
import modules.user as _user


class Experimenter(_user.User):
    """TODO document"""

    _experiment: _experiment.Experiment
    _hub: _hub.Hub

    def __init__(self, id: str, hub: _hub.Hub):
        """TODO document"""
        super().__init__(id)
        self._hub = hub
        self.on("GET_SESSION_LIST", self._handle_get_session_list)
        self.on("SAVE_SESSION", self._handle_save_session)
        self.on("DELETE_SESSION", self._handle_delete_session)
        self.on("CREATE_EXPERIMENT", self._handle_create_experiment)
        self.on("JOIN_EXPERIMENT", self._handle_join_experiment)
        self.on("START_EXPERIMENT", self._handle_start_experiment)
        self.on("STOP_EXPERIMENT", self._handle_stop_experiment)
        self.on("ADD_NOTE", self._handle_add_note)

    def _handle_get_session_list(self, _):
        """TODO document"""
        sessions = self._hub.session_manager.get_session_dict_list()
        return MessageDict(type="SESSION_LIST", data=sessions)

    def _handle_save_session(self, data):
        """TODO document"""
        # Data check
        if not check_valid_typed_dict(data, SessionDict):
            raise ErrorDictException(
                code=400, type="INVALID_REQUEST", description="Expected session object."
            )
        assert isinstance(data, SessionDict)

        sm = self._hub.session_manager
        if "id" not in data:
            # Create new session
            sm.create_session(data)
        else:
            # Update existing session
            session = sm.get_session(data["id"])
            if session is not None:
                session.update(data)
            else:
                raise ErrorDictException(
                    code=404,
                    type="UNKNOWN_SESSION",
                    description="No session with the given ID found to update.",
                )

        success = SuccessDict(
            type="SAVE_SESSION", description="Successfully saved session."
        )
        return MessageDict(type="SUCCESS", data=success)

    def _handle_delete_session(self, data):
        """TODO document"""
        if "session_id" not in data:
            raise ErrorDictException(
                code=400,
                type="INVALID_REQUEST",
                description="Missing session_id in request.",
            )

        session_id = data["session_id"]
        self._hub.session_manager.delete_session(session_id)

        success = SuccessDict(
            type="DELETE_SESSION", description="Successfully deleted session."
        )
        return MessageDict(type="SUCCESS", data=success)

    def _handle_create_experiment(self, data):
        """TODO document"""
        if "session_id" not in data:
            raise ErrorDictException(
                code=400,
                type="INVALID_REQUEST",
                description="Missing session_id in request.",
            )

        self._experiment = self._hub.create_experiment(data["session_id"])
        self._experiment.add_experimenter(self)

        success = SuccessDict(
            type="CREATE_EXPERIMENT", description="Successfully started session."
        )
        return MessageDict(type="SUCCESS", data=success)

    def _handle_join_experiment(self, data):
        """TODO document"""
        if "session_id" not in data:
            raise ErrorDictException(
                code=400,
                type="INVALID_REQUEST",
                description="Missing session_id in request.",
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

    def _handle_start_experiment(self, _):
        """TODO document"""
        if not self._experiment:
            raise ErrorDictException(
                code=409,
                type="INVALID_REQUEST",
                description=(
                    "Cannot start experiment. Experimenter is not connected to an "
                    + "experiment."
                ),
            )

        self._experiment.start()

        success = SuccessDict(
            type="START_EXPERIMENT", description="Successfully started experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    def _handle_stop_experiment(self, _):
        """TODO document"""
        if not self._experiment:
            raise ErrorDictException(
                code=409,
                type="INVALID_REQUEST",
                description=(
                    "Cannot start experiment. Experimenter is not connected to an "
                    + "experiment."
                ),
            )

        self._experiment.stop()

        success = SuccessDict(
            type="STOP_EXPERIMENT", description="Successfully stopped experiment."
        )
        return MessageDict(type="SUCCESS", data=success)

    def _handle_add_note(self, data):
        """TODO document"""
        if not check_valid_typed_dict(data, NoteDict):
            raise ErrorDictException(
                code=400, type="INVALID_REQUEST", description="Expected note object."
            )
        self._experiment.session.add_note(data)

        success = SuccessDict(type="ADD_NOTE", description="Successfully added note.")
        return MessageDict(type="SUCCESS", data=success)


async def experimenter_factory(offer: RTCSessionDescription, id: str, hub: _hub.Hub):
    """TODO document"""
    experimenter = Experimenter(id, hub)
    answer, connection = await connection_factory(offer, experimenter.handle_message)
    experimenter.set_connection(connection)
    return (answer, experimenter)
