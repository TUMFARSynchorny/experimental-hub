"""Provide the abstract `User` class.

See Also
--------
modules.participant.Participant : Participant implementation of User.
modules.experimenter.Experimenter : Experimenter implementation of User.
"""

from __future__ import annotations

import logging
import asyncio
import traceback
from abc import ABCMeta, abstractmethod
from typing import Callable, Any, Coroutine
from pyee.asyncio import AsyncIOEventEmitter

from custom_types.ping import PongDict
from custom_types.error import ErrorDict
from filters import FilterDict
from custom_types.message import MessageDict
from session.data.participant.participant_summary import ParticipantSummaryDict
from custom_types.connection import ConnectionOfferDict, is_valid_connection_offer_dict

import modules.experiment as _exp
from modules.util import timestamp
import users.experimenter as _experimenter
from modules.exceptions import ErrorDictException
from modules.connection_state import ConnectionState
from modules.connection_interface import ConnectionInterface


class User(AsyncIOEventEmitter, metaclass=ABCMeta):
    """User class representing a connected client.

    Provides client connection and message handling logic for child classes.

    Extends AsyncIOEventEmitter, providing the following events:
    - `disconnected` : modules.user.User
        Emitted when the connection with the client closes.
    - `CONNECTION_ANSWER` : custom_types.connection.ConnectionAnswerDict
        CONNECTION_ANSWER message received from a client.
    - `connection_set` : User (self)

    Attributes
    ----------
    id : str
        ID of this User.

    Methods
    -------
    on_message(endpoint, handler)
        Register an `handler` function for incoming messages with type `endpoint`.
    handle_message(message)
        Handle incoming message from client.
    set_connection(connection)
        Set the connection of this user.
    send(message)
        Send a custom_types.message.MessageDict to the connected client.
    disconnect()
        Closes the connection with the client.
    add_subscriber(user)
        Add `user` as a subscriber to this User.
    set_muted(video, audio)
        Set the muted state for this user
    get_summary()
        Get summary of User for client

    See Also
    --------
    modules.participant.Participant : Participant implementation of User.
    modules.experimenter.Experimenter : Experimenter implementation of User.

    Notes
    -----
    Messages received from the client are handled using the custom event handler in User
    (add handler using: `on_message` and internally emit event using: `handle_message`).
    Do not confuse this with the events the User provides using the AsyncIOEventEmitter.
    """

    id: str
    _experiment: _exp.Experiment | None
    _logger: logging.Logger
    _muted_video: bool
    _muted_audio: bool
    _connection: ConnectionInterface | None
    _handlers: dict[str, list[Callable[[Any], Coroutine[Any, Any, MessageDict | None]]]]
    __subscribers: dict[str, str]  # User ID -> subconnection_id
    __disconnected: bool
    __lock: asyncio.Lock

    def __init__(
        self, user_id: str, muted_video: bool = False, muted_audio: bool = False
    ) -> None:
        """Instantiate new User base class.

        Should only be called by child classes.

        Parameters
        ----------
        user_id : str
            Unique identifier for this Experimenter.
        muted_video : bool, default False
            Whether the users video should be muted.
        muted_audio : bool, default False
            Whether the users audio should be muted.
        """
        super().__init__()
        self._logger = logging.getLogger(f"User-{user_id}")
        self.id = user_id
        self._experiment = None
        self._muted_video = muted_video
        self._muted_audio = muted_audio
        self._handlers = {}
        self.__subscribers = {}
        self.__disconnected = False
        self._connection = None
        self.__lock = asyncio.Lock()
        self.on_message("PING", self._handle_ping)

    @property
    def muted_video(self) -> bool:
        """bool indicating if the users video is muted."""
        return self._muted_video

    @property
    def muted_audio(self) -> bool:
        """bool indicating if the users audio is muted."""
        return self._muted_audio

    @property
    def recorded(self) -> bool:
        """bool indicating if the users video is recorded."""
        return self._recorded

    @property
    def connection(self) -> ConnectionInterface | None:
        """Get Connection of this User."""
        return self._connection

    @property
    def experiment(self) -> None | _exp.Experiment:
        """Get Experiment this User is connected to.

        Returns
        -------
        None or modules.experiment.Experiment
            None if user is not connected to an experiment, otherwise experiment.

        See Also
        --------
        get_experiment_or_raise : get experiment or raise if experiment is None
        """
        return self._experiment

    def get_summary(self) -> ParticipantSummaryDict | None:
        """Get summary of User for client.

        Base implementation returns None.  Should be implemented in classes extending
        User to provide a summary.

        Returns
        -------
        ParticipantSummaryDict | None
            Summary of user.  Subclasses may override this function and return values
            other than None.

        See Also
        --------
        modules.participant.Participant.get_summary
            Participant implementation for get_summary.
        """
        return None

    def set_connection(self, connection: ConnectionInterface) -> None:
        """Set the connection of this user.

        This should only be used once before using this User.  See factory functions.

        See Also
        --------
        modules.participant.Participant : Participant implementation of User.
        modules.experimenter.Experimenter : Experimenter implementation of User.
        """
        self._logger.debug(f"Added Connection: {repr(connection)}")
        self._connection = connection
        self._connection.add_listener(
            "state_change", self._handle_connection_state_change
        )
        self._connection.add_listener(
            "state_change", self._handle_connection_state_change_user
        )
        self.emit("connection_set", self)

    async def send(self, message: MessageDict) -> None:
        """Send a custom_types.message.MessageDict to the connected client.

        Parameters
        ----------
        message : custom_types.message.MessageDict
            Message for the client.
        """
        if self._connection is not None:
            await self._connection.send(message)
        else:
            self._logger.debug(
                f"Not sending {message['type']} message, connection is None"
            )

    async def disconnect(self) -> None:
        """Disconnect.  Closes the connection with the client."""
        if self._connection is not None:
            await self._connection.stop()
        self._handle_disconnect()

    async def add_subscriber(self, user: User) -> None:
        """Add `user` as a subscriber to this User.

        Sends a `CONNECTION_PROPOSAL` to `user` and waits for an `CONNECTION_OFFER`.
        Will respond with a `CONNECTION_ANSWER` to the `CONNECTION_OFFER` with the same
        `id` as the send proposal.

        Parameters
        ----------
        user : modules.user.User
            New subscriber to this User.

        See Also
        --------
        Connection Protocol Wiki :
            https://github.com/TUMFARSynchrony/experimental-hub/wiki/Connection-Protocol#adding-a-sub-connection
        """
        if self._connection is not None:
            return await self.__add_subscriber(user)
        else:
            # wait for connection, then add subscriber
            @self.once("connection_set")
            async def __add_subscriber_later(_):
                await self.__add_subscriber(user)

    async def __add_subscriber(self, user: User) -> None:
        """Inner, private add_subscriber function called when connection is set.

        See add_subscriber for documentation.
        """
        if self._connection is None:
            self._logger.error(
                "Called __add_subscriber with connection == None. "
                "Failed to add subscriber"
            )
            return

        # Error handling in case multiple users connect simultaneously
        # Abort if user is not yet fully connected
        if user.connection is None:
            self._logger.debug(
                f"Avoid adding not fully connected subscriber: {repr(user)}"
            )
            return

        async with self.__lock:
            # Avoid duplicate subscriptions
            if user.id in self.__subscribers:
                self._logger.debug(f"Avoid adding duplicate subscriber: {repr(user)}")
                return

            self._logger.debug(f"Adding subscriber: {repr(user)}")
            if isinstance(user, _experimenter.Experimenter):
                proposal = await self._connection.create_subscriber_proposal(self.id)
            else:
                proposal = await self._connection.create_subscriber_proposal(
                    self.get_summary()
                )

            msg = MessageDict(type="CONNECTION_PROPOSAL", data=proposal)
            await user.send(msg)

            self.__subscribers[user.id] = proposal["id"]

        @user.once("disconnected")
        def _remove_subscriber(_):
            self._logger.debug(f"subscribers: {self.__subscribers.keys()}")
            if user.id in self.__subscribers:
                self.__subscribers.pop(user.id)

        @user.on("CONNECTION_OFFER")
        async def _handle_offer(offer: ConnectionOfferDict):
            if self._connection is None:
                self._logger.error("Called _handle_offer with connection == None")
                return

            if offer["id"] == proposal["id"]:
                user.remove_listener("CONNECTION_OFFER", _handle_offer)
                try:
                    answer = await self._connection.handle_subscriber_offer(offer)
                except ErrorDictException as err:
                    await user.send(err.error_message)
                    return
                msg = MessageDict(type="CONNECTION_ANSWER", data=answer)
                await user.send(msg)

        @self.on("disconnected")
        def _remove_listener(_):
            try:
                user.remove_listener("CONNECTION_OFFER", _handle_offer)
            except KeyError:
                return

        @user.on("disconnected")
        async def _remove_subconnection(_):
            if self._connection is not None:
                await self._connection.stop_subconnection(proposal["id"])

    async def remove_subscriber(self, user: User) -> None:
        """Remove `user` from the subscribers to this User.

        Stops the SubConnection distributing the steam of this User to `user`.

        Not required if `user` disconnects.

        Parameters
        ----------
        user : modules.user.User
            Subscriber to this User that will be removed.
        """
        self._logger.debug(f"Removing subscriber: {user}")
        subconnection_id = self.__subscribers.pop(user.id, None)
        if subconnection_id is None:
            self._logger.error(
                f"Failed to remove SubConnection, {repr(User)} not found in subscribers"
            )
            return

        if self._connection is None:
            self._logger.error("Can't remove subconnection, connection is None.")
            return

        await self._connection.stop_subconnection(subconnection_id)

    def on_message(
        self,
        endpoint: str,
        handler: Callable[[Any], Coroutine[Any, Any, MessageDict | None]],
    ) -> None:
        """Register an `handler` function for incoming messages with type `endpoint`.

        Parameters
        ----------
        endpoint : str
            Endpoint for `handler`.  When a message with type `endpoint` is received,
            `handler` will be called.
        handler : function(data: Any) -> custom_types.message.MessageDict
            Function that handles incoming data for Messages with type `endpoint`.
        """
        if endpoint in self._handlers:
            self._handlers[endpoint].append(handler)
        else:
            self._handlers[endpoint] = [handler]

    async def handle_message(self, message: MessageDict) -> None:
        """Handle incoming message from client.

        Pass Message data to all functions registered to message type endpoint using
        `on_message`.  Note that `on` is listening for events using AsyncIOEventEmitter,
        not api requests.

        Send responses or exceptions from message handlers to client.

        Parameters
        ----------
        message : custom_types.message.MessageDict
            Incoming message.  Must be a valid MessageDict dictionary.
        """

        endpoint = message["type"]

        if endpoint == "CONNECTION_OFFER":
            if not is_valid_connection_offer_dict(message["data"]):
                self._logger.warning(f"Received invalid CONNECTION_OFFER")
                err = ErrorDict(
                    code=400,
                    type="INVALID_DATATYPE",
                    description="Invalid connection offer dict",
                )
                await self.send(MessageDict(type="ERROR", data=err))
                return
            self.emit("CONNECTION_OFFER", message["data"])
            return

        handler_functions = self._handlers.get(endpoint, None)

        if handler_functions is None:
            self._logger.warning(f"No handler for {endpoint} found")
            return

        self._logger.info(f"Received {endpoint}")
        self._logger.debug(f"Calling {len(handler_functions)} handler(s)")
        for handler in handler_functions:
            try:
                response = await handler(message["data"])
            except ErrorDictException as err:
                self._logger.info(
                    f"Failed to handle {endpoint} message. {err.description}"
                )
                response = err.error_message
            except Exception as err:
                self._logger.error(f"INTERNAL SERVER ERROR: {err}")
                self._logger.error(traceback.format_exc())
                err = ErrorDict(
                    type="INTERNAL_SERVER_ERROR",
                    code=500,
                    description="Internal server error. See server log for details.",
                )
                response = MessageDict(type="ERROR", data=err)

            if response is not None:
                await self.send(response)

    def get_experiment_or_raise(self, action_prefix: str = "") -> _exp.Experiment:
        """Get `self._experiment` or raise ErrorDictException if it is None.

        Use to check if this Experimenter is connected to an
        modules.experiment.Experiment.

        Parameters
        ----------
        action_prefix : str, optional
            Prefix for the error message.  If not set / default (empty string), the
            error message is: *<ClassName> is not connected to an experiment.*,
            otherwise: *<action_prefix> <ClassName> is not connected to an experiment.*
            .

        Raises
        ------
        ErrorDictException
            If `self._experiment` is None
        """
        if self._experiment is not None:
            return self._experiment

        if action_prefix == "":
            desc = f"{self.__class__.__name__} is not connected to an experiment."
        else:
            desc = (
                f"{action_prefix} {self.__class__.__name__} is not connected to an "
                "experiment."
            )

        raise ErrorDictException(
            code=409, type="NOT_CONNECTED_TO_EXPERIMENT", description=desc
        )

    async def set_muted(self, video: bool, audio: bool) -> None:
        """Set the muted state for this user.

        Parameters
        ----------
        video : bool
            Whether the users video should be muted.
        audio : bool
            Whether the users audio should be muted.
        """
        if self._muted_video == video and self._muted_audio == audio:
            return

        self._muted_video = video
        self._muted_audio = audio

        if self._connection is not None:
            await self._connection.set_muted(video, audio)

    async def set_video_filters(self, filters: list[FilterDict]) -> None:
        """Set or update video filters to `filters`.

        Wrapper for modules.connection_interface.ConnectionInterface `set_video_filters`
        , with callback in case the connection is not set

        Parameters
        ----------
        filters : list of filters.FilterDict
            List of video filter configs.
        """
        if self._connection is not None:
            await self._connection.set_video_filters(filters)
        else:

            @self.once("connection_set")
            async def _set_video_filters_later(_):
                if self._connection is None:
                    self._logger.error(
                        "__set_video_filters_later callback failed, _connection is "
                        "None."
                    )
                    return
                await self._connection.set_video_filters(filters)

    async def set_audio_filters(self, filters: list[FilterDict]) -> None:
        """Set or update audio filters to `filters`.

        Wrapper for modules.connection_interface.ConnectionInterface `set_audio_filters`
        , with callback in case the connection is not set

        Parameters
        ----------
        filters : list of filters.FilterDict
            List of audio filter configs.
        """
        if self._connection is not None:
            await self._connection.set_audio_filters(filters)
        else:

            @self.once("connection_set")
            async def _set_audio_filters_later(_):
                if self._connection is None:
                    self._logger.error(
                        "__set_audio_filters_later callback failed, _connection is "
                        "None."
                    )
                    return
                await self._connection.set_audio_filters(filters)

    async def start_recording(self) -> None:
        """Start recording for this user."""
        if self._connection is not None:
            await self._connection.start_recording()

    async def stop_recording(self) -> None:
        """Stop recording for this user."""
        await self._connection.stop_recording()

    def _handle_disconnect(self) -> None:
        """Handle this user disconnecting.

        Emit "disconnected" event and remove all event listeners on user.
        """
        if self.__disconnected:
            return
        self.__disconnected = True
        self._logger.info("Disconnected")
        self.emit("disconnected", self)
        self.remove_all_listeners()

    def _handle_connection_state_change_user(self, state: ConnectionState) -> None:
        """Calls _handle_disconnect if state is CLOSED or FAILED.

        Parameters
        ----------
        state : modules.connection_state.ConnectionState
            New state of `self._connection`.
        """
        if state in [ConnectionState.CLOSED, ConnectionState.FAILED]:
            self._handle_disconnect()

    async def _handle_ping(self, data: Any) -> MessageDict:
        """Handle requests with type `PING`.

        Parameters
        ----------
        data : any
            Message data, can be anything.  Will be included in return message.

        Returns
        -------
        custom_types.message.MessageDict
            MessageDict with type: `PONG`, data: custom_types.ping.PongDict.
        """
        pong = PongDict(server_time=timestamp(), ping_data=data)
        return MessageDict(type="PONG", data=pong)

    @abstractmethod
    async def _handle_connection_state_change(self, state: ConnectionState) -> None:
        """Handler for connection "state_change" event.

        Must be implemented in classes extending User.

        Parameters
        ----------
        state : modules.connection_state.ConnectionState
            New state of the connection this user has with the client.
        """
        pass
