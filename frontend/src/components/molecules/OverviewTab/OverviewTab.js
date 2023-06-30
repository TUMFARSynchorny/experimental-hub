import PlayArrowOutlined from "@mui/icons-material/PlayArrowOutlined";
import { useState } from "react";
import { useBackListener } from "../../../hooks/useBackListener";
import EndVerificationModal from "../../../modals/EndVerificationModal/EndVerificationModal";
import StartVerificationModal from "../../../modals/StartVerificationModal/StartVerificationModal";
import { useAppSelector } from "../../../redux/hooks";
import { selectOngoingExperiment } from "../../../redux/slices/ongoingExperimentSlice";
import { selectSessions } from "../../../redux/slices/sessionsListSlice";
import { instructionsList } from "../../../utils/constants";
import { getSessionById, integerToDateTime } from "../../../utils/utils";
import {
  ActionButton,
  ActionIconButton,
  LinkActionButton
} from "../../atoms/Button";
import Heading from "../../atoms/Heading/Heading";
import Label from "../../atoms/Label/Label";
import TextAreaField from "../TextAreaField/TextAreaField";
import "./OverviewTab.css";

function OverviewTab({
  onLeaveExperiment,
  onStartExperiment,
  onEndExperiment
}) {
  const [message, setMessage] = useState("");
  const [startVerificationModal, setStartVerificationModal] = useState(false);
  const [endVerificationModal, setEndVerificationModal] = useState(false);

  const ongoingExperiment = useAppSelector(selectOngoingExperiment);
  const sessionId = ongoingExperiment.sessionId;
  const sessionsList = useAppSelector(selectSessions);
  const sessionData = getSessionById(sessionId, sessionsList);

  useBackListener(() => onLeaveExperiment());

  return (
    <div className="overviewTabContainer">
      <Heading heading={sessionData.title} />
      <hr className="separatorLine"></hr>
      <div className="sessionInformation">
        <div className="sessionDuration">
          <div>
            <Label title={"Instructions"} />
            <ul>
              {
                // getting a common set of instructions for the participant from constants.js
                instructionsList.map((instruction, index) => {
                  return <li key={index}>{instruction}</li>;
                })
              }
            </ul>
          </div>
          <div>
            <Label title={"Starting time: "} />
            {sessionData.start_time > 0
              ? integerToDateTime(sessionData.start_time)
              : "Not started yet"}
          </div>
          <div>
            <Label title={"Ending time: "} />{" "}
            {sessionData.end_time > 0
              ? integerToDateTime(sessionData.start_time)
              : "Not ended yet"}
          </div>
        </div>
        <hr className="separatorLine"></hr>
      </div>
      <div className="sessionInformation">
        <h3>Send Message to all participants</h3>
        <TextAreaField
          placeholder={"Enter your message here"}
          value={message}
          onChange={(newMessage) => setMessage(newMessage)}
        />
        <ActionIconButton
          text="Send"
          variant="outlined"
          color="primary"
          size="medium"
          icon={<PlayArrowOutlined />}
        />
      </div>
      <hr className="separatorLine"></hr>

      <LinkActionButton
        text="LEAVE EXPERIMENT"
        variant="outlined"
        path="/"
        size="large"
        color="primary"
        onClick={() => onLeaveExperiment()}
      />
      {sessionData.start_time === 0 ? (
        <ActionButton
          text="START EXPERIMENT"
          variant="contained"
          color="success"
          size="large"
          onClick={() => {
            setStartVerificationModal(true);
          }}
        />
      ) : (
        <ActionButton
          text="END EXPERIMENT"
          variant="contained"
          color="error"
          size="large"
          onClick={() => {
            setEndVerificationModal(true);
          }}
        />
      )}

      {startVerificationModal && (
        <StartVerificationModal
          setShowModal={setStartVerificationModal}
          onStartExperiment={onStartExperiment}
        />
      )}

      {endVerificationModal && (
        <EndVerificationModal
          setShowModal={setEndVerificationModal}
          onEndExperiment={onEndExperiment}
        />
      )}
    </div>
  );
}

export default OverviewTab;
