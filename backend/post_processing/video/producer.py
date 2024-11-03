from __future__ import annotations
import json
import jsonpickle
import logging
import time
import zmq

from server import Config
from ..post_processing_data import PostProcessingData


class PostVideoProducer():
    """Handles producer for post-processing experiments' video."""

    _logger: logging.Logger
    _config: Config
    _sock: zmq.Socket

    def __init__(self, config: Config):
        """Initialize new PostVideoProducer."""
        super().__init__()
        self._logger = logging.getLogger("PostVideoProducer")
        context = zmq.Context()
        self._sock = context.socket(zmq.PUB)
        self._config = config
        try:
            self._sock.bind(f"tcp://{self._config.host}:{self._config.post_processing['port']}")
            self._logger.info(f"Bound to port: {self._config.post_processing['port']}")
            # Give zmq some time to bind with consumer
            time.sleep(self._config.post_processing['time_sleep'])
        except zmq.ZMQError as e:
            self._logger.error(f"ZMQError: {e}")
            raise Exception(e)

    def publish(self, recording_list: list[PostProcessingData]):
        """Publish the recorded data to consumer."""
        for video in recording_list:
            try:
                videoJSON = jsonpickle.encode(video)
                message = json.dumps(videoJSON, indent=4)
                self._sock.send_string(message)
                self._logger.info(f"Publish: {message}")
            except Exception as error:
                self._logger.error("Error post-processing producer." + 
                                f"Video: {video}." + 
                                f"Exception: {error}")
        # Exit message for consumer
        self._sock.send_string("0")