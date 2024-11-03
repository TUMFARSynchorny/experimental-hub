from session.data.participant import ParticipantSummaryDict, ParticipantDict


def find_participant_asymmetric_filter(
        participant_summary: ParticipantSummaryDict | str | None,
        subscriber: ParticipantDict = None
):
    if subscriber is not None:
        return next((f for f in subscriber["asymmetric_filters"] if
                     f["id"] == participant_summary["asymmetric_filters_id"]), None)

    return None
