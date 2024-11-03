import { useState } from "react";
import JoinedParticipantModal from "../../../modals/JoinedParticipantModal/JoinedParticipantModal";
import KickParticipantModal from "../../../modals/KickParticipantModal/KickParticipantModal";
import { getParticipantById } from "../../../utils/utils";
import { ActionButton } from "../../atoms/Button";
import Label from "../../atoms/Label/Label";
import "./JoinedParticipantCard.css";

function JoinedParticipant({
  participantId,
  sessionData,
  onKickBanParticipant,
  onMuteParticipant
}) {
  const [showModal, setShowModal] = useState(false);
  const [showKickBanReason, setShowKickBanReason] = useState(false);
  const [action, setAction] = useState("");
  const participantData = getParticipantById(participantId, sessionData);

  return (
    <div className="joinedParticipantContainer">
      <div className="participantSummary">
        <Label title={participantData.participant_name} />
        <ActionButton
          text="Info"
          variant="contained"
          color="info"
          size="small"
          onClick={() => setShowModal(!showModal)}
        />
        <ActionButton
          text="Kick"
          variant="contained"
          color="error"
          size="small"
          onClick={() => {
            setShowKickBanReason(true);
            setAction("Kick");
          }}
        />
        <ActionButton
          text="Ban"
          variant="contained"
          color="error"
          size="small"
          onClick={() => {
            setShowKickBanReason(true);
            setAction("Ban");
          }}
        />
      </div>
      {showModal && (
        <JoinedParticipantModal
          participantData={participantData}
          showModal={showModal}
          setShowModal={setShowModal}
          sessionId={sessionData.id}
          onMuteParticipant={onMuteParticipant}
        />
      )}
      {showKickBanReason && (
        <KickParticipantModal
          participantId={participantData.id}
          showModal={showKickBanReason}
          setShowModal={setShowKickBanReason}
          onKickBanParticipant={onKickBanParticipant}
          action={action}
          sessionId={sessionData.id}
        />
      )}
    </div>
  );
}

export default JoinedParticipant;
