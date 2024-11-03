"""Provide GroupFilterHandler for handling group filters."""

import asyncio
from typing import Literal
import logging
from group_filters import GroupFilter
import zmq
import zmq.asyncio
from queue import Queue
from itertools import combinations
from typing import Any
import numpy as np
import pickle
from time import perf_counter, time
from group_filters.group_filter import AGGREGRATION_RESULT_ZMQ_TOPIC


class GroupFilterAggregator(object):
    """Handles audio and video group filters aggregation step."""

    _logger: logging.Logger
    _task: asyncio.Task
    _context: zmq.Context
    _socket: zmq.Socket
    is_socket_connected: bool
    _result_socket: zmq.Socket
    is_result_socket_connected: bool
    _kind: Literal["video", "audio"]
    _group_filter: GroupFilter
    _data: dict[str, Queue[tuple[float, Any]]]

    def __init__(
        self,
        kind: Literal["video", "audio"],
        group_filter: GroupFilter,
        data_port: int,
        result_port: int,
    ) -> None:
        super().__init__()
        self._logger = logging.getLogger(
            f"{group_filter.name()}-GroupFilterAggregator-Port-{data_port}-{result_port}"
        )
        self._kind = kind
        self._group_filter = group_filter
        self._data = {}

        self._context = zmq.asyncio.Context.instance()

        self._socket = self._context.socket(zmq.PULL)
        try:
            self._socket.bind(f"ipc://127.0.0.1:{data_port}")
            self.is_socket_connected = True
        except zmq.ZMQError as e:
            self.is_socket_connected = False
            self._logger.error(f"ZMQ Error: {e}")

        self._result_socket = self._context.socket(zmq.PUB)
        try:
            self._result_socket.bind(f"ipc://127.0.0.1:{result_port}")
            self.is_result_socket_connected = True
        except zmq.ZMQError as e:
            self.is_result_socket_connected = False
            self._logger.error(f"ZMQ Error: {e}")

    def __repr__(self) -> str:
        return f"Group filter aggregator for {self._group_filter.name()}"

    def set_task(self, task: asyncio.Task) -> None:
        self._task = task

    async def cleanup(self) -> None:
        self.is_socket_connected = False
        self.is_result_socket_connected = False
        self.delete_data()
        self._context.destroy()
        self._task.cancel()

    def delete_data(self) -> None:
        self._data = {}

    def add_data(self, participant_id: str, t: float, data: Any) -> None:
        q = self._data.get(
            participant_id, Queue(maxsize=self._group_filter.data_len_per_participant)
        )

        if q.full():
            q.get()
        q.put((t, data))

        self._data[participant_id] = q

        self._logger.debug(
            f"Data added for {participant_id} at {perf_counter()}: ({t}, {data}),"
            + f" # of data: {[(k, v.qsize()) for k, v in self._data.items()]}"
        )

    async def run(self) -> None:
        aggregation_history = {}
        while True:
            if self.is_socket_connected:
                try:
                    message = await self._socket.recv_json()

                    start_time = perf_counter()

                    self._logger.debug(
                        f"Message waited for {start_time - message['timestamp']} seconds"
                    )

                    self.add_data(message["participant_id"], message["time"], message["data"])

                    num_participants_in_aggregation = (
                        len(self._data)
                        if self._group_filter.num_participants_in_aggregation == "all"
                        else self._group_filter.num_participants_in_aggregation
                    )

                    if len(self._data) >= num_participants_in_aggregation:
                        aggregation_result_dict = dict()
                        for c in combinations(self._data.keys(), num_participants_in_aggregation):
                            # Check if all participants have enough data
                            participants_have_enough_data = True
                            if self._group_filter.data_len_per_participant != 0:
                                for pid in c:
                                    if (
                                        self._data[pid].qsize()
                                        != self._group_filter.data_len_per_participant
                                    ):
                                        participants_have_enough_data = False
                                        break

                            if not participants_have_enough_data:
                                continue

                            # Take snapshot from the data queues
                            c_data = {}
                            for pid in c:
                                c_data[pid] = list(self._data[pid].queue)

                            # Check if all participant's data is recently updated
                            participants_data_updated_recently = True
                            latest_aggregated_data = aggregation_history.get(c, None)
                            if latest_aggregated_data is not None:
                                for pid in c:
                                    if np.array_equal(latest_aggregated_data[pid], c_data[pid]):
                                        participants_data_updated_recently = False
                                        break

                            if not participants_data_updated_recently:
                                continue

                            # Align data
                            data, alignment_debug_str = self.align_data(c, c_data)

                            # Skip if the alignment cannot be performed because there is no overlapping time horizon among participants
                            if data is None:
                                continue

                            # Aggregate data
                            aggregation_result = self._group_filter.aggregate(data=data)

                            # Update aggregation history
                            aggregation_history[c] = c_data

                            # Add the aggregation result to the aggregation result messages
                            aggregation_result_dict[c] = aggregation_result

                            end_time = perf_counter()
                            self._logger.debug(
                                alignment_debug_str
                                + "\n"
                                + f"\n\tData aggregation performed for {c}."
                                + f"\n\tTime: {time()}"
                                + f"\n\tRuntime: {end_time - start_time}"
                                + f"\n\tData: {data}"
                                + f"\n\tResult: {aggregation_result}"
                            )
                        # Send the aggregation result to each participant
                        if self.is_result_socket_connected and aggregation_result_dict:
                            for pid in self._data:
                                aggregation_results = dict()
                                for comb, agg_result in aggregation_result_dict.items():
                                    if pid in comb:
                                        i = comb.index(pid)
                                        others = tuple(comb[:i] + comb[i + 1 :])
                                        aggregation_results[others] = agg_result

                                if not aggregation_results:
                                    continue

                                aggregation_result_message_topic = (
                                    f"{AGGREGRATION_RESULT_ZMQ_TOPIC}-{pid}"
                                )

                                try:
                                    self._result_socket.send_multipart(
                                        [
                                            aggregation_result_message_topic.encode(),
                                            pickle.dumps(aggregation_results),
                                        ],
                                        flags=zmq.NOBLOCK,
                                    )
                                    self._logger.debug(
                                        f"Aggregation result sent for {pid} with topic {aggregation_result_message_topic}: {aggregation_results}"
                                    )
                                except Exception as e:
                                    self._logger.debug(
                                        f"Exception: {e} | Aggregation result cannot be sent for {pid}."
                                    )
                except asyncio.CancelledError:
                    # If the task is cancelled, break the loop and stop execution
                    break
                except Exception as e:
                    self._logger.debug(f"Exception: {e} | Data aggregation cannot be performed.")

    def align_data(
        self, participant_ids: tuple[str], data: dict[str, list[tuple[float, Any]]]
    ) -> list[list[Any]] | None:
        start_time = perf_counter()

        if self._group_filter.data_len_per_participant == 1:
            # Align the data based on average time points
            total = 0
            for pid in participant_ids:
                total += data[pid][0][0]

            base_time_horizon = [total / len(participant_ids)]
        else:
            # Calculate the base time horizon as the intersection: max of time horizon starts - min of time horizon ends
            base_time_horizon_start = data[participant_ids[0]][0][0]
            base_time_horizon_end = data[participant_ids[0]][-1][0]
            for pid in participant_ids[1:]:
                th_start = data[pid][0][0]
                if th_start > base_time_horizon_start:
                    base_time_horizon_start = th_start

                th_end = data[pid][-1][0]
                if th_end < base_time_horizon_end:
                    base_time_horizon_end = th_end

            # Return None if the start of base time horizon is greater than its end to prevent aggregation
            if base_time_horizon_start > base_time_horizon_end:
                return None

            base_time_horizon = list(
                np.linspace(
                    base_time_horizon_start,
                    base_time_horizon_end,
                    self._group_filter.data_len_per_participant,
                )
            )

        # Align the data for other participants
        aligned_data = []
        participant_debug_str_list = []
        for pid in participant_ids:
            x, y = map(list, zip(*data[pid]))

            # Align the data
            y_aligned = self._group_filter.align_data(x, y, base_time_horizon)

            # Store the aligned data
            aligned_data.append(y_aligned)

            participant_debug_str_list.append(
                f"\n\tParticipant: {pid}"
                + f"\n\t\tTime Horizon: {x}"
                + f"\n\t\tData: {y}"
                + f"\n\t\tAligned Data: {y_aligned}"
            )

        end_time = perf_counter()
        debug_str = (
            f"\n\tData alignment performed for {participant_ids}."
            + f"\n\tTime: {time()}"
            + f"\n\tRuntime: {end_time - start_time}"
            + f"\n\tBase time horizon: {base_time_horizon}"
            + "".join(participant_debug_str_list)
        )

        return aligned_data, debug_str
