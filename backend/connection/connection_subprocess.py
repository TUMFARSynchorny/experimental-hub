"""Provides the multiprocessing Connection wrapper: ConnectionSubprocess."""

import sys
import time
import json
import logging
import asyncio
from os.path import join
from aiortc import RTCSessionDescription
from typing import Any, Callable, Coroutine, Tuple
from asyncio.subprocess import Process, PIPE, create_subprocess_exec
from connection.messages.rtc_ice_candidate_dict import RTCIceCandidateDict

from connection.messages import (
    ConnectionAnswerDict,
    ConnectionOfferDict,
    RTCSessionDescriptionDict,
    AddIceCandidateDict,
)
from hub import BACKEND_DIR
from server import Config
from hub.exceptions import ErrorDictException
from connection.connection_state import ConnectionState
from connection.connection_interface import ConnectionInterface
from hub.subprocess_logging import handle_log_from_subprocess
from filter_api import FilterAPI, FilterSubprocessReceiver

from custom_types.error import ErrorDict
from filters import FilterDict
from filters.filter_data_dict import FilterDataDict
from custom_types.message import MessageDict
from session.data.participant import ParticipantDict
from session.data.participant.participant_summary import ParticipantSummaryDict


class ConnectionSubprocess(ConnectionInterface):
    """Wrapper executing a hub.connection.Connection on a dedicated subprocess.

    Relays all logging and events from the Connection.

    Implements hub.connection_interface.ConnectionInterface.

    Extends AsyncIOEventEmitter, providing the following events:
    - `state_change` : hub.connection_state.ConnectionState
        Emitted when the state of this connection changes.
    """

    _config: Config
    _offer: RTCSessionDescriptionDict
    _log_name_suffix: str
    _message_handler: Callable[[MessageDict], Coroutine[Any, Any, None]]
    _initial_audio_filters: list[FilterDict]
    _initial_video_filters: list[FilterDict]
    _initial_audio_group_filters: list[FilterDict]
    _initial_video_group_filters: list[FilterDict]
    _filter_receiver: FilterSubprocessReceiver
    _record_data: tuple

    __lock: asyncio.Lock
    _running: bool
    _process: Process | None
    _state: ConnectionState
    _logger: logging.Logger
    _tasks: list[asyncio.Task]
    _command_nr: int
    _responses: dict[int, asyncio.Queue[dict]]

    _local_description_received: asyncio.Event
    _local_description: RTCSessionDescription | None

    def __init__(
            self,
            offer: RTCSessionDescriptionDict,
            message_handler: Callable[[MessageDict], Coroutine[Any, Any, None]],
            log_name_suffix: str,
            config: Config,
            audio_filters: list[FilterDict],
            video_filters: list[FilterDict],
            audio_group_filters: list[FilterDict],
            video_group_filters: list[FilterDict],
            filter_api: FilterAPI,
            record_data: tuple,
    ):
        """Create new ConnectionSubprocess.

        Parameters
        ----------
        offer : connection.messages.rtc_session_description_dict.RTCSessionDescriptionDict
            Initial connection offer.
        message_handler : function (custom_typed.message.MessageDict) -> None
            Handler for incoming messages over the datachannel.  Incoming messages will
            be parsed and type checked (only top level, not including contents of data).
        log_name_suffix : str
            Suffix for logger.  Format: Connection-<log_name_suffix>.
        config : hub.config.Config
            Hub config.
        audio_filters : list of custom_types.filter.FilterDict
            Default audio filters for this connection.
        video_filters : list of custom_types.filter.FilterDict
            Default video filters for this connection.
        record_data : tuple
            Boolean flag for recording the experiment and the path where the recordings will be saved.

        See Also
        --------
        connection_subprocess_factory :
            Factory function to create a new ConnectionSubprocess and get the
            ConnectionSubprocess as well as the response to the initial offer.
        """
        super().__init__()
        self._config = config
        self._offer = offer
        self._log_name_suffix = log_name_suffix
        self._message_handler = message_handler
        self._initial_audio_filters = audio_filters
        self._initial_video_filters = video_filters
        self._initial_audio_group_filters = audio_group_filters
        self._initial_video_group_filters = video_group_filters
        self._record_data = record_data

        self.__lock = asyncio.Lock()
        self._running = True
        self._process = None
        self._state = ConnectionState.NEW
        self._logger = logging.getLogger("ConnectionSubprocess")
        self._filter_receiver = FilterSubprocessReceiver(
            filter_api,
            self._send_command
        )

        self._local_description_received = asyncio.Event()
        self._local_description = None

        self._command_nr = 0
        self._responses = {}

        self._tasks = [
            asyncio.create_task(self._run(), name="ConnectionSubprocess.run")
        ]

    @property
    def state(self) -> ConnectionState:
        # For docstring see ConnectionInterface or hover over function declaration
        return self._state

    async def create_subscriber_proposal(
            self, participant_summary: ParticipantSummaryDict | str | None,
            subscriber: ParticipantDict = None
    ) -> ConnectionOfferDict:
        # For docstring see ConnectionInterface or hover over function declaration
        # Send command and wait for response.
        data = dict()
        data['participant_summary'] = participant_summary
        if subscriber is not None:
            data['subscriber'] = subscriber
        offer = await self._send_command_wait_for_response("CREATE_PROPOSAL", data)
        return offer

    async def handle_add_ice_candidate(self, candidate: RTCIceCandidateDict):
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("ADD_ICE_CANDIDATE", candidate)

    async def handle_subscriber_offer(
            self, offer: ConnectionOfferDict
    ) -> ConnectionAnswerDict:
        # For docstring see ConnectionInterface or hover over function declaration
        # Send command and wait for response.
        answer = await self._send_command_wait_for_response("HANDLE_OFFER", offer)
        return answer

    async def handle_subscriber_add_ice_candidate(
            self, candidate: AddIceCandidateDict
    ):
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("ADD_SUBSCRIBER_ICE_CANDIDATE", candidate)

    async def get_local_description(self) -> RTCSessionDescription:
        """Get localdescription.  Blocks until subprocess sends localdescription."""
        self._logger.debug("Wait for local_description")
        await self._local_description_received.wait()
        self._logger.debug("Return local_description")
        assert self._local_description is not None
        return self._local_description

    async def stop(self) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        self._logger.debug("Stopping ConnectionSubprocess")
        if self._process is not None and self._process.returncode is None:
            self._process.terminate()
        async with self.__lock:
            self._running = False
        current_task = asyncio.current_task()
        tasks = [t for t in self._tasks if t is not current_task]
        await asyncio.gather(*tasks)
        await self._log_final_stdout_stderr()
        self._set_state(ConnectionState.CLOSED)
        self._logger.debug("Stop complete")

    async def send(self, data: MessageDict | dict) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("SEND", data)

    async def stop_subconnection(self, subconnection_id: str) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("STOP_SUBCONNECTION", subconnection_id)

    async def set_muted(self, video: bool, audio: bool) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("SET_MUTED", (video, audio))

    async def set_video_filters(self, filters: list[FilterDict]) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("SET_VIDEO_FILTERS", filters)

    async def set_audio_filters(self, filters: list[FilterDict]) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("SET_AUDIO_FILTERS", filters)

    async def set_video_group_filters(
            self, group_filters: list[FilterDict], ports: list[tuple[int, int]]
    ) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("SET_VIDEO_GROUP_FILTERS", (group_filters, ports))

    async def set_audio_group_filters(
            self, group_filters: list[FilterDict], ports: list[tuple[int, int]]
    ) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("SET_AUDIO_GROUP_FILTERS", (group_filters, ports))

    async def start_recording(self) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("START_RECORDING", None)

    async def stop_recording(self) -> None:
        # For docstring see ConnectionInterface or hover over function declaration
        await self._send_command("STOP_RECORDING", None)

    async def get_video_filters_data(self, id, name) -> list[FilterDataDict]:
        answer = await self._send_command_wait_for_response(
            "GET_VIDEO_FILTERS", {"id": id, "name": name}
        )
        return answer

    async def get_audio_filters_data(self, id, name) -> list[FilterDataDict]:
        answer = await self._send_command_wait_for_response(
            "GET_AUDIO_FILTERS", {"id": id, "name": name}
        )
        return answer

    def _set_state(self, state: ConnectionState) -> None:
        """Set connection state and emit `state_change` event."""
        if self._state == state:
            return

        self._logger.debug(f"ConnectionState is: {state}")
        self._state = state
        self.emit("state_change", state)

    async def _run(self) -> None:
        """Run this subprocess.

        Should be called in new process, returns when child process finished.
        """
        self._logger.debug("Starting subprocess")

        # Start subprocess
        program = [
            sys.executable,
            join(BACKEND_DIR, "subprocess_main.py"),
            "-l",
            self._log_name_suffix,
            "-o",
            json.dumps(self._offer),
            "--audio-filters",
            json.dumps(self._initial_audio_filters),
            "--video-filters",
            json.dumps(self._initial_video_filters),
            "--audio-group-filters",
            json.dumps(self._initial_audio_group_filters),
            "--video-group-filters",
            json.dumps(self._initial_video_group_filters),
            "--record-data",
            json.dumps(self._record_data),
        ]
        program_summary = program[:5] + [
            program[5][:10] + ("..." if len(program[5]) >= 10 else "")
        ]

        self._process = await create_subprocess_exec(
            *program, stdin=PIPE, stderr=PIPE, stdout=PIPE
        )
        self._logger = logging.getLogger(f"ConnectionSubprocess-{self._process.pid}")
        self._logger.debug(
            f"Subprocess started. Program: {program_summary}, PID: {self._process.pid}"
        )

        # Create task listening for messages from subprocess
        self._tasks.append(
            asyncio.create_task(
                self._wait_for_messages(),
                name="ConnectionSubprocess._wait_for_messages",
            )
        )
        if self._config.ping_subprocesses > 0:
            self._tasks.append(
                asyncio.create_task(
                    self._ping(float(self._config.ping_subprocesses)),
                    name="ConnectionSubprocess.ping",
                ),
            )

    async def _ping(self, interval: float) -> None:
        """Send PING message in interval, until self._running is False.

        Used for debugging.

        Parameters
        ----------
        interval : float
            Time between `PING` commands.
        """
        await asyncio.sleep(6)
        self._logger.debug("Start PING loop")
        while True:
            async with self.__lock:
                if not self._running:
                    return
            await self._send_command("PING", time.time())
            await asyncio.sleep(interval)

    async def _wait_for_messages(self) -> None:
        """Receive and handle messages from subprocess via stdout."""
        if self._process is None:
            self._logger.error(
                "Failed to listen for messages from subprocess, _process is None"
            )
            return
        if self._process.stdout is None:
            self._logger.error(
                "Failed to listen for messages from subprocess, _process.stdout is None"
            )
            return

        while True:
            async with self.__lock:
                if not self._running:
                    return

            try:
                msg = await self._process.stdout.readline()
            except ValueError:
                self._logger.error("readline() failed, message was to long.")
                continue

            if len(msg) == 0:
                self._logger.debug(
                    "Stop listening for messages from subprocess, len(msg) == 0"
                )
                await self.stop()
                break

            try:
                parsed = json.loads(msg)
            except (json.JSONDecodeError, TypeError) as e:
                self._logger.debug(f"Msg: {msg}, len: {len(msg)}")
                self._logger.error(f"Failed to parse message from subprocess: {e}")
                continue

            await self._handle_process_message(parsed)

    async def _handle_process_message(self, msg: dict) -> None:
        """Handle a message / command from the subprocess.

        Parameters
        ----------
        msg : dict
            message received from subprocess.
        """
        data = msg["data"]
        command = msg["command"]
        command_nr = msg["command_nr"]

        # self._logger.debug(
        #     f"Received {command} command from subprocess, nr: {command_nr}, data: {data}"
        # )

        match command:
            case "FILTER_API":
                # Forward FILTER_API requests to FilterSubprocessReceiver
                # and send possible answer back to FilterSubprocessAPI
                answer = await self._filter_receiver.handle(data)
                if answer is not None:
                    await self._send_command(
                        "FILTER_API_ANSWER",
                        answer,
                        command_nr
                    )
            case "SET_LOCAL_DESCRIPTION":
                self._local_description = RTCSessionDescription(
                    data["sdp"], data["type"]
                )
                self._local_description_received.set()
            case "PONG":
                t = time.time()
                rtt = round((t - data["original"]) * 1000, 2)
                to_time = round((data["subprocess_time"] - data["original"]) * 1000, 2)
                back_time = round((t - data["subprocess_time"]) * 1000, 2)
                self._logger.debug(
                    f"Subprocess ping: RTT: {rtt}ms, to subprocess: {to_time}ms, back: "
                    f"{back_time}ms"
                )
            case "STATE_CHANGE":
                self._set_state(ConnectionState(data))
            case "API":
                await self._message_handler(data)
            case "CONNECTION_PROPOSAL" | "CONNECTION_ANSWER" | "ACTIVE_VIDEO_FILTERS" | "ACTIVE_AUDIO_FILTERS":
                await self._set_answer(command_nr, data)
            case "LOG":
                handle_log_from_subprocess(data, self._logger)
            case _:
                self._logger.error(f"Unrecognized command from subprocess: {command}")

    async def _log_final_stdout_stderr(self) -> None:
        """Wait for and log potential output on stdout and stderr of exited subprocess.

        Will wait for the subprocess to exit.  Should not be called while listening
        directly to stdout or stderr.
        """
        if self._process is None:
            return

        self._logger.debug("Wait for final stdout and stderr from subprocess")
        stdout, stderr = await self._process.communicate()
        self._logger.debug(
            f"Subprocess exited with returncode: {self._process.returncode}"
        )
        if stdout:
            self._logger.debug(f"[stdout START]:\n {stdout.decode()}\n[stdout END]")
        if stderr:
            self._logger.error(f"[stderr START]:\n {stderr.decode()}\n[stderr END]")

    async def _set_answer(self, command_nr: int, data: dict):
        """Save a answer in `_responses`"""
        queue = self._responses.get(command_nr)
        if queue is None:
            self._logger.error(
                f"Did not find queue for response with command_nr: {command_nr}"
            )
            self._logger.error(f"{command_nr} data: {data}")
            return
        await queue.put(data)

    async def _send_command_wait_for_response(
            self,
            command: str,
            data: str
                  | int
                  | float
                  | dict
                  | None
                  | tuple
                  | ParticipantSummaryDict
                  | ConnectionOfferDict
                  | MessageDict,
            timeout: int | None = None,
            retries: int = 1,
    ) -> dict | None:
        """Send a command including unique command_nr and wait for response.

        Parameters
        ----------
        command : str
            Command / operator for message.
        data : ...
            Data for command / operator.
        timeout : int or None, default None
            timeout for waiting for response
        retries : int = 1
            If > 0, the command will be send again after `timeout` expired.

        Returns
        -------
        None or dict
            None if no response was received, otherwise response

        Raises
        ------
        ErrorDictException
            If the subprocess returned an error custom_types.message.Message.
        """
        for attempt in range(retries + 1):
            if attempt > 0:
                self._logger.debug(
                    f"Retry sending {command}. Attempt: {attempt + 1}/{retries + 1}"
                )
            command_nr = self._command_nr
            self._command_nr += 1
            responseQueue = asyncio.Queue(maxsize=2)
            self._responses[command_nr] = responseQueue

            # Send command and wait for response.  Response should be added to Queue
            # in self._responses[command_num] using _set_answer
            await self._send_command(command, data, command_nr)
            try:
                answer = await asyncio.wait_for(responseQueue.get(), timeout)
            except asyncio.TimeoutError:
                continue
            finally:
                # Remove queue from _responses
                self._responses.pop(command_nr)

            if "type" in answer and answer["type"] == "ERROR":
                err: ErrorDict = answer["data"]
                raise ErrorDictException(
                    code=err["code"], type=err["type"], description=err["description"]
                )

            return answer

    async def _send_command(
            self,
            command: str,
            data: str
                  | int
                  | float
                  | dict
                  | None
                  | tuple
                  | ParticipantSummaryDict
                  | ConnectionOfferDict
                  | MessageDict
                  | list,
            command_nr: int = -1,
    ) -> None:
        """Send command to subprocess via stdin.

        Parameters
        ----------
        command : str
            Command / operator for message.
        data : ...
            Data for command / operator.
        command_nr : int, optional
            Command nr identifying commands with responses.  Only required if response
            must be identified with request.
        """
        data = json.dumps({"command": command, "data": data, "command_nr": command_nr})
        self._logger.debug(data)
        if self._process is None:
            self._logger.error(f"Failed send {data}, _process is None")
            return
        if self._process.stdin is None:
            self._logger.error(f"Failed send {data}, _process.stdin is None")
            return

        async with self.__lock:
            if not self._running:
                self._logger.debug(
                    f"Not sending {command} command, because running is false"
                )
                return
            self._process.stdin.write(data.encode("utf-8") + b"\n")
            await self._process.stdin.drain()


