import { useEffect, useState } from "react";

import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import Divider from "@mui/material/Divider";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import styled from "@mui/material/styles/styled";
import { ActionIconButton, ActionButton } from "../../components/atoms/Button";
import SessionCard from "../../components/organisms/SessionCard/SessionCard";
import SessionPreview from "../../components/organisms/SessionPreview/SessionPreview";
import { useAppDispatch, useAppSelector } from "../../redux/hooks";
import { initializeSession } from "../../redux/slices/openSessionSlice";
import { selectSessions } from "../../redux/slices/sessionsListSlice";
import { INITIAL_SESSION_DATA } from "../../utils/constants";
import { getPastAndFutureSessions } from "../../utils/utils";

function SessionOverview({ onDeleteSession, onJoinExperiment, onCreateExperiment }) {
  const dispatch = useAppDispatch();
  const sessionsList = useAppSelector(selectSessions);
  const [past, setPast] = useState([]);
  const [future, setFuture] = useState([]);
  const [selectedSession, setSelectedSession] = useState(future.length !== 0 ? future[0] : null);
  const [showPastSessions, setShowPastSessions] = useState(false);

  // const { past, future } = getPastAndFutureSessions(sessionsList);
  useEffect(() => {
    const { pastSession, futureSession } = getPastAndFutureSessions(sessionsList);
    setPast(pastSession);
    setFuture(futureSession);
    setSelectedSession(futureSession.length !== 0 ? futureSession[0] : null);
  }, [sessionsList]);

  const handleClick = (session) => {
    setSelectedSession(session);
  };

  const onCreateNewSession = () => {
    dispatch(initializeSession(INITIAL_SESSION_DATA));
  };

  const onShowPastSessions = () => {
    setShowPastSessions(!showPastSessions);
  };

  const WelcomeText = styled(Typography)(({ theme }) => ({
    margin: theme.spacing(2, 4, 2, 4), // top, right, bottom, left
    fontStyle: "italic"
  }));

  const Separator = styled(Divider)(() => ({
    borderRightWidth: 5
  }));

  return (
    <>
      <div className="flex flex-col justify-center items-center py-10">
        <div>
          <ActionButton
            text="CREATE NEW EXPERIMENT"
            path="/sessionForm"
            variant="contained"
            color="primary"
            size="large"
            onClick={() => onCreateNewSession()}
          />
        </div>
        <WelcomeText>
          A video conferencing tool for researchers. Create a new experimental template to start
          designing and hosting your next experiment. See the{" "}
          <a href="https://github.com/TUMFARSynchrony/experimental-hub/wiki">
            <u> Wiki </u>
          </a>{" "}
          for more info.
        </WelcomeText>
      </div>
      <Grid container className="flex flex-col justify-center">
        <Grid item sm={7} sx={{ m: 3 }}>
          {selectedSession ? (
            <SessionPreview
              selectedSession={selectedSession}
              setSelectedSession={setSelectedSession}
              onDeleteSession={onDeleteSession}
              onCreateExperiment={onCreateExperiment}
              onJoinExperiment={onJoinExperiment}
            />
          ) : (
            <Typography variant="h6" sx={{ fontWeight: "bold" }}>
              No session selected.
            </Typography>
          )}
        </Grid>
        <Grid item>
          <Separator orientation="vertical" />
        </Grid>
        <Grid item sm={4} sx={{ m: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: "bold" }}>
            Upcoming sessions:
          </Typography>
          {future.length !== 0 ? (
            future.map((session, index) => {
              return (
                <SessionCard
                  title={session.title}
                  key={index}
                  date={session.date}
                  description={session.description}
                  onClick={() => handleClick(session)}
                  ongoing={session.creation_time > 0 && session.end_time === 0}
                  selected={session.id === selectedSession?.id}
                />
              );
            })
          ) : (
            <Typography variant="h6" sx={{ fontWeight: "bold" }}>
              No active sessions found.
            </Typography>
          )}
          <ActionIconButton
            text={showPastSessions ? "Hide past sessions" : "Show past sessions"}
            variant="outlined"
            color="primary"
            size="medium"
            onClick={() => onShowPastSessions()}
            icon={showPastSessions ? <ExpandLess /> : <ExpandMore />}
          />
          {showPastSessions &&
            past.length > 0 &&
            past.map((session, index) => {
              return (
                <SessionCard
                  title={session.title}
                  key={index}
                  date={session.date}
                  description={session.description}
                  onClick={() => handleClick(session)}
                  selected={session.id === selectedSession?.id}
                />
              );
            })}
        </Grid>
      </Grid>
    </>
  );
}

export default SessionOverview;
