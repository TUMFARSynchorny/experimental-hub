import DragAndDrop from "../../components/organisms/DragAndDrop/DragAndDrop";
import ParticipantData from "../../components/organisms/ParticipantData/ParticipantData";
import { INITIAL_PARTICIPANT_DATA } from "../../utils/constants";
import {
  checkValidSession,
  filterListByIndex,
  formatDate,
  generateRandomColor,
  getParticipantDimensions,
  getParticipantIdentifiers
} from "../../utils/utils";

import AddIcon from "@mui/icons-material/Add";
import ChevronLeft from "@mui/icons-material/ChevronLeft";
import ChevronRight from "@mui/icons-material/ChevronRight";
import Box from "@mui/material/Box";
import CardContent from "@mui/material/CardContent";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { ActionButton, ActionIconButton } from "../../components/atoms/Button";
import CustomSnackbar from "../../components/atoms/CustomSnackbar/CustomSnackbar";
import { useAppDispatch, useAppSelector } from "../../redux/hooks";
import {
  addParticipant,
  changeParticipant,
  changeValue,
  deleteParticipant,
  selectNumberOfParticipants,
  selectOpenSession
} from "../../redux/slices/openSessionSlice";
import { initialSnackbar } from "../../utils/constants";
import { v4 as uuid } from "uuid";

