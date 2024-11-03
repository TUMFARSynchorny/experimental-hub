"""Provide abstract `GroupFilter` class."""

from __future__ import annotations

import numpy
import zmq
import zmq.asyncio
import pickle
from typing import TypeGuard
from abc import ABC, abstractmethod
from av import VideoFrame, AudioFrame

from custom_types import util
from filters.filter_dict import FilterDict
from filters.simple_line_writer import SimpleLineWriter
import logging
from typing import Any
from time import perf_counter


AGGREGRATION_RESULT_ZMQ_TOPIC = "aggregation_result"


class GroupFilter(ABC):
    """Abstract base class for all group filters.

    Attributes
    ----------
    config
    """

    _config: FilterDict
    _logger: logging.Logger

    _context: zmq.Context | None

    _socket: zmq.Socket | None
    is_socket_connected: bool

    _result_socket: zmq.Socket | None
    is_result_socket_connected: bool

    __aggregation_results: dict[str, Any]

    __line_writer: SimpleLineWriter

    data_len_per_participant: int = 0
    num_participants_in_aggregation: int = 2

    def __init__(self, config: FilterDict, participant_id: str) -> None:
        """Initialize new Group Filter.

        Parameters
        ----------
        config : custom_types.filter.FilterDict
            Configuration for filter.  `config["name"]` must match the filter
            implementation.

        Notes
        -----
        If other filters need to be accessed or the initiation contains an asynchronous
        part, use `complete_setup`. The other filters may not be initialized when
        __init__ is called. However, filters must be ready to be accessed by other
        filters after __init__ (if they are designed to be).
        """
        self._logger = logging.getLogger(f"{config['name']}-GroupFilter-P-{participant_id}")
        self._config = config
        self.participant_id = participant_id

        self._context = None

        self._socket = None
        self.is_socket_connected = False

        self._result_socket = None
        self.is_result_socket_connected = False

        self.__aggregation_results = {}

        self.__line_writer = SimpleLineWriter()

    @property
    def config(self) -> FilterDict:
        """Get Group Filter config."""
        return self._config

    def set_config(self, config: FilterDict) -> None:
        """Update filter config.

        Notes
        -----
        Provide a custom implementation for this function in a subclass in case the
        group filter should react to config changes.
        """
        self._config = config

    def connect_aggregator(self, data_port: int, result_port: int) -> None:
        self._context = zmq.asyncio.Context.instance()

        self._socket = self._context.socket(zmq.PUSH)
        try:
            self._socket.connect(f"ipc://127.0.0.1:{data_port}")
            self.is_socket_connected = True
        except zmq.ZMQError as e:
            self.is_socket_connected = False
            self._logger.error(f"ZMQ Error: {e}")

        self._result_socket = self._context.socket(zmq.SUB)
        self._result_socket.setsockopt_string(
            zmq.SUBSCRIBE, f"{AGGREGRATION_RESULT_ZMQ_TOPIC}-{self.participant_id}"
        )
        try:
            self._result_socket.connect(f"ipc://127.0.0.1:{result_port}")
            self.is_result_socket_connected = True
        except zmq.ZMQError as e:
            self.is_result_socket_connected = False
            self._logger.error(f"ZMQ Error: {e}")

    async def complete_setup(self) -> None:
        """Complete setup, allowing for asynchronous setup and accessing other filters.

        If the initiation / setup of a filter requires anything asynchronous or other
        filters must be accessed, it should be donne in `complete_setup`.
        `complete_setup` is called when all filters have been set up, therefore other
        filters will be available (may not be the case in __init__, depending on the
        position in the filter pipeline).
        """
        return

    async def cleanup(self) -> None:
        """Cleanup, in case filter will no longer be used.

        Called before the filter is deleted.  In case the filter spawned any
        asyncio.Task tasks they should be stopped & awaited in a custom implementation
        overriding this function.
        """
        self.is_socket_connected = False
        self.is_result_socket_connected = False
        self._context.destroy()

    @staticmethod
    def validate_dict(data) -> TypeGuard[FilterDict]:
        return util.check_valid_typeddict_keys(data, FilterDict)

    def __repr__(self) -> str:
        """Get string representation for this group filter."""
        return f"{self.__class__.__name__}(config={self.config})"

    async def process_individual_frame_and_send_data_to_aggregator(
        self, original: VideoFrame | AudioFrame, ndarray: numpy.ndarray, ts: float
    ) -> numpy.ndarray:
        if self.is_socket_connected:
            data = await self.process_individual_frame(original, ndarray)
            if data is not None:
                message = dict()
                message["participant_id"] = self.participant_id
                message["time"] = ts
                message["data"] = data
                message["timestamp"] = perf_counter()

                try:
                    self._socket.send_json(message, flags=zmq.NOBLOCK)

                    # self._logger.debug(
                    #     f"Data sent for {self.participant_id}: {message}"
                    # )
                except Exception as e:
                    self._logger.debug(
                        f"Exception: {e} | Data cannot be sent for {self.participant_id}: {message}"
                    )

            # Get the current aggregation result from the aggreagator
            if self.is_result_socket_connected:
                try:
                    [topic, aggregation_results] = await self._result_socket.recv_multipart(
                        flags=zmq.NOBLOCK
                    )
                    aggregation_results = pickle.loads(aggregation_results)
                    self.__aggregation_results.update(aggregation_results)
                    for comb in self.__aggregation_results.keys():
                        if len(comb) != len(list(aggregation_results.keys())[0]):
                            del self.__aggregation_results[comb]

                    self._logger.debug(
                        f"Aggregation result received for {self.participant_id} with topic {topic.decode()}: {self.__aggregation_results}"
                    )
                except zmq.Again:
                    pass
                except Exception as e:
                    self._logger.debug(
                        f"Exception: {e} | Aggregation result cannot be retrieved for {self.participant_id}"
                    )

            # Print the data and aggregation results on the frame
            lines = [f"Individual data: {round(float(data or 0), 2)}"]
            if self.__aggregation_results:
                lines += ["Aggregation results:"]
                lines += [
                    f"- {'&'.join(sorted(comb))}: {round(float(agg_result or 0), 2)}"
                    for comb, agg_result in sorted(
                        self.__aggregation_results.items(), key=lambda x: x[0]
                    )
                ]
            ndarray = self.__line_writer.write_lines(ndarray, lines)

        return ndarray

    @staticmethod
    @abstractmethod
    def name() -> str:
        """Provide name of the group filter.

        The given name must be unique among all filters.
        The given name is used as the unique ID for communicating the active filters
        between frontend and backend.
        """
        raise NotImplementedError(
            f"{__name__} is missing it's implementation of the static abstract name()" " method."
        )

    @staticmethod
    @abstractmethod
    def type() -> str:
        """Provide the type of the group filter.

        It can be either "TEST" or "SESSION"
        "NONE" type is used for mute filters
        This is used to build the filters_data JSON object
        """
        raise NotImplementedError(
            f"{__name__} is missing it's implementation of the static abstract filter_type()"
            " method."
        )

    @staticmethod
    @abstractmethod
    def channel() -> str:
        """Provide the channel of the filter.

        It can be either "video", "audio" or "both"
        This is used to build the filters_data JSON object
        """
        raise NotImplementedError(
            f"{__name__} is missing it's implementation of the static abstract channel()" " method."
        )

    @staticmethod
    def default_config() -> dict:
        """Provide the default config for the group filter.

        By default, the default config is an empty dictionary, overwrite this in the
        group filter class to provide a custom config in the filters_data JSON object.
        This is used to build the filters_data JSON object
        """
        return {}

    @abstractmethod
    async def process_individual_frame(
        self, original: VideoFrame | AudioFrame, ndarray: numpy.ndarray
    ) -> Any:
        raise NotImplementedError(
            f"{self} is missing it's implementation of the abstract"
            " `process_individual_frame` method."
        )

    @staticmethod
    @abstractmethod
    def align_data(x: list, y: list, base_timeline: list) -> list:
        raise NotImplementedError(
            f"{__name__} is missing it's implementation of the static"
            " abstract `align_data` method."
        )

    @staticmethod
    @abstractmethod
    def aggregate(data: list[list[Any]]) -> Any:
        raise NotImplementedError(
            f"{__name__} is missing it's implementation of the static"
            " abstract `aggregate` method."
        )

    @staticmethod
    @abstractmethod
    def extract_post_process(self, extraction_path: str) -> Any:
        raise NotImplementedError(
            f"{self} is missing it's implementation of the abstract"
            " `process_individual_frame` method."
        )
