import Button from "../../atoms/Button/Button";
import LinkButton from "../../atoms/LinkButton/LinkButton";
import "./SessionPreview.css";

function SessionPreview({ sessionInformation }) {
  return (
    <div className="sessionPreviewContainer">
      <div className="sessionPreviewHeader">
        <h3 className="sessionPreviewTitles">
          Title: {sessionInformation.title}
        </h3>
        <h3 className="sessionPreviewTitles">
          Date: {sessionInformation.date}
        </h3>
        <h3 className="sessionPreviewTitles">
          Time: {sessionInformation.time}
        </h3>
        <h3 className="sessionPreviewTitles">
          TimeLimit: {sessionInformation.timeLimit}
        </h3>
      </div>
      <p className="sessionPreviewInformation">{"Some meta information"}</p>
      <div className="sessionPreviewButtons">
        <LinkButton name={"COPY"} to="/sessionForm" />
        <LinkButton name={"EDIT"} to="/sessionForm" />
        <LinkButton name={"START"} to="/watchingRoom" />
      </div>
    </div>
  );
}

export default SessionPreview;
