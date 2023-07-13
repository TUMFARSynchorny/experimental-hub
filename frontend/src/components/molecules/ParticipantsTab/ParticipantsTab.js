import { useAppSelector } from "../../../redux/hooks";
import { selectOngoingExperiment } from "../../../redux/slices/ongoingExperimentSlice";
import { selectSessions } from "../../../redux/slices/sessionsListSlice";
import { getSessionById } from "../../../utils/utils";
import Heading from "../../atoms/Heading/Heading";
import JoinedParticipantCard from "../../organisms/JoinedParticipantCard/JoinedParticipantCard";
import "./ParticipantsTab.css";

function ParticipantsTab({
  connectedParticipants,
  onKickBanParticipant,
  onMuteParticipant
}) {
  const ongoingExperiment = useAppSelector(selectOngoingExperiment);
  const sessionId = ongoingExperiment.sessionId;
  const sessionsList = useAppSelector(selectSessions);
  const sessionData = getSessionById(sessionId, sessionsList);
  return (
    <>
      <Heading heading={"Joined participants"} />
      <div className="joinedParticipants">
        {connectedParticipants.length > 0
          ? connectedParticipants.map((participant, index) => {
              return (
                <JoinedParticipantCard
                  participantId={participant.summary}
                  key={index}
                  sessionData={sessionData}
                  onKickBanParticipant={onKickBanParticipant}
                  onMuteParticipant={onMuteParticipant}
                />
              );
            })
          : "No participants joined yet."}
      </div>
    </>
  );
}

export default ParticipantsTab;
