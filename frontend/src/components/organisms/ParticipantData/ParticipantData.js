import Button from "../../atoms/Button/Button";
import InputTextField from "../../molecules/InputTextField/InputTextField";
import "./ParticipantData.css";
import Checkbox from "../../molecules/Checkbox/Checkbox";
import Heading from "../../atoms/Heading/Heading";
import Label from "../../atoms/Label/Label";

import { useForm } from "react-hook-form";
import { FaRegTrashAlt } from "react-icons/fa";
import { useDispatch } from "react-redux";
import { deleteParticipant } from "../../../features/openSession";
import { ToastContainer, toast } from "react-toastify";

function ParticipantData({
  onDeleteParticipant,
  onChange,
  index,
  participantData,
  sessionId,
  showParticipantInput,
  setShowParticipantInput,
}) {
  const { register, handleSubmit } = useForm();
  const dispatch = useDispatch();
  const handleChange = (first_name, last_name, muted_audio, muted_video) => {
    onChange(index, {
      first_name,
      last_name,
      muted_audio,
      muted_video,
    });
  };

  const onAddAdditionalInformation = () => {
    setShowParticipantInput(!showParticipantInput);
  };

  const onCloseModalWithoutData = () => {
    setShowParticipantInput(!showParticipantInput);
    onDeleteParticipant();
    toast.warning("Participant deleted since no data was provided.");
  };

  return (
    <div className="participantDataContainer">
      <ToastContainer />
      <InputTextField
        title="Participant Name"
        placeholder={"Enter the information"}
        value={[participantData.first_name, participantData.last_name]
          .filter((str) => str.length > 0)
          .join(" ")}
        readonly={true}
        register={register}
        label={"name"}
        required={false}
      />
      <div className="participantButtons">
        <Button
          name="Enter participant information"
          design={"secondary"}
          onClick={() => onAddAdditionalInformation()}
        />

        <Button
          name={""}
          design={"negative"}
          onClick={() => onDeleteParticipant()}
          icon={<FaRegTrashAlt />}
        />
      </div>

      {showParticipantInput && (
        <div className="additionalParticipantInfoContainer">
          <div className="additionalParticipantInfo">
            <div className="additionalParticipantInfoCard">
              <Heading heading={"General information:"} />

              <InputTextField
                title="First Name"
                value={participantData.first_name}
                placeholder={"Name of participant"}
                onChange={(newFirstName) =>
                  handleChange(
                    newFirstName,
                    participantData.last_name,
                    participantData.muted_audio,
                    participantData.muted_video
                  )
                }
                register={register}
                label={"first_name"}
                required={true}
              />
              <InputTextField
                title="Last Name"
                value={participantData.last_name}
                placeholder={"Name of participant"}
                onChange={(newLastName) =>
                  handleChange(
                    participantData.first_name,
                    newLastName,
                    participantData.muted_audio,
                    participantData.muted_video
                  )
                }
                register={register}
                label={"last_name"}
                required={true}
              />
              <InputTextField
                title="Link"
                value={
                  participantData.id.length > 0
                    ? `https:://experimental-hub/experimentRoom/userId=${participantData.id}&sessionId=${sessionId}`
                    : "Save session to generate link."
                }
                readonly={true}
                register={register}
                label={"link"}
                required={false}
              />
              <div className="participantMuteCheckbox">
                <Checkbox
                  title="Mute Audio"
                  value={participantData.muted_audio}
                  checked={participantData.muted_audio}
                  onChange={() =>
                    handleChange(
                      participantData.first_name,
                      participantData.last_name,
                      !participantData.muted_audio,
                      participantData.muted_video
                    )
                  }
                  register={register}
                  label={"muted_audio"}
                  required={false}
                />
                <Checkbox
                  title="Mute Video"
                  value={participantData.muted_video}
                  checked={participantData.muted_video}
                  onChange={() =>
                    handleChange(
                      participantData.first_name,
                      participantData.last_name,
                      participantData.muted_audio,
                      !participantData.muted_video
                    )
                  }
                  register={register}
                  label={"muted_video"}
                  required={false}
                />
              </div>
              <Heading heading={"Current video position and size:"} />
              <div className="participantVideoSize">
                <div className="participantPosition">
                  <Label title={"x: "} /> {participantData.position.x}
                </div>
                <div className="participantPosition">
                  <Label title={"y: "} /> {participantData.position.y}
                </div>
                <div className="participantPosition">
                  <Label title={"Width: "} /> {participantData.size.width}
                </div>
                <div className="participantPosition">
                  <Label title={"Height: "} /> {participantData.size.height}
                </div>
              </div>
              <Button
                name="Save"
                design={"secondary"}
                onClick={handleSubmit(onAddAdditionalInformation)}
              />
              <Button
                name="Back"
                design={"negative"}
                onClick={onCloseModalWithoutData}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ParticipantData;
