import { integerToDateTime } from "../../../utils/utils";
import Button from "../../atoms/Button/Button";
import LinkButton from "../../atoms/LinkButton/LinkButton";
import "./SessionPreview.css";

import { useDispatch } from "react-redux";
import { initializeSession } from "../../../features/openSession";

function SessionPreview({
  selectedSession,
  setSelectedSession,
  onDeleteSession,
}) {
  const dispatch = useDispatch();

  const deleteSession = () => {
    const sessionId = selectedSession.id;
    onDeleteSession(sessionId);
    setSelectedSession(null);
  };

  const onCopySession = () => {
    let copiedSession = { ...selectedSession };
    copiedSession.id = "";
    dispatch(initializeSession(copiedSession));
  };

  const onEditSession = () => {
    dispatch(initializeSession(selectedSession));
  };

  return (
    <div className="sessionPreviewContainer">
      <div className="sessionPreviewHeader">
        <h3 className="sessionPreviewTitles">Title: {selectedSession.title}</h3>
        <h3 className="sessionPreviewTitles">
          Date: {integerToDateTime(selectedSession.date)}
        </h3>
        <h3 className="sessionPreviewTitles">
          Time Limit: {selectedSession.time_limit / 60000} minutes
        </h3>
      </div>
      <p className="sessionPreviewInformation">{selectedSession.description}</p>
      <>
        <div className="sessionPreviewButtons">
          <Button
            name={"DELETE"}
            design={"negative"}
            onClick={() => deleteSession()}
          />
          <LinkButton
            name={"COPY"}
            to="/sessionForm"
            onClick={() => onCopySession()}
          />
          <LinkButton
            name={"EDIT"}
            to="/sessionForm"
            onClick={() => onEditSession()}
          />
          <LinkButton name={"START"} to="/watchingRoom" />
        </div>
      </>
    </div>
  );
}

export default SessionPreview;
