import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DeleteOutlined from "@mui/icons-material/DeleteOutlined";
import EditOutlined from "@mui/icons-material/EditOutlined";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import PlayArrowOutlined from "@mui/icons-material/PlayArrowOutlined";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardActions from "@mui/material/CardActions";
import CardContent from "@mui/material/CardContent";
import CardHeader from "@mui/material/CardHeader";
import Chip from "@mui/material/Chip";
import Collapse from "@mui/material/Collapse";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { useAppDispatch } from "../../../redux/hooks";
import { copySession, initializeSession } from "../../../redux/slices/openSessionSlice";
import {
  ongoingSessionCardBackgroundColor,
  ongoingSessionCardBorderColor,
  ongoingSessionCardHeaderColor,
  sessionCardBorderColor
} from "../../../styles/styles";
import { initialSnackbar } from "../../../utils/constants";
import { getParticipantInviteLink, integerToDateTime, isFutureSession } from "../../../utils/utils";
import { ActionIconButton } from "../../atoms/Button";
import CustomSnackbar from "../../atoms/CustomSnackbar/CustomSnackbar";
import { setCurrentSession } from "../../../redux/slices/sessionsListSlice";

function SessionPreview({
  selectedSession,
  setSelectedSession,
  onDeleteSession,
  onJoinExperiment,
  onCreateExperiment
}) {
  const dispatch = useAppDispatch();
  const deleteSession = () => {
    const sessionId = selectedSession.id;
    onDeleteSession(sessionId);
    setSelectedSession(null);
  };

  const [allParticipantsShow, setAllParticipantsShow] = useState(false);
  const [expandedParticipant, setExpandedParticipant] = useState("");
  const [snackbar, setSnackbar] = useState(initialSnackbar);
  const experimentOngoing = selectedSession.creation_time > 0 && selectedSession.end_time === 0;

  // handles click on show/hide list of all participants
  const handleParticipantsClick = () => {
    setAllParticipantsShow(!allParticipantsShow);
  };

  // handles click on show/hide of selected participant
  const handleSingleParticipantClick = (participantIndex) => {
    setExpandedParticipant(expandedParticipant === participantIndex ? "" : participantIndex);
  };

  // Method to copy the invite link to clipboard and display a snackbar notification.
  const handleCopyParticipantInviteLink = (participantId, participantName, sessionId) => {
    try {
      const participantInviteLink = getParticipantInviteLink(participantId, sessionId);
      navigator.clipboard.writeText(participantInviteLink);
      setSnackbar({
        open: true,
        text: participantInviteLink
          ? `Copied ${participantName}'s invite link to clipboard`
          : "Unfortunately, nothing got copied!",
        severity: "success"
      });
    } catch (error) {
      // displays error snackbar
      setSnackbar({
        open: true,
        text: "There was an error while copying the invite link.",
        severity: "error"
      });
    }
  };

  const handleCloseParticipantInviteLinkFeedback = () => {
    setSnackbar(initialSnackbar);
  };

  return (
    // Using common colors stored in the styles.js file
    <Card
      sx={{
        backgroundColor: experimentOngoing ? ongoingSessionCardBackgroundColor : "white",
        borderTop: experimentOngoing ? ongoingSessionCardBorderColor : sessionCardBorderColor
      }}
    >
      {experimentOngoing ? (
        <CardHeader
          title={`Experiment Ongoing: ${selectedSession.title}`}
          titleTypographyProps={{
            fontWeight: "bold",
            fontSize: "24px",
            color: ongoingSessionCardHeaderColor
          }}
        />
      ) : (
        <CardHeader
          title={`${selectedSession.title}`}
          titleTypographyProps={{ fontWeight: "bold", fontSize: "24px" }}
        />
      )}
      <CardContent>
        <List>
          <ListItem>
            <ListItemText primary={`Date: ${integerToDateTime(selectedSession.date)}`} />
          </ListItem>
          <ListItemButton onClick={handleParticipantsClick}>
            <ListItemText primary={`Participants (${selectedSession.participants.length})`} />
            {allParticipantsShow ? <ExpandLess /> : <ExpandMore />}
          </ListItemButton>

          {/* Displays a collapsible list of all participants */}
          <Collapse in={allParticipantsShow} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {selectedSession.participants.map((participant, participantIndex) => {
                return (
                  <div key={participantIndex}>
                    <ListItemButton
                      sx={{ pl: 4 }}
                      onClick={() => handleSingleParticipantClick(participantIndex)}
                    >
                      <ListItemText primary={`${participant.participant_name}`} />
                      {expandedParticipant === participantIndex ? <ExpandLess /> : <ExpandMore />}
                    </ListItemButton>

                    {/* Displays a collapsible view of the filters and invite link of selected participant */}
                    <Collapse
                      in={expandedParticipant === participantIndex}
                      timeout="auto"
                      unmountOnExit
                    >
                      <List component="div" disablePadding>
                        <ListItem
                          sx={{
                            pl: 4,
                            display: "flex",
                            justifyContent: "space-between"
                          }}
                        >
                          <Typography variant="overline">Audio Filters : </Typography>
                          {participant.audio_filters.length === 0 && (
                            <Typography>No audio filters applied!</Typography>
                          )}
                          <Box>
                            {participant.audio_filters.map((filter, filterIndex) => {
                              return (
                                <Chip
                                  key={filterIndex}
                                  variant="outlined"
                                  label={filter.name}
                                  size="small"
                                  color="secondary"
                                />
                              );
                            })}
                          </Box>
                        </ListItem>
                        <ListItem
                          sx={{
                            pl: 4,
                            display: "flex",
                            justifyContent: "space-between"
                          }}
                        >
                          <Typography variant="overline">Video Filters : </Typography>
                          {participant.video_filters.length === 0 && (
                            <Typography>No video filters applied!</Typography>
                          )}
                          <Box>
                            {participant.video_filters.map((flter, filterIndex) => {
                              return (
                                <Chip
                                  key={filterIndex}
                                  variant="outlined"
                                  label={flter.name}
                                  size="small"
                                  color="secondary"
                                />
                              );
                            })}
                          </Box>
                        </ListItem>
                        <ListItem
                          sx={{
                            pl: 4,
                            display: "flex",
                            justifyContent: "space-between"
                          }}
                        >
                          <Typography variant="overline">Group Filters : </Typography>
                          {participant.audio_group_filters.length === 0 &&
                            participant.video_group_filters.length === 0 && (
                              <Typography>No group filters applied!</Typography>
                            )}
                          <Box>
                            {participant.video_group_filters.map((filter, filterIndex) => {
                              return (
                                <Chip
                                  key={filterIndex}
                                  variant="outlined"
                                  label={filter.name}
                                  size="small"
                                  color="secondary"
                                />
                              );
                            })}
                            {participant.audio_group_filters.map((filter, filterIndex) => {
                              return (
                                <Chip
                                  key={filterIndex}
                                  variant="outlined"
                                  label={filter.name}
                                  size="small"
                                  color="secondary"
                                />
                              );
                            })}
                          </Box>
                        </ListItem>
                        <ListItem
                          sx={{
                            display: "flex",
                            justifyContent: "flex-end"
                          }}
                        >
                          <ActionIconButton
                            text="INVITE"
                            variant="outlined"
                            color="primary"
                            size="small"
                            onClick={() =>
                              handleCopyParticipantInviteLink(
                                participant.id,
                                participant.participant_name,
                                selectedSession.id
                              )
                            }
                            icon={<ContentCopyIcon />}
                          />
                          {/* Displays success/error notification on copy invite link to clipboard */}
                          <CustomSnackbar
                            open={snackbar.open}
                            text={snackbar.text}
                            severity={snackbar.severity}
                            handleClose={handleCloseParticipantInviteLinkFeedback}
                          />
                        </ListItem>
                      </List>
                    </Collapse>
                  </div>
                );
              })}
            </List>
          </Collapse>
        </List>
        <Typography>{selectedSession.description}</Typography>
      </CardContent>

      {/* Displays list of delete, duplicate, edit and join buttons */}
      <CardActions sx={{ display: "flex", justifyContent: "space-between" }}>
        {(selectedSession.creation_time === 0 || selectedSession.end_time > 0) && (
          <ActionIconButton
            text="DELETE"
            variant="outlined"
            color="error"
            size="medium"
            onClick={() => deleteSession()}
            icon={<DeleteOutlined />}
          />
        )}
        <Box>
          <ActionIconButton
            text="DUPLICATE"
            variant="outlined"
            color="primary"
            size="medium"
            path="/sessionForm"
            onClick={() => dispatch(copySession(selectedSession))}
            icon={<ContentCopyIcon />}
          />
          {!selectedSession.creation_time > 0 &&
            selectedSession.end_time === 0 &&
            isFutureSession(selectedSession) && (
              <>
                <ActionIconButton
                  text="EDIT"
                  variant="outlined"
                  color="primary"
                  size="medium"
                  path="/sessionForm"
                  onClick={() => dispatch(initializeSession(selectedSession))}
                  icon={<EditOutlined />}
                />
                <ActionIconButton
                  text="JOIN"
                  variant="contained"
                  color="primary"
                  size="medium"
                  path="/experimentOverview"
                  onClick={() => {
                    onCreateExperiment(selectedSession.id);
                    dispatch(setCurrentSession(selectedSession));
                  }}
                  icon={<PlayArrowOutlined />}
                />
              </>
            )}
          {selectedSession.creation_time > 0 && selectedSession.end_time === 0 && (
            <ActionIconButton
              text="JOIN"
              variant="contained"
              size="medium"
              path="/experimentOverview"
              onClick={() => onJoinExperiment(selectedSession)}
              icon={<PlayArrowOutlined />}
            />
          )}
        </Box>
      </CardActions>
    </Card>
  );
}

export default SessionPreview;
