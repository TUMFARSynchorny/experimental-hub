import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import { ActionButton } from "../../components/atoms/Button";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useAppSelector } from "../../redux/hooks";
import { selectCurrentSession } from "../../redux/slices/sessionsListSlice";

// This is used to take the consent of the participant before getting access to their microphone and camera.
function Consent() {
  const [checkParticipation, setCheckParticipation] = useState(false);
  const [checkRecording, setCheckRecording] = useState(false);
  const consentTextParticipation =
    "I understand that I may terminate my participation in the study at any time.";
  const consentTextRecording =
    "I accept the recording of my audio and video and am also aware that the data will be kept anonymous and maybe used for research purposes.";
  const [searchParams, setSearchParams] = useSearchParams();
  const sessionId = searchParams.get("sessionId");
  const participantId = searchParams.get("participantId");
  const session = useAppSelector(selectCurrentSession);
  //TODO: dynamic page (experiment name) - find a way to get the information without actually streaming in the session

  return (
    <div className="h-screen flex flex-col mx-8 py-4 items-start text-left gap-y-4 xl:items-center">
      <div className="header py-4 font-bold text-3xl xl:w-1/2">Synchrony Lab - {}</div>
      <hr className="w-screen -mx-8 border-2 border-gray-200" />
      <div className="flex flex-col h-full overflow-y-auto justify-center gap-y-4 xl:w-1/2">
        <div className="font-bold text-lg">Consent Form</div>
        <p className="text-justify">
          DESCRIPTION: You were previously invited to join this study by the person conducting the
          research. The researcher may already informed you about the consent, their study
          description, the risks and benefits, their contact information, and as well as any
          payments you will get for taking part in this study.
          <br />
          DATA COLLECTION: During the study, the hub will record the video conversation which can be
          used for post-processing work and will only be accessed by the researcher and their team.
          <br />
          PARTICIPANT&apos;S RIGHTS: If you have read this form and have decided to participate in
          this project, please understand that although your participation is voluntary, we would
          like your involvement as much as you can afford. That being said, you have the right to
          withdraw your consent or discontinue participation at any time without penalty or loss of
          benefits to which you are otherwise entitled. You have the right to refuse to answer
          particular questions. The results of this research study may be presented at scientific or
          professional meetings or published in scientific journals. Your identity is not disclosed
          unless we directly inform and ask for your permission.
        </p>
        <div className="flex flex-col">
          <FormControlLabel
            control={<Checkbox />}
            className="h-fit"
            label={consentTextParticipation}
            checked={checkParticipation}
            onChange={() => {
              setCheckParticipation(!checkParticipation);
            }}
          />
          <FormControlLabel
            control={<Checkbox />}
            className="h-fit"
            label={consentTextRecording}
            checked={checkRecording}
            onChange={() => {
              setCheckRecording(!checkRecording);
            }}
          />
        </div>
      </div>
      <div className="self-center h-fit">
        <a
          href={`${window.location.origin}/lobby?participantId=${participantId}&sessionId=${sessionId}`}
          className={!checkParticipation || !checkRecording ? "pointer-events-none" : ""}
        >
          <ActionButton
            text="Continue"
            variant="contained"
            disabled={!checkParticipation || !checkRecording}
          />
        </a>
      </div>
    </div>
  );
}

export default Consent;
