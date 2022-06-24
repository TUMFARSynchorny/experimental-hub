import { useState } from "react";
import { useSelector } from "react-redux";
import { integerToDateTime } from "../../../utils/utils";
import Button from "../../atoms/Button/Button";
import Heading from "../../atoms/Heading/Heading";
import Label from "../../atoms/Label/Label";
import TextAreaField from "../TextAreaField/TextAreaField";
import "./OverviewTab.css";

function OverviewTab() {
  const [message, setMessage] = useState("");
  const sessionData = useSelector((state) => state.ongoingExperiment.value);

  const onEnterMessage = (newMessage) => {
    setMessage(newMessage);
  };

  return (
    <div className="overviewTabContainer">
      <Heading heading={sessionData.title} />
      <hr className="separatorLine"></hr>
      <div className="sessionInformation">
        <h3>Session Information</h3>
        <div className="sessionDuration">
          <div>
            <Label title={"Time Limit: "} /> {sessionData.time_limit / 60000}
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
          onChange={(newMessage) => onEnterMessage(newMessage)}
        />
        <Button name={"Send"} design={"secondary"} />
      </div>
    </div>
  );
}

export default OverviewTab;
