import "./App.css";
import ExperimentRoom from "./pages/ExperimentRoom/ExperimentRoom";
import SessionOverview from "./pages/SessionOverview/SessionOverview";
import PostProcessing from "./pages/PostProcessing/PostProcessing";
import WatchingRoom from "./pages/WatchingRoom/WatchingRoom";
import SessionForm from "./pages/SessionForm/SessionForm";
import Connection from "./networking/Connection";
import ConnectionTest from "./pages/ConnectionTest/ConnectionTest";
import ConnectionState from "./networking/ConnectionState";
import {
  createSession,
  getSessionsList,
  updateSession,
} from "./features/sessionsList";
import { deleteSession } from "./features/sessionsList";

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useEffect, useState } from "react";
import { getLocalStream } from "./utils/utils";
import { useSelector, useDispatch } from "react-redux";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

function App() {
  const [localStream, setLocalStream] = useState(null);
  const [connection, setConnection] = useState(null);
  const [connectionState, setConnectionState] = useState(null);

  const sessionsList = useSelector((state) => state.sessionsList.value);
  const dispatch = useDispatch();

  const streamChangeHandler = async (_) => {
    console.log("%cRemote Stream Change Handler", "color:blue");
  };

  /** Handle `connectionStateChange` event of {@link Connection}. */
  const stateChangeHandler = async (state) => {
    console.log(
      `%cConnection state change Handler: ${ConnectionState[state]}`,
      "color:blue"
    );

    setConnectionState(state);
    if (state === "CONNECTED") {
    }
  };

  // Register Connection event handlers
  useEffect(() => {
    if (!connection) {
      return;
    }

    connection.on("remoteStreamChange", streamChangeHandler);
    connection.on("connectionStateChange", stateChangeHandler);
    return () => {
      connection.off("remoteStreamChange", streamChangeHandler);
      connection.off("connectionStateChange", stateChangeHandler);
    };
  }, [connection]);

  useEffect(() => {
    const asyncStreamHelper = async () => {
      const stream = await getLocalStream();
      if (stream) {
        setLocalStream(stream);
      }
    };

    if (connection?.userType === "participant" && !localStream) {
      asyncStreamHelper();
    }
  }, [localStream, connection]);

  useEffect(() => {
    const userType = "experimenter";
    const newConnection = new Connection(userType, "", "", true);
    setConnection(newConnection);

    newConnection.start();
    return () => {
      newConnection.stop();
    };
  }, [localStream]);

  useEffect(() => {
    if (!connection) {
      return;
    }

    connection.api.on("SESSION_LIST", handleSessionList);
    connection.api.on("DELETED_SESSION", handleDeletedSession);
    connection.api.on("CREATED_SESSION", handleCreatedSession);
    connection.api.on("UPDATED_SESSION", handleUpdatedSession);
    connection.api.on("CREATED_SESSION", handleCreatedSession);
    connection.api.on("SUCCESS", handleSuccess);
    connection.api.on("ERROR", handleError);

    return () => {
      connection.api.off("SESSION_LIST", handleSessionList);
      connection.api.off("DELETED_SESSION", handleDeletedSession);
      connection.api.off("UPDATED_SESSION", handleUpdatedSession);
      connection.api.off("CREATED_SESSION", handleCreatedSession);
      connection.api.off("SUCCESS", handleSuccess);
      connection.api.off("ERROR", handleError);
    };
  }, [connection]);

  useEffect(() => {
    if (!connection || connectionState !== ConnectionState.CONNECTED) {
      return;
    }

    connection.sendMessage("GET_SESSION_LIST", {});
  }, [connection, connectionState]);

  const onDeleteSession = (sessionId) => {
    connection.sendMessage("DELETE_SESSION", {
      session_id: sessionId,
    });
  };

  const onSendSessionToBackend = (session) => {
    connection.sendMessage("SAVE_SESSION", session);
  };

  const handleSessionList = (data) => {
    dispatch(getSessionsList(data));
  };

  const handleDeletedSession = (data) => {
    toast.success("Successfully deleted session with ID " + data);
    dispatch(deleteSession(data));
  };

  const handleUpdatedSession = (data) => {
    toast.success("Successfully updated session" + data.title);
    dispatch(updateSession(data));
  };

  const handleCreatedSession = (data) => {
    toast.success("Successfully created session" + data.title);
    dispatch(createSession(data));
  };

  const handleSuccess = (data) => {
    toast.success("SUCCESS: " + data);
  };

  const handleError = (data) => {
    toast.error("Something went wrong! " + data);
  };

  return (
    <div className="App">
      <ToastContainer />
      {sessionsList ? (
        <Router>
          <Routes>
            <Route
              exact
              path="/"
              element={<SessionOverview onDeleteSession={onDeleteSession} />}
            />
            <Route
              exact
              path="/postProcessingRoom"
              element={<PostProcessing />}
            />
            <Route exact path="/experimentRoom" element={<ExperimentRoom />} />
            <Route exact path="/watchingRoom" element={<WatchingRoom />} />
            <Route
              exact
              path="/sessionForm"
              element={
                <SessionForm onSendSessionToBackend={onSendSessionToBackend} />
              }
            />
            <Route
              exact
              path="/connectionTest"
              element={
                connection ? (
                  <ConnectionTest
                    localStream={localStream}
                    connection={connection}
                    setConnection={setConnection}
                  />
                ) : (
                  "loading"
                )
              }
            />
          </Routes>
        </Router>
      ) : (
        <h1>Loading...</h1>
      )}
    </div>
  );
}

export default App;
