import asyncio
import json
from argparse import ArgumentParser
import sys
from typing import Tuple
from aiortc import RTCSessionDescription

from connection.messages import is_valid_rtc_session_description_dict
from filters import FilterDict

from connection.connection_runner import ConnectionRunner


def parse_args() -> (
    Tuple[RTCSessionDescription, str, list[FilterDict], list[FilterDict]]
):
    """Parse command line arguments.

    Raises
    ------
    ValueError
        If the offer is invalid
    """
    parser = ArgumentParser()
    parser.add_argument("-o", "--offer", dest="offer", required=True)
    parser.add_argument(
        "-l", "--log_name_suffix", dest="log_name_suffix", required=True
    )
    parser.add_argument(
        "--audio-filters", dest="audio_filters", required=False, default=[]
    )
    parser.add_argument(
        "--video-filters", dest="video_filters", required=False, default=[]
    )
    parser.add_argument("--record-data", dest="record_data", required=False, default=[])
    args = parser.parse_args()

    # Check and parse offer
    try:
        offer_obj = json.loads(args.offer)
        audio_filters = json.loads(args.audio_filters)
        video_filters = json.loads(args.video_filters)
        record_data = json.loads(args.record_data)
    except (json.JSONDecodeError, TypeError) as e:
        print(
            (
                "Failed to parse command line arguments received in command line"
                f" arguments: {e}"
            ),
            file=sys.stderr,
        )
        raise e

    if not is_valid_rtc_session_description_dict(offer_obj):
        print("Offer parsed from command line arguments is invalid.", file=sys.stderr)
        raise ValueError("Invalid offer")

    offer = RTCSessionDescription(offer_obj["sdp"], offer_obj["type"])

    return (offer, args.log_name_suffix, audio_filters, video_filters, record_data)


async def main() -> None:
    offer, log_name_suffix, audio_filters, video_filters, record_data = parse_args()

    runner = ConnectionRunner()
    await runner.run(offer, log_name_suffix, audio_filters, video_filters, record_data)


if __name__ == "__main__":
    asyncio.run(main())
