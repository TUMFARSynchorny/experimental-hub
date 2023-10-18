import DeleteOutline from "@mui/icons-material/DeleteOutline";
import EditOutlined from "@mui/icons-material/EditOutlined";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import { useState } from "react";
import ParticipantDataModal from "../../../modals/ParticipantDataModal/ParticipantDataModal";
import { ActionIconButton } from "../../atoms/Button";

function ParticipantData({
  onDeleteParticipant,
  participantData,
  sessionId,
  index,
  handleParticipantChange,
  setSnackbarResponse,
  handleCanvasPlacement
}) {
  // I first name and last name of the participant are empty, then we have a newly created participant. The default value is then true.
  // This is the flag used to display participant details in the ParticipantDataModal.
  const [showParticipantInput, setShowParticipantInput] = useState(
    participantData.participant_name === ""
  );

  const onAddAdditionalInformation = () => {
    setShowParticipantInput(!showParticipantInput);
  };

  return (
    <>
      {/* Displays one row for each participant, with name text field, edit and delete button. */}
      <Box sx={{ display: "flex", justifyContent: "flex-start", mb: 1 }}>
        <TextField
          label="Participant Name"
          value={[participantData.participant_name].filter((str) => str.length > 0).join(" ")}
          inputProps={{ readOnly: true }}
          size="small"
          sx={{ mt: "5px" }}
        />
        <ActionIconButton
          text="EDIT"
          variant="outlined"
          color="primary"
          size="medium"
          onClick={() => onAddAdditionalInformation()}
          icon={<EditOutlined />}
        />
        <ActionIconButton
          text="DELETE"
          variant="outlined"
          color="error"
          size="medium"
          onClick={() => onDeleteParticipant()}
          icon={<DeleteOutline />}
        />
      </Box>

      {/* This is the modal to enter/display :
      participant first and last name, 
      invite link (generated only after session is saved - since the participant and session IDs are required to be generated by the backend), 
      video stream screen positions,
      mute audio and video options,
      audio and video filters applied/choose to apply. */}
      <ParticipantDataModal
        originalParticipant={participantData}
        sessionId={sessionId}
        index={index}
        showParticipantInput={showParticipantInput}
        setShowParticipantInput={setShowParticipantInput}
        handleParticipantChange={handleParticipantChange}
        onDeleteParticipant={onDeleteParticipant}
        setSnackbarResponse={setSnackbarResponse}
        handleCanvasPlacement={handleCanvasPlacement}
      />
    </>
  );
}

export default ParticipantData;