function SessionForm({ onSendSessionToBackend, onGetFiltersConfig }) {
  const dispatch = useAppDispatch();
  const openSession = useAppSelector(selectOpenSession);
  const [sessionData, setSessionData] = useState(openSession);
  const [title, setTitle] = useState(sessionData.title);
  const [description, setDescription] = useState(sessionData.description);
  const numberOfParticipants = useAppSelector(selectNumberOfParticipants);
  const [xAxis, setXAxis] = useState(0);
  const [yAxis, setYAxis] = useState(0);
  // TO DO: remove the field time_limit from session.json
  const [timeLimit, setTimeLimit] = useState(sessionData.time_limit / 60000);
  // const [numOfParticipants, setNumOfParticipants] = useState();
  const [snackbar, setSnackbar] = useState(initialSnackbar);
  const [showSessionDataForm, setShowSessionDataForm] = useState(true);
  const [participantDimensions, setParticipantDimensions] = useState(
    getParticipantDimensions(sessionData.participants ? sessionData.participants : [])
  );
  const [participantIdentifiers, setParticipantIdentifiers] = useState(
    getParticipantIdentifiers(sessionData.participants ? sessionData.participants : [])
  );

  // It is used as flags to display warning notifications upon entry of incorrect data/not saved in the Participant Modal.
  // It is displayed here instead of in the Participant Modal itself, since upon closing the modal it is no longer
  // available to display the warnings.
  const [snackbarResponse, setSnackbarResponse] = useState({
    newParticipantInputEmpty: false,
    requiredInformationMissing: false,
    participantOriginalEmpty: false,
    newInputEqualsOld: false
  });

  useEffect(() => {
    setSessionData(openSession);
    if (openSession.participants.length === 0) {
      setXAxis(0);
      setYAxis(0);
    }
  }, [openSession]);

  useEffect(() => {
    setParticipantIdentifiers(getParticipantIdentifiers(sessionData.participants));
  }, [sessionData.participants]);

  useEffect(() => {
    if (snackbarResponse.newParticipantInputEmpty) {
      setSnackbar({
        open: true,
        text: "You did not enter any information. Participant will be deleted now.",
        severity: "warning"
      });
      return;
    }

    if (snackbarResponse.requiredInformationMissing) {
      setSnackbar({
        open: true,
        text: "Required information (Participant Name) is missing. Participant will be deleted now.",
        severity: "warning"
      });
      return;
    }

    if (snackbarResponse.participantOriginalEmpty && !snackbarResponse.newInputEqualsOld) {
      setSnackbar({
        open: true,
        text: "You need to save the information first!",
        severity: "warning"
      });
      return;
    }
  }, [snackbarResponse]);

  useEffect(() => {
    onGetFiltersConfig();
  }, []);

  const handleCanvasPlacement = (participantCount) => {
    if (participantCount !== 0 && participantCount % 20 === 0) {
      setXAxis((participantCount / 20) * 250);
      setYAxis(0);
    } else {
      setXAxis(xAxis + 25);
      setYAxis(yAxis + 25);
    }
  };

  const onDeleteParticipant = (index) => {
    dispatch(deleteParticipant(index));
    setParticipantDimensions(filterListByIndex(participantDimensions, index));
  };

  const onAddParticipant = () => {
    const canvasId = uuid();
    const asymmetricFiltersId = uuid();

    dispatch(
      addParticipant({
        ...INITIAL_PARTICIPANT_DATA,
        canvas_id: canvasId,
        asymmetric_filters_id: asymmetricFiltersId,
        position: { x: xAxis, y: yAxis, z: 0 }
      })
    );
    const newParticipantDimensions = [
      ...participantDimensions,
      {
        shapes: {
          x: 0,
          y: 0,
          z: 0,
          fill: generateRandomColor(canvasId)
        },
        groups: {
          x: xAxis,
          y: yAxis,
          z: 0,
          width: 250,
          height: 250
        },
        id: canvasId
      }
    ];
    setParticipantDimensions(newParticipantDimensions);
  };

  const handleParticipantChange = (index, participant) => {
    dispatch(changeParticipant({ participant: participant, index: index }));

    let newParticipantDimensions = [...participantDimensions];
    newParticipantDimensions[index].shapes = {
      ...newParticipantDimensions[index].shapes,
      participant_name: participant.participant_name
    };
    setParticipantDimensions(newParticipantDimensions);
  };

  const handleSessionDataChange = (objKey, newObj) => {
    dispatch(changeValue({ objKey: objKey, objValue: newObj }));
  };

  const handleSessionTitleChange = (payload) => {
    setTitle(payload);
    dispatch(changeValue({ objKey: "title", objValue: payload }));
  };

  const handleSessionDescriptionChange = (payload) => {
    setDescription(payload);
    dispatch(changeValue({ objKey: "description", objValue: payload }));
  };

  const onShowSessionFormModal = () => {
    setShowSessionDataForm(!showSessionDataForm);
  };

  const onSaveSession = () => {
    if (!checkValidSession(sessionData)) {
      setSnackbar({
        open: true,
        text: "Failed to save session since required fields are missing!",
        severity: "error"
      });
      return;
    }
    onSendSessionToBackend(sessionData);
  };

  return (
    <>
      <div className="flex h-[calc(100vh-84px)] flex-row px-4 py-8 items-start">
        {showSessionDataForm && (
          <div className="shadow-lg rounded-md h-full">
            <div className="px-4 flex flex-col h-full">
              <div className="flex justify-start items-center">
                <ChevronLeft sx={{ color: "gray" }} />
                <ActionButton
                  text="Back to Session Overview"
                  variant="text"
                  size="small"
                  path="/"
                />
              </div>
              <CardContent>
                {/* Override text fields' margin and width using MUI classnames */}
                <Typography variant="h6" sx={{ fontWeight: "bold" }}>
                  Session Details
                </Typography>
                <Box
                  component="form"
                  sx={{ "& .MuiTextField-root": { m: 1 } }}
                  noValidate
                  autoComplete="off"
                >
                  <Box sx={{ "& .MuiTextField-root": { width: "38vw" } }}>
                    <TextField
                      label="Title"
                      value={title}
                      size="small"
                      required
                      onChange={(event) => handleSessionTitleChange(event.target.value)}
                    />
                    <TextField
                      label="Description"
                      value={description}
                      size="small"
                      required
                      onChange={(event) => handleSessionDescriptionChange(event.target.value)}
                    />
                  </Box>
                  <Box sx={{ "& .MuiTextField-root": { width: "18.5vw" } }}>
                    <TextField
                      value={sessionData.date ? formatDate(sessionData.date) : ""}
                      type="datetime-local"
                      size="small"
                      required
                      onChange={(event) =>
                        handleSessionDataChange(
                          "date",
                          event.target.value ? new Date(event.target.value).getTime() : 0
                        )
                      }
                    />
                    <TextField
                      label="Number of Participants"
                      value={numberOfParticipants}
                      type="number"
                      size="small"
                      disabled
                    />
                  </Box>
                  <Box sx={{ mt: 1, mb: 1 }}>
                    <FormControlLabel
                      control={<Checkbox />}
                      label="Record Session"
                      checked={sessionData.record}
                      onChange={() => handleSessionDataChange("record", !sessionData.record)}
                    />
                  </Box>
                </Box>

                <div className="flex">
                  <Typography variant="h6" sx={{ my: 1, fontWeight: "bold" }}>
                    Participant List
                  </Typography>
                  <ActionIconButton
                    text="ADD"
                    variant="outlined"
                    color="primary"
                    size="small"
                    onClick={() => onAddParticipant()}
                    icon={<AddIcon />}
                  />
                </div>
                <div className="overflow-y-auto h-[300px] shadow-lg bg-slate-50 pl-4 py-2">
                  {openSession.participants.map((participant, index) => {
                    return (
                      <ParticipantData
                        onDeleteParticipant={() => onDeleteParticipant(index)}
                        key={index}
                        index={index}
                        participantData={participant}
                        sessionId={sessionData.id}
                        handleParticipantChange={handleParticipantChange}
                        setSnackbarResponse={setSnackbarResponse}
                        handleCanvasPlacement={handleCanvasPlacement}
                        participantDimensions={participantDimensions}
                        participantIdentifiers={participantIdentifiers}
                      />
                    );
                  })}
                </div>
              </CardContent>
              <div className="flex justify-center h-full pb-2">
                <div className="self-end">
                  <ActionButton
                    text="SAVE SESSION"
                    variant="contained"
                    color="success"
                    size="medium"
                    onClick={() => onSaveSession()}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
        <div>
          <ActionIconButton
            text=""
            variant="text"
            color="primary"
            size="large"
            onClick={() => onShowSessionFormModal()}
            icon={showSessionDataForm ? <ChevronLeft /> : <ChevronRight />}
          />
        </div>
        <div className="pr-8">
          <DragAndDrop
            participantDimensions={participantDimensions}
            setParticipantDimensions={setParticipantDimensions}
            asymmetricView={false}
          />
        </div>
      </div>
      <CustomSnackbar
        open={snackbar.open}
        text={snackbar.text}
        severity={snackbar.severity}
        handleClose={() => setSnackbar(initialSnackbar)}
      />
    </>
  );
}

export default SessionForm;
