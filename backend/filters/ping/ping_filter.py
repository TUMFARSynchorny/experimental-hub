import numpy
import cv2  # noqa: F401

from filters.filter import Filter
from filter_api import FilterAPIInterface
from filters.filter_data_dict import FilterDataDict
from filters.filter_dict import FilterDict


class PingFilter(Filter):
    """A simple example filter printing the current API ping on a video Track.
    """

    filter_api: FilterAPIInterface
    counter: int
    ping: int
    period: int
    buffer_length: int

    def __init__(
        self, config: FilterDict, audio_track_handler, video_track_handler
    ) -> None:
        super().__init__(config, audio_track_handler, video_track_handler)

        self.filter_api = video_track_handler.filter_api
        self.counter = 0
        self.ping = 0
        self.period = config["config"]["period"]["value"]
        self.buffer_length = config["config"]["bufferLength"]["value"]

    async def complete_setup(self) -> None:
        await self.filter_api.start_pinging(self.period, self.buffer_length)

    async def cleanup(self) -> None:
        self.filter_api.stop_pinging()

    @staticmethod
    def name() -> str:
        return "PING"

    @staticmethod
    def type() -> str:
        return "SESSION"

    @staticmethod
    def channel() -> str:
        return "video"

    @staticmethod
    def default_config() -> object:
        return {
            "period": {
                "min": 10,
                "max": 60000,
                "step": 1,
                "value": 1000,
                "defaultValue": 1000,
            },
            "bufferLength": {
                "min": 1,
                "max": 300,
                "step": 1,
                "value": 10,
                "defaultValue": 10,
            },
        }

    async def get_filter_data(self) -> None | FilterDataDict:
        return FilterDataDict(
            id=self.id,
            data={"ping": self.ping},
        )

    async def process(self, _, ndarray: numpy.ndarray) -> numpy.ndarray:
        # Fetch current PING
        if not self.counter % 30:
            self.ping = await self.filter_api.get_current_ping()

        # Uncomment to display PING on the video frame
        # height, _, _ = ndarray.shape
        # origin = (10, height - 10)
        # font = cv2.FONT_HERSHEY_SIMPLEX
        # font_size = 1
        # thickness = 3
        # color = (0, 255, 0)
        # text = "{:.0f} ms".format(self.ping)
        # ndarray = cv2.putText(
        #     ndarray, text, origin, font, font_size, color, thickness
        # )

        self.counter += 1

        return ndarray