ConnectionInterface.register(ConnectionSubprocess)


async def connection_subprocess_factory(
        offer: RTCSessionDescription,
        message_handler: Callable[[MessageDict], Coroutine[Any, Any, None]],
        log_name_suffix: str,
        config: Config,
        audio_filters: list[FilterDict],
        video_filters: list[FilterDict],
        audio_group_filters: list[FilterDict],
        video_group_filters: list[FilterDict],
        filter_api: FilterAPI,
        record_data: tuple,
) -> Tuple[RTCSessionDescription, ConnectionSubprocess]:
    """Instantiate new ConnectionSubprocess.

    Parameters
    ----------
    offer : aiortc.RTCSessionDescription
        WebRTC offer for building the connection to the client.
    message_handler : function (message: custom_types.message.MessageDict) -> None
        Message handler for ConnectionSubprocess.  ConnectionSubprocess will pass parsed
        MessageDicts to this handler.
    log_name_suffix : str
        Suffix for logger used in Connection.  Format: Connection-<log_name_suffix>.
    audio_filters : list of custom_types.filter.FilterDict
        Default audio filters for this connection.
    video_filters : list of custom_types.filter.FilterDict
        Default video filters for this connection.
    audio_group_filters : list of custom_types.filter.FilterDict
        Default audio group filters for this connection.
    video_group_filters : list of custom_types.filter.FilterDict
        Default video group filters for this connection.
    record_data : tuple
        Boolean flag for recording the experiment and the path where the recordings will be saved.

    Returns
    -------
    tuple with aiortc.RTCSessionDescription, hub.connection_subprocess.ConnectionSubprocess
        WebRTC answer that should be send back to the client and a ConnectionSubprocess.
    """
    offer_dict = RTCSessionDescriptionDict(sdp=offer.sdp, type=offer.type)  # type: ignore

    connection = ConnectionSubprocess(
        offer_dict,
        message_handler,
        log_name_suffix,
        config,
        audio_filters,
        video_filters,
        audio_group_filters,
        video_group_filters,
        filter_api,
        record_data,
    )

    local_description = await connection.get_local_description()

    return (local_description, connection)
