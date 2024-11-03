from session.data.participant import ParticipantDict
from session.data.participant.participant_data import ParticipantData
from session.data.position.position_data import PositionData
from session.data.size.size_data import SizeData


def participant_data_factory(participant_dict: ParticipantDict) -> ParticipantData:
    """Create a ParticipantData object based on a ParticipantDict.

    Parameters
    ----------
    participant_dict : custom_types.participant.ParticipantDict
        Participant dictionary with the data for the resulting ParticipantData

    Returns
    -------
    session.data.participant.ParticipantData
        ParticipantData based on the data in `participant_dict`.
    """
    size = participant_dict["size"]
    sizeData = SizeData(size["width"], size["height"])

    pos = participant_dict["position"]
    positionData = PositionData(pos["x"], pos["y"], pos["z"])

    return ParticipantData(
        participant_dict["id"],
        participant_dict["participant_name"],
        participant_dict["banned"],
        sizeData,
        participant_dict["muted_video"],
        participant_dict["muted_audio"],
        participant_dict["local_stream"],
        positionData,
        participant_dict["chat"],
        participant_dict["audio_filters"],
        participant_dict["video_filters"],
        participant_dict["chat_filters"],
        participant_dict["audio_group_filters"],
        participant_dict["video_group_filters"],
        participant_dict["lastMessageSentTime"],
        participant_dict["lastMessageReadTime"],
        participant_dict["view"],
        participant_dict["canvas_id"],
        participant_dict["asymmetric_filters"],
        participant_dict["asymmetric_filters_id"],
    )
