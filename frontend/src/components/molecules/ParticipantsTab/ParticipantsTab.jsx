import { useAppSelector } from "../../../redux/hooks";
import { selectOngoingExperiment } from "../../../redux/slices/ongoingExperimentSlice";
import { selectSessions } from "../../../redux/slices/sessionsListSlice";
import { getSessionById } from "../../../utils/utils";
import JoinedParticipantCard from "../../organisms/JoinedParticipantCard/JoinedParticipantCard";

function ParticipantsTab({ connectedParticipants, onKickBanParticipant, onMuteParticipant }) {
  const ongoingExperiment = useAppSelector(selectOngoingExperiment);
  const sessionId = ongoingExperiment.sessionId;
  const sessionsList = useAppSelector(selectSessions);
  const sessionData = getSessionById(sessionId, sessionsList);
  return (
    <div className="flex flex-col p-4 border-l-gray-100 border-l-2 w-full items-center h-[calc(100vh-84px)] gap-y-5">
      <div className="text-3xl">Participants</div>
      <div className="w-full flex flex-col overflow-y-auto h-full">
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
    </div>
  );
}

export default ParticipantsTab;
