import { useEffect, useRef, useState } from "react";
import { Route, Routes, useNavigate, useSearchParams } from "react-router-dom";
import "./App.css";
import { ActionButton } from "./components/atoms/Button";
import CustomSnackbar from "./components/atoms/CustomSnackbar/CustomSnackbar";
import Connection from "./networking/Connection";
import ConnectionState from "./networking/ConnectionState";
import ConnectionLatencyTest from "./pages/ConnectionLatencyTest/ConnectionLatencyTest";
import ConnectionTest from "./pages/ConnectionTest/ConnectionTest";
import Lobby from "./pages/Lobby/Lobby";
import MeetingRoom from "./pages/MeetingRoom/MeetingRoom";
import PostProcessing from "./pages/PostProcessing/PostProcessing";
import SessionForm from "./pages/SessionForm/SessionForm";
import SessionOverview from "./pages/SessionOverview/SessionOverview";
import ExperimentOverview from "./pages/ExperimentOverview/ExperimentOverview";
import Consent from "./pages/Consent/Consent";
import End from "./pages/End/End";
import PageTemplate from "./components/templates/PageTemplate";
import HeaderActionArea from "./components/atoms/Button/HeaderActionArea";
import { useAppDispatch, useAppSelector } from "./redux/hooks";
import {
  changeExperimentState,
  createExperiment,
  joinExperiment,
  selectOngoingExperiment
} from "./redux/slices/ongoingExperimentSlice";
import { initializeFiltersData, saveSession } from "./redux/slices/openSessionSlice";
import {
  addMessageToCurrentSession,
  addNote,
  createSession,
  deleteSession,
  getSessionsList,
  selectSessions,
  setCurrentSession,
  setExperimentTimes,
  updateFiltersData,
  updateSession
} from "./redux/slices/sessionsListSlice";
import { initialSnackbar } from "./utils/constants";
import { ExperimentTimes, Tabs } from "./utils/enums";
import { getLocalStream, getSessionById } from "./utils/utils";
import { toggleSingleTab } from "./redux/slices/tabsSlice";
import { faComment } from "@fortawesome/free-solid-svg-icons/faComment";
import { faClipboardCheck, faUsers, faClipboardList } from "@fortawesome/free-solid-svg-icons";
import OpenAI from "openai";
import { ErrorBoundary } from "react-error-boundary";
import LoadingScreen from "./components/organisms/LoadingScreen/LoadingScreen";
import { CircularProgress } from "@mui/material";

