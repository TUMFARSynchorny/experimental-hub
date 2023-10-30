import cv2
import numpy
from av import VideoFrame

from filters.filter import Filter
from filters.simple_line_writer import SimpleLineWriter
from filters.open_face_au.open_face_publisher import OpenFacePublisher
from .open_face_data_parser import OpenFaceDataParser


class OpenFaceAUFilter(Filter):
    """OpenFace AU Extraction filter."""

    frame: int
    data: dict
    file_writer: OpenFaceDataParser
    line_writer: SimpleLineWriter
    publisher: OpenFacePublisher

    def __init__(self, config, audio_track_handler, video_track_handler):
        super().__init__(config, audio_track_handler, video_track_handler)
        self.publisher = OpenFacePublisher()
        self.line_writer = SimpleLineWriter()
        self.file_writer = OpenFaceDataParser()

        self.data = {"intensity": {"AU06": "-", "AU12": "-"}}
        self.frame = 0

    def __del__(self):
        del self.file_writer, self.line_writer, self.publisher

    @staticmethod
    def name(self) -> str:
        return "OPENFACE_AU"

    @staticmethod
    def filter_type(self) -> str:
        return "SESSION"

    @staticmethod
    def get_filter_json(self) -> object:
        # For docstring see filters.filter.Filter or hover over function declaration
        name = self.name(self)
        id = name.lower()
        id = id.replace("_", "-")
        return {
            "name": name,
            "id": id,
            "channel": "video",
            "groupFilter": False,
            "config": {},
        }

    async def process(
        self, original: VideoFrame, ndarray: numpy.ndarray
    ) -> numpy.ndarray:
        self.frame = self.frame + 1
        success, image = cv2.imencode(".png", ndarray)
        response = self.publisher.send(image.tostring())

        # if exit_code == 0:
        #     self.data = result
        #     # TODO: use correct frame
        #     # if a frame is skipped, data corresponds to a frame before current frame, but self.frame does not
        #     self.file_writer.write(self.frame, self.data)
        # else:
        #     self.file_writer.write(self.frame, {"intensity": "-1"})

        # # Put text on image
        # au06 = self.data["intensity"]["AU06"]
        # au12 = self.data["intensity"]["AU12"]
        # ndarray = self.line_writer.write_lines(
        #     ndarray, [f"AU06: {au06}", f"AU12: {au12}", msg]
        # )
        return ndarray

    async def cleanup(self) -> None:
        del self
