from __future__ import annotations
from typing import Literal, TYPE_CHECKING, Optional

from filters.filter_utils import get_filter_dict

if TYPE_CHECKING:
    from hub.track_handler import TrackHandler

from filters import FilterDict, Filter, MuteVideoFilter, MuteAudioFilter

from hub.exceptions import ErrorDictException


def create_filter(
    filter_config: FilterDict,
    audio_track_handler: Optional[TrackHandler] = None,
    video_track_handler: Optional[TrackHandler] = None,
) -> Filter:
    """Create a filter based on `type` of `filter_config`.

    Parameters
    ----------
    filter_config : filters.FilterDict
        Filter config used to determine type of filter.  Also passed to new filter.
    audio_track_handler : TrackHandler
        The audio TrackHandler to assign
    video_track_handler : TrackHandler
        The video TrackHandler to assign

    Raises
    ------
    hub.exceptions.ErrorDictException
        If the filter type is unknown.
    """
    filter_name = filter_config["name"]

    filters = get_filter_dict()

    if filter_name not in filters:
        raise ErrorDictException(
            code=404,
            type="UNKNOWN_FILTER_TYPE",
            description=f'Unknown filter type "{filter_name}".',
        )

    return filters[filter_name](filter_config, audio_track_handler, video_track_handler)

def init_mute_filter(
    kind: Literal["audio", "video"],
    audio_track_handler: TrackHandler,
    video_track_handler: TrackHandler,
) -> MuteAudioFilter | MuteVideoFilter:
    """Initialize audio and video mute filter.

    Parameters
    ----------
    kind : Literal["audio", "video"]
        Decides which kind of mute filter is returned.
    audio_track_handler : TrackHandler
        The audio TrackHandler to assign
    video_track_handler : TrackHandler
        The video TrackHandler to assign

    Returns
    -------
    A MuteAudioFilter or MuteVideoFilter, depending on the given "kind".
    """
    if kind == "audio":
        return MuteAudioFilter(
            {
                "name": "MUTE_AUDIO",
                "id": "0",
                "channel": "audio",
                "groupFilter": False,
                "config": {},
            },
            audio_track_handler,
            video_track_handler,
        )
    else:
        return MuteVideoFilter(
            {
                "name": "MUTE_VIDEO",
                "id": "0",
                "channel": "video",
                "groupFilter": False,
                "config": {},
            },
            audio_track_handler,
            video_track_handler,
        )
