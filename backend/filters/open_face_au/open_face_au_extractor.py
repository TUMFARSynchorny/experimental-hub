import base64
import json
import logging

import cv2
import numpy
import zmq
from socket import socket
from os.path import join

from hub import BACKEND_DIR
from filters.open_face_au.open_face import OpenFace
from filters.open_face_au.open_face_subprocess import OpenFaceSubProcess
from filters.open_face_au.open_face_dockerized import OpenFaceDockerized


def find_an_available_port(addr: str = "") -> int:
    with socket() as s:
        s.bind((addr, 0))
        return s.getsockname()[1]

# Determine which implementation to use based on config.json open_face_type field
def get_openface_instance(config: str = "", port: int = 0) -> OpenFace:
    env_variable = config  # Default to 'subprocess' if not set

    if env_variable.lower().startswith('docker'):
        # Dockerized version
        return OpenFaceDockerized(port)
    else:
        # Subprocess version
        return OpenFaceSubProcess(port)


class OpenFaceAUExtractor:
    open_face: OpenFace
    context: zmq.Context
    socket: zmq.Socket
    is_extracting: bool
    is_connected: bool
    __openface_port: int
    running_environment: str

    def __init__(self):
        self._logger = logging.getLogger("OpenFaceAuExtractor")
        # find an available port to run openface process
        self.__openface_port = find_an_available_port()
        # read openface running environment, dockerized or subprocess
        config_path = join(BACKEND_DIR, "config.json")
        config = json.load(open(config_path))
        # get openface process instance from the choice
        self.running_environment = config["open_face_type"] if "open_face_type" in config else "subprocess"
        self.open_face = get_openface_instance(self.running_environment, self.__openface_port)# OpenFace(self.__openface_port)
        # initialize zmq instance and socket
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PAIR)

        try:
            # connect to zmq endpoint depending on the running environment
            if self.running_environment == 'dockerized':
                self.socket.connect(f"tcp://127.0.0.1:{self.__openface_port}")
            else:
                self.socket.bind(f"tcp://127.0.0.1:{self.__openface_port}")
            self.is_connected = True
        except zmq.ZMQError as e:
            self.is_connected = False
            self._logger.error(f"ZMQError while connecting port {self.__openface_port}: {e}")

        self.is_extracting = False

    def __del__(self):
        self.is_connected = False
        self.socket.close()
        self.context.destroy()
        del self.open_face

    def extract(
        self, ndarray: numpy.ndarray, roi: dict[str, int] = None
    ) -> tuple[int, str, object]:
        # If ROI is sent from the OpenFace, only send that region
        if roi is not None and roi["width"] > 2:
            ndarray = ndarray[
                roi["y"]: (roi["y"] + roi["height"]),
                roi["x"]: (roi["x"] + roi["width"]),
            ]
        port_msg = f"Port: {self.__openface_port}"

        if not self.is_connected:
            return -1, f"Port {self.__openface_port} is already taken!", None

        result = None
        received = False
        try:
            result = self._get_result()
            received = True
        except zmq.ZMQError:
            if self.is_extracting:
                return 1, port_msg, None

        success = self._start_extraction(ndarray)
        if success:
            try:
                result = self._get_result()
                received = True
            except zmq.ZMQError:
                pass

            if received:
                return 0, port_msg, result
            else:
                return 1, port_msg, result
        else:
            return -2, f"No connection established on {self.__openface_port}", result

    def _start_extraction(self, ndarray: numpy.ndarray) -> bool:
        is_success, image_enc = cv2.imencode(".png", ndarray)

        if not is_success:
            return False

        im_bytes = bytearray(image_enc.tobytes())
        im_64 = base64.b64encode(im_bytes)

        try:
            self.socket.send(im_64, flags=zmq.NOBLOCK)
            self.is_extracting = True
            return True
        except zmq.ZMQError:
            return False

    def _get_result(self) -> object:
        message = self.socket.recv(flags=zmq.NOBLOCK)
        data = json.loads(message)
        self.is_extracting = False
        return data
