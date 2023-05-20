import numpy
from av import VideoFrame

from filters.filter import Filter
from filters.simple_line_writer import SimpleLineWriter
from filters.open_face_au.open_face_au_exctractor import OpenFaceAUExtractor
from .open_face_data_parser import OpenFaceDataParser


class OpenFaceAUFilter(Filter):
    """Filter example rotating a video track."""

    frame: int

    file_writer: OpenFaceDataParser
    line_writer: SimpleLineWriter
    au_extractor: OpenFaceAUExtractor

    def __init__(self, config, audio_track_handler, video_track_handler):
        super().__init__(config, audio_track_handler, video_track_handler)
        self.au_extractor = OpenFaceAUExtractor()
        self.line_writer = SimpleLineWriter()
        self.file_writer = OpenFaceDataParser()

        self.data = {"intensity": {"AU06": "-", "AU12": "-"}}
        self.frame = 0

    @staticmethod
    def name(self) -> str:
        return "OPENFACE_AU"

    async def process(
        self, original: VideoFrame, ndarray: numpy.ndarray
    ) -> numpy.ndarray:
        self.frame = self.frame + 1
        exit_code, msg, result = self.au_extractor.extract(ndarray)

        if exit_code == 0:
            self.data = result
            # TODO: use correct frame
            # if a frame is skipped, data corresponds to a frame before current frame, but self.frame does not
            self.file_writer.write(self.frame, self.data)
        else:
            self.file_writer.write(self.frame, {"intensity": "-1"})

        # Put text on image
        au06 = self.data["intensity"]["AU06"]
        au12 = self.data["intensity"]["AU12"]
        ndarray = self.line_writer.write_lines(
            ndarray, [f"AU06: {au06}", f"AU12: {au12}", msg]
        )
        return ndarray
