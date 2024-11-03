from __future__ import annotations
import json
import logging
import os
import subprocess

from server import Config
from hub.exceptions import ErrorDictException
from ..post_processing_interface import PostProcessingInterface
from .producer import PostVideoProducer


class VideoPostProcessing(PostProcessingInterface):
    """Executes post-processing experiments' video by running its producer and consumer."""

    _logger: logging.Logger
    _config: Config
    _producer: PostVideoProducer

    def __init__(self):
        """Initialize new VideoPostProcessing."""
        super().__init__()
        self._logger = logging.getLogger("VideoPostProcessing")
        self._config = Config()

    def execute(self):
        """Execute video post-processing."""
        self.run_consumer()
        self._producer = PostVideoProducer(self._config)
        self._producer.publish(self.recording_list)

    def check_existing_process(self) -> dict:
        """Check whether there are FeatureExtraction subprocesses running."""
        proc = subprocess.Popen(["ps", "aux"],
                                stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE)
        proc2 = subprocess.Popen(["grep", "FeatureExtraction"],
                                 stdin=proc.stdout,
                                 stdout=subprocess.PIPE)
        proc3 = subprocess.Popen(["grep", "out_dir"],
                                 stdin=proc2.stdout,
                                 stdout=subprocess.PIPE)
        out = proc3.stdout.readlines()
        count = len(out)
        if count <= 0:
            error_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "errors.json"
            )

            success_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "success.json"
            )
            if os.path.exists(error_path):
                with open(error_path, 'r') as f:
                    data = json.load(f)
                    error_messages = []
                    for err in data:
                        error_messages.append(err['message'])
                    os.remove(error_path)
                    raise ErrorDictException(
                        code=400,
                        type="POST_PROCESSING_FAILED",
                        description=f'Post-processing failed. Error: {error_messages}.'
                    )
            elif os.path.exists(success_path):
                with open(success_path, 'r') as f:
                    data = json.load(f)
                    os.remove(success_path)
                    return {
                        "is_processing": False,
                        "message": data['message']
                    }

            return {
                "is_processing": False,
                "message": ""
            }
        else:
            for line in out:
                self._logger.info(line)
            return {
                "is_processing": True,
                "message": "The OpenFace extraction is still in progress."
            }

    def run_consumer(self) -> subprocess:
        """Run consumer subprocess."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            consumer = subprocess.Popen(
                [
                    "python",
                    os.path.join(
                        current_dir,
                        "consumer.py"
                    ),
                    self._config.host,
                    str(self._config.post_processing['port'])
                ]
            )
            self._logger.info(f"[PID {consumer.pid}]. Run: consumer.py")
        except Exception as error:
            raise Exception("Error running post-processing consumer." +
                            f"Exception: {error}.")
        return consumer
