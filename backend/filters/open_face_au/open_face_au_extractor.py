import base64
import json

import cv2
import numpy
import zmq

from filters.open_face_au.open_face import OpenFace
from filters.open_face_au.port_manager import PortManager


class OpenFaceAUExtractor:
    port_manager: PortManager
    open_face: OpenFace
    socket: zmq.Socket
    is_extracting: bool
    is_connected: bool

    def __init__(self):
        self.port_manager = PortManager()

        self.open_face = OpenFace(self.port_manager.port)

        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        try:
            self.socket.bind(f"tcp://127.0.0.1:{self.port_manager.port}")
            self.is_connected = True
        except zmq.ZMQError as e:
            print(f"ZMQError: {e}")

        self.is_extracting = False

    def __del__(self):
        self.socket.close()
        del self.port_manager, self.open_face

    def extract(self, ndarray: numpy.ndarray) -> tuple[int, str, object]:
        port_msg = f"Port: {self.port_manager.port}"

        if not self.is_connected:
            return -1, f"Port {self.port_manager.port} is already taken!", None

        result = None
        received = False
        try:
            result = self._get_result()
            received = True
        except zmq.ZMQError as e:
            if self.is_extracting:
                return 1, port_msg, None

        success = self._start_extraction(ndarray)
        if success:
            try:
                result = self._get_result()
                received = True
            except zmq.ZMQError as e:
                pass

            if received:
                return 0, port_msg, result
            else:
                return 1, port_msg, result
        else:
            return -2, f"No connection established on {self.port_manager.port}", result

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
        except zmq.ZMQError as e:
            return False

    def _get_result(self) -> object:
        message = self.socket.recv(flags=zmq.NOBLOCK)
        self.open_face.flush_result()
        data = json.loads(message)
        self.is_extracting = False
        return data