function App() {
  const [localStream, setLocalStream] = useState(null);
  const [connection, setConnection] = useState(null);
  const [connectionState, setConnectionState] = useState(null);
  const [connectedParticipants, setConnectedParticipants] = useState([]);
  const [recordings, setRecordings] = useState([]);
  const [status, setPostProcessingStatus] = useState(null);
  const [errorPostProc, setPostProcessingError] = useState(null);
  const [successPostProc, setPostProcessingSuccess] = useState(null);
  const [connectionLossTimeOut, setConnectionLossTimeOut] = useState(false);
  const [refreshTimeOut, setRefreshTimeOut] = useState(false);
  let [searchParams, setSearchParams] = useSearchParams();
  const sessionIdParam = searchParams.get("sessionId");
  const participantIdParam = searchParams.get("participantId");
  const experimenterPasswordParam = searchParams.get("experimenterPassword");
  const sessionsList = useAppSelector(selectSessions);
  const ongoingExperiment = useAppSelector(selectOngoingExperiment);
  const sessionsListRef = useRef();
  sessionsListRef.current = sessionsList;
  const ongoingExperimentRef = useRef();
  ongoingExperimentRef.current = ongoingExperiment;
  const [snackbar, setSnackbar] = useState(initialSnackbar);
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const connectedPeersChangeHandler = async (peers) => {
    console.groupCollapsed("%cConnection peer streams change Handler", "color:blue");
    console.groupEnd();
    setConnectedParticipants(peers);
  };

  const streamChangeHandler = async () => {
    console.log("%cRemote Stream Change Handler", "color:blue");
  };

  /** Handle `connectionStateChange` event of {@link Connection} */
  const stateChangeHandler = async (state) => {
    console.log(`%cConnection state change Handler: ${ConnectionState[state]}`, "color:blue");

    setConnectionState(state);
  };

  useEffect(() => {
    //connectionLossTimer
    const connectionLossTimer = setTimeout(() => {
      setConnectionLossTimeOut(true);
    }, 120000);

    //refreshTimer
    const refreshTimer = setTimeout(() => {
      setRefreshTimeOut(true);
    }, 90000);

    return () => {
      clearTimeout(refreshTimer);
      clearTimeout(connectionLossTimer);
    };
  }, []);

  // ChatGPT validity check
  const gptKeyValid = useRef();
  useEffect(() => {
    const openai = new OpenAI({
      apiKey: import.meta.env.VITE_CHAT_GPT_API_KEY,
      dangerouslyAllowBrowser: true
    });

    async function validKey() {
      try {
        await openai.models.list();
        console.log("true in validKey()");
        return true;
      } catch (error) {
        console.log("false in validKey()");
        return false;
      }
    }

    validKey().then((res) => {
      gptKeyValid.current = res;
      console.log(gptKeyValid);
    });
    console.log(gptKeyValid);
  }, []);

  // Register Connection event handlers
  useEffect(() => {
    if (!connection) {
      return;
    }

    connection.on("remoteStreamChange", streamChangeHandler);
    connection.on("connectionStateChange", stateChangeHandler);
    connection.on("connectedPeersChange", connectedPeersChangeHandler);

    connection.api.on("SESSION_LIST", handleSessionList);
    connection.api.on("SESSION", handleSession);
    connection.api.on("DELETED_SESSION", handleDeletedSession);
    connection.api.on("SAVED_SESSION", handleSavedSession);
    connection.api.on("SESSION_CHANGE", handleSessionChange);
    connection.api.on("SUCCESS", handleSuccess);
    connection.api.on("ERROR", handleError);
    connection.api.on("EXPERIMENT_CREATED", handleExperimentCreated);
    connection.api.on("EXPERIMENT_STARTED", handleExperimentStarted);
    connection.api.on("EXPERIMENT_ENDED", handleExperimentEnded);
    connection.api.on("CHAT", handleChatMessages);
    connection.api.on("RECORDING_LIST", handleRecordingList);
    connection.api.on("CHECK_POST_PROCESSING", handleCheckPostProcessing);
    connection.api.on("PING", handlePing);
    connection.api.on("FILTERS_CONFIG", handleFiltersConfig);
    connection.api.on("FILTERS_DATA", handleFiltersData);
    return () => {
      connection.off("remoteStreamChange", streamChangeHandler);
      connection.off("connectionStateChange", stateChangeHandler);
      connection.off("connectedPeersChange", connectedPeersChangeHandler);

      connection.api.off("SESSION_LIST", handleSessionList);
      connection.api.off("SESSION", handleSession);
      connection.api.off("DELETED_SESSION", handleDeletedSession);
      connection.api.off("SAVED_SESSION", handleSavedSession);
      connection.api.off("SESSION_CHANGE", handleSessionChange);
      connection.api.off("SUCCESS", handleSuccess);
      connection.api.off("ERROR", handleError);
      connection.api.off("EXPERIMENT_CREATED", handleExperimentCreated);
      connection.api.off("EXPERIMENT_STARTED", handleExperimentStarted);
      connection.api.off("EXPERIMENT_ENDED", handleExperimentEnded);
      connection.api.off("CHAT", handleChatMessages);
      connection.api.off("RECORDING_LIST", handleRecordingList);
      connection.api.off("CHECK_POST_PROCESSING", handleCheckPostProcessing);
      connection.api.off("PING", handlePing);
      connection.api.off("FILTERS_CONFIG", handleFiltersConfig);
      connection.api.off("FILTERS_DATA", handleFiltersData);
    };
  }, [connection]);

  useEffect(() => {
    const closeConnection = () => {
      connection?.stop();
    };
    const sessionId = sessionIdParam ? sessionIdParam : "";
    const participantId = participantIdParam ? participantIdParam : "";
    let experimenterPassword = experimenterPasswordParam ?? "";
    const userType = sessionId && participantId ? "participant" : "experimenter";

    const pathname = window.location.pathname.toLowerCase();
    const isConnectionTestPage =
      pathname === "/connectiontest" || pathname === "/connectionlatencytest";
    const isConsentOrEndPage = pathname === "/consent" || pathname === "/end";

    // TODO: get experimenter password before creating Connection, e.g. from "login" page
    // The following solution using `prompt` is only a placeholder.
    if (!isConnectionTestPage && userType === "experimenter" && !experimenterPassword) {
      //experimenterPassword = prompt("Please enter experimenter password", "no-password-given");
      experimenterPassword = "no-password-given";
    }

    const asyncStreamHelper = async (connection) => {
      const stream = await getLocalStream();
      if (stream) {
        setLocalStream(stream);
        // Start connection if current page is not connection test page
        if (!isConnectionTestPage) {
          connection.start(stream);
        }
      }
    };

    const newConnection = new Connection(
      userType,
      sessionId,
      participantId,
      experimenterPassword || "no-password-given", // "no-password-given" is a placeholder when experimenterPassword is an empty string
      true
    );

    !isConsentOrEndPage && setConnection(newConnection);
    if (
      userType === "participant" &&
      pathname !== "/connectionlatencytest" &&
      !isConsentOrEndPage
    ) {
      asyncStreamHelper(newConnection);
      return;
    }

    // Start connection if current page is not connection test page
    if (!isConnectionTestPage) {
      newConnection.start();
    }

    window.addEventListener("beforeunload", closeConnection);

    return () => {
      window.removeEventListener("beforeunload", closeConnection);
      closeConnection();
    };
  }, []);

  useEffect(() => {
    if (!connection || connectionState !== ConnectionState.CONNECTED) {
      return;
    }

    connection.sendMessage("GET_SESSION_LIST", {});
  }, [connection, connectionState]);

  const handleSessionList = (data) => {
    dispatch(getSessionsList(data));
  };

  const handleSession = (data) => {
    dispatch(setCurrentSession(data));
  };

  const handleChatMessages = (data) => {
    dispatch(
      addMessageToCurrentSession({
        message: data,
        author: data.author,
        target: data.target
      })
    );
    if (data.author === "experimenter" && data.target === "participants") {
      setSnackbar({
        open: true,
        text: data.message,
        severity: "info",
        autoHideDuration: 10000,
        anchorOrigin: { vertical: "top", horizontal: "center" }
      });
    }
    if (data.target === "experimenter") {
      connection.sendMessage("GET_SESSION", {
        session_id: ongoingExperimentRef.current.sessionId
      });
    }
  };

  const handleDeletedSession = (data) => {
    setSnackbar({
      open: true,
      text: `Successfully deleted session with ID ${data}`,
      severity: "success"
    });
    dispatch(deleteSession(data));
  };

  const handleSavedSession = (data) => {
    // Redirects to session overview page on saving a session
    navigate("/");
    if (!getSessionById(data.id, sessionsListRef.current)) {
      setSnackbar({
        open: true,
        text: `Successfully created session ${data.title}`,
        severity: "success"
      });
      dispatch(createSession(data));
    } else {
      setSnackbar({
        open: true,
        text: `Successfully updated session ${data.title}`,
        severity: "success"
      });
      dispatch(updateSession(data));
    }

    dispatch(saveSession(data));
  };

  const onProcessingComplete = () => {
    setPostProcessingStatus(null);
    setSnackbar({
      open: true,
      text: "Post-processing complete.",
      severity: "info"
    });
  };

  const handleSuccess = (data) => {
    if (data.type == "POST_PROCESSING_VIDEO") {
      setPostProcessingSuccess(data.description);
      setPostProcessingError(null);
      onProcessingComplete();
    } else {
      setSnackbar({
        open: true,
        text: `SUCCESS: ${data.description}`,
        severity: "success"
      });
    }
  };

  const handleError = (data) => {
    if (data.type == "POST_PROCESSING_FAILED") {
      setPostProcessingError(data.description);
      setPostProcessingSuccess(null);
      onProcessingComplete();
    } else {
      setSnackbar({ open: true, text: `${data.description}`, severity: "error" });
    }
  };

  const handleSessionChange = (data) => {
    if (!getSessionById(data.id, sessionsListRef.current)) {
      dispatch(createSession(data));
    } else {
      dispatch(updateSession(data));
    }
  };

  const handleExperimentCreated = (data) => {
    dispatch(
      setExperimentTimes({
        action: ExperimentTimes.CREATION_TIME,
        value: data.creation_time,
        sessionId: data.session_id
      })
    );
  };

  const handleExperimentStarted = (data) => {
    if (window.location.pathname === "/lobby") {
      navigate({
        pathname: "/meetingRoom",
        search: `?participantId=${participantIdParam}&sessionId=${sessionIdParam}`
      });
    }
    dispatch(
      setExperimentTimes({
        action: ExperimentTimes.START_TIME,
        value: data.start_time,
        sessionId: ongoingExperimentRef.current.sessionId
      })
    );
  };

  const handleExperimentEnded = (data) => {
    if (window.location.pathname === "/meetingRoom") {
      navigate({
        pathname: "/end",
        search: `?participantId=${participantIdParam}&sessionId=${sessionIdParam}`
      });
    }
    dispatch(
      setExperimentTimes({
        action: ExperimentTimes.END_TIME,
        value: data.end_time,
        sessionId: ongoingExperimentRef.current.sessionId
      })
    );

    dispatch(
      setExperimentTimes({
        action: ExperimentTimes.START_TIME,
        value: data.start_time,
        sessionId: ongoingExperimentRef.current.sessionId
      })
    );
  };

  const handleRecordingList = (data) => {
    setRecordings(data);
  };

  const handleCheckPostProcessing = (data) => {
    setPostProcessingStatus(data);
  };

  const handlePing = (data) => {
    const timestamp = window.performance.now();

    connection.sendMessage("PONG", {
      handled_time: timestamp,
      ping_data: data
    });
  };

  const handleFiltersConfig = (data) => {
    dispatch(initializeFiltersData(data));
    console.log("Received filter config data:", data);
  };

  const handleFiltersData = (data) => {
    dispatch(updateFiltersData(data));
  };

  /**
   * Get a specific session information
   * Used in participant's view
   * @param sessionId
   */
  const onGetSession = (sessionId) => {
    connection.sendMessage("GET_SESSION", { session_id: sessionId });
  };

  const onCreateExperiment = (sessionId) => {
    connection.sendMessage("CREATE_EXPERIMENT", { session_id: sessionId });
    dispatch(createExperiment(sessionId)); // Initialize ongoingExperiment redux slice
  };

  const onGetFiltersData = (data) => {
    connection.sendMessage("GET_FILTERS_DATA", data);
  };

  const onGetFiltersDataSendToParticipant = (data) => {
    connection.sendMessage("GET_FILTERS_DATA_SEND_TO_PARTICIPANT", data);
  };

  const onDeleteSession = (sessionId) => {
    connection.sendMessage("DELETE_SESSION", {
      session_id: sessionId
    });
  };

  const onSendSessionToBackend = (session) => {
    connection.sendMessage("SAVE_SESSION", session);
  };

  const onKickBanParticipant = (participant, action) => {
    if (action === "Kick") {
      connection.sendMessage("KICK_PARTICIPANT", participant);
    } else {
      connection.sendMessage("BAN_PARTICIPANT", participant);
    }
  };

  const onJoinExperiment = (session) => {
    const sessionId = session.id;
    connection.sendMessage("JOIN_EXPERIMENT", { session_id: sessionId });
    dispatch(joinExperiment(sessionId));
    dispatch(setCurrentSession(session));
  };

  const onAddNote = (note, sessionId) => {
    connection.sendMessage("ADD_NOTE", note);
    dispatch(addNote({ note: note, id: sessionId }));
  };

  const onChat = (messageObj) => {
    // do not send a message if it's empty
    if (messageObj.message && messageObj.message !== "") {
      connection.sendMessage("CHAT", messageObj);
    }
  };

  const onLeaveExperiment = () => {
    connection.sendMessage("LEAVE_EXPERIMENT", {});
  };

  const onMuteParticipant = (muteRequest) => {
    connection.sendMessage("MUTE", muteRequest);
  };

  const onStartExperiment = () => {
    connection.sendMessage("START_EXPERIMENT", {});
    dispatch(changeExperimentState("ONGOING"));
  };

  const onEndExperiment = () => {
    connection.sendMessage("STOP_EXPERIMENT", {});
  };

  const onGetRecordingList = () => {
    connection.sendMessage("GET_RECORDING_LIST", {});
  };

  const onPostProcessingVideo = (sessionId) => {
    connection.sendMessage("POST_PROCESSING_VIDEO", { session_id: sessionId });
  };

  const onCheckPostProcessing = () => {
    connection.sendMessage("CHECK_POST_PROCESSING", {});
  };

  const onApplyFiltersToVideos = (sessionId, filterRequests) => {
    const formattedFilterRequests = filterRequests
      .map(({ filter, videos }) => {
        if (filter.groupFilter) {
          return {
            video_filenames: videos,
            filter_configs: [filter]
          };
        } else {
          // Handle individual filters
          return videos.map((video) => ({
            video_filenames: video,
            filter_configs: [filter]
          }));
        }
      })
      .flat();

    console.log("Sending request:", {
      session_id: sessionId,
      videos: formattedFilterRequests
    });

    connection.sendMessage("APPLY_FILTER_TO_VIDEO", {
      session_id: sessionId,
      videoFilterRequests: formattedFilterRequests
    });
  };

  const onUpdateMessageReadTime = (participantId, lastMessageReadTime) => {
    connection.sendMessage("UPDATE_READ_MESSAGE_TIME", {
      participant_id: participantId,
      lastMessageReadTime: lastMessageReadTime
    });
  };

  const toggleModal = (modal) => {
    dispatch(toggleSingleTab(modal));
  };

  const onGetFiltersConfig = () => {
    if (connection && connection.sendMessage) {
      connection.sendMessage("GET_FILTERS_CONFIG", {});
    } else {
      console.error("Connection not exists");
    }
  };

  return (
    <div className="App">
      {sessionsList ? (
        <Routes>
          <Route
            exact
            path="/"
            element={
              <PageTemplate
                title={"SynthARium"}
                customComponent={
                  connectionState == ConnectionState.CONNECTED ? (
                    <SessionOverview
                      onDeleteSession={onDeleteSession}
                      onCreateExperiment={onCreateExperiment}
                      onJoinExperiment={onJoinExperiment}
                    />
                  ) : (
                    <div className="flex flex-col overflow-y-auto justify-center h-[calc(100vh-84px)]">
                      <LoadingScreen
                        refreshTimeOut={refreshTimeOut}
                        connectionTimeOut={connectionLossTimeOut}
                      />
                    </div>
                  )
                }
                buttonListComponent={
                  <HeaderActionArea
                    buttons={[
                      {
                        onClick: () => navigate("/postProcessingRoom"),
                        label: "Post-Processing Room"
                      }
                    ]}
                  />
                }
              />
            }
          />
          <Route
            exact
            path="/postProcessingRoom"
            element={
              <PageTemplate
                title={"Post-Processing Room"}
                customComponent={
                  connectionState === ConnectionState.CONNECTED ? (
                    <PostProcessing
                      status={status}
                      recordings={recordings}
                      connection={connection}
                      connectionState={connectionState}
                      errorMessage={errorPostProc}
                      successMessage={successPostProc}
                      onPostProcessingVideo={onPostProcessingVideo}
                      onCheckPostProcessing={onCheckPostProcessing}
                      onGetRecordingList={onGetRecordingList}
                      onApplyFiltersToVideos={onApplyFiltersToVideos}
                      onGetFiltersConfig={onGetFiltersConfig}
                      onProcessingComplete={onProcessingComplete}
                    />
                  ) : (
                    <div className="flex flex-col items-center mt-10">
                      <CircularProgress />
                      <h1>Loading...</h1>
                    </div>
                  )
                }
                centerContentOnYAxis={true}
                buttonListComponent={
                  <HeaderActionArea
                    buttons={[
                      {
                        onClick: () => navigate("/"),
                        label: "Back to Session Overview"
                      }
                    ]}
                  />
                }
              />
            }
          />
          <Route exact path="/consent" element={<Consent />} />
          <Route exact path="/end" element={<End />} />
          <Route exact path="/postProcessingRoom" element={<PostProcessing />} />
          <Route
            exact
            path="/lobby"
            element={
              connection ? (
                <PageTemplate
                  title={"Lobby"}
                  buttonListComponent={
                    gptKeyValid.current ? (
                      <HeaderActionArea
                        buttons={[
                          {
                            onClick: () => toggleModal(Tabs.CHAT),
                            icon: faComment,
                            tooltip: "Chat with participants"
                          },
                          {
                            onClick: () => toggleModal(Tabs.INSTRUCTIONS),
                            icon: faClipboardCheck,
                            tooltip: "View instructions"
                          },
                          {
                            onClick: () => toggleModal(Tabs.CHATGPT),
                            externalIcon: true,
                            tooltip: "Chat with GPT"
                          }
                        ]}
                      />
                    ) : (
                      <HeaderActionArea
                        buttons={[
                          {
                            onClick: () => toggleModal(Tabs.CHAT),
                            icon: faComment,
                            tooltip: "Chat with participants"
                          },
                          {
                            onClick: () => toggleModal(Tabs.INSTRUCTIONS),
                            icon: faClipboardCheck,
                            tooltip: "View instructions"
                          }
                        ]}
                      />
                    )
                  }
                  customComponent={
                    <Lobby
                      localStream={localStream}
                      connection={connection}
                      onGetSession={onGetSession}
                      onChat={onChat}
                    />
                  }
                />
              ) : (
                "Loading..."
              )
            }
          />
          <Route
            exact
            path="/meetingRoom"
            element={
              connection ? (
                <PageTemplate
                  title={"Meeting Room"}
                  buttonListComponent={
                    <HeaderActionArea
                      buttons={[
                        {
                          onClick: () => toggleModal(Tabs.CHAT),
                          icon: faComment,
                          tooltip: "Chat with participants"
                        },
                        {
                          onClick: () => toggleModal(Tabs.INSTRUCTIONS),
                          icon: faClipboardCheck,
                          tooltip: "View instructions"
                        },
                        {
                          onClick: () => toggleModal(Tabs.CHATGPT),
                          externalIcon: true,
                          tooltip: "Chat with GPT"
                        }
                      ]}
                    />
                  }
                  customComponent={
                    <MeetingRoom
                      localStream={localStream}
                      connection={connection}
                      onGetSession={onGetSession}
                      onChat={onChat}
                    />
                  }
                />
              ) : (
                "Loading..."
              )
            }
          />
          <Route
            exact
            path="/template"
            element={
              <PageTemplate
                title={"Experimental Hub Template"}
                buttonListComponent={
                  <HeaderActionArea
                    buttons={[
                      {
                        onClick: () => toggleModal(Tabs.CHAT),
                        icon: faComment
                      },
                      {
                        onClick: () => toggleModal(Tabs.INSTRUCTIONS),
                        icon: faClipboardCheck
                      },
                      {
                        onClick: () => toggleModal(Tabs.PARTICIPANTS),
                        icon: faUsers
                      },
                      {
                        onClick: () => toggleModal(Tabs.FILTER_INFORMATION),
                        icon: faClipboardList
                      },
                      {
                        onClick: () => toggleModal(Tabs.CHATGPT),
                        externalIcon: true
                      }
                    ]}
                  />
                }
                customComponent={
                  <ExperimentOverview
                    connectedParticipants={connectedParticipants}
                    onKickBanParticipant={onKickBanParticipant}
                    onAddNote={onAddNote}
                    onChat={onChat}
                    onGetSession={onGetSession}
                    onLeaveExperiment={onLeaveExperiment}
                    onMuteParticipant={onMuteParticipant}
                    onStartExperiment={onStartExperiment}
                    onEndExperiment={onEndExperiment}
                    onGetFiltersData={onGetFiltersData}
                  />
                }
              />
            }
          />
          <Route
            exact
            path="/experimentOverview"
            element={
              <PageTemplate
                title={"Experiment Overview"}
                buttonListComponent={
                  <HeaderActionArea
                    buttons={[
                      {
                        onClick: () => toggleModal(Tabs.CHAT),
                        icon: faComment,
                        tooltip: "Chat with participants"
                      },
                      // {
                      //   onClick: () => toggleModal(Tabs.INSTRUCTIONS),
                      //   icon: faClipboardCheck,
                      // },
                      {
                        onClick: () => toggleModal(Tabs.PARTICIPANTS),
                        icon: faUsers,
                        tooltip: "View participants"
                      },
                      {
                        onClick: () => toggleModal(Tabs.FILTER_INFORMATION),
                        icon: faClipboardList,
                        tooltip: "View filter information"
                      },
                      {
                        onClick: () => toggleModal(Tabs.CHATGPT),
                        externalIcon: true,
                        tooltip: "Chat with GPT"
                      }
                    ]}
                  />
                }
                customComponent={
                  <ExperimentOverview
                    connectedParticipants={connectedParticipants}
                    onKickBanParticipant={onKickBanParticipant}
                    onAddNote={onAddNote}
                    onChat={onChat}
                    onGetSession={onGetSession}
                    onLeaveExperiment={onLeaveExperiment}
                    onMuteParticipant={onMuteParticipant}
                    onStartExperiment={onStartExperiment}
                    onEndExperiment={onEndExperiment}
                    onGetFiltersData={onGetFiltersData}
                    onUpdateMessageReadTime={onUpdateMessageReadTime}
                  />
                }
                centerContentOnYAxis={true}
              />
            }
          />
          <Route
            exact
            path="/sessionForm"
            element={
              <PageTemplate
                title={"Session Form"}
                customComponent={
                  connectionState === ConnectionState.CONNECTED ? (
                    <ErrorBoundary
                      fallback={
                        <div className="flex flex-col items-center">
                          <h2>Something went wrong.</h2>
                          <ActionButton
                            text="Go to Session Overview"
                            path="/"
                            variant="contained"
                            size="large"
                          />
                        </div>
                      }
                    >
                      <SessionForm
                        onSendSessionToBackend={onSendSessionToBackend}
                        onGetFiltersConfig={onGetFiltersConfig}
                      />
                    </ErrorBoundary>
                  ) : (
                    <div className="flex flex-col items-center">
                      <LoadingScreen
                        refreshTimeOut={refreshTimeOut}
                        connectionTimeOut={connectionLossTimeOut}
                      />
                    </div>
                  )
                }
                centerContentOnYAxis={true}
              />
            }
          />
          <Route
            exact
            path="/connectionTest"
            element={
              connection ? (
                <ConnectionTest
                  localStream={localStream}
                  setLocalStream={setLocalStream}
                  connection={connection}
                  setConnection={setConnection}
                />
              ) : (
                "loading"
              )
            }
          />
          <Route
            exact
            path="/connectionLatencyTest"
            element={
              connection ? (
                <ConnectionLatencyTest
                  localStream={localStream}
                  setLocalStream={setLocalStream}
                  connection={connection}
                />
              ) : (
                "loading"
              )
            }
          />
        </Routes>
      ) : (
        <h1>Loading...</h1>
      )}
      <CustomSnackbar
        open={snackbar.open}
        text={snackbar.text}
        severity={snackbar.severity}
        handleClose={() => setSnackbar(initialSnackbar)}
        autoHideDuration={snackbar.autoHideDuration}
        anchorOrigin={snackbar.anchorOrigin}
      />
    </div>
  );
}

export default App;
