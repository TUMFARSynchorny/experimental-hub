import Typography from "@mui/material/Typography";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import VideoCanvas from "../../components/organisms/VideoCanvas/VideoCanvas";
import ConnectionState from "../../networking/ConnectionState";
import { useAppSelector } from "../../redux/hooks";
import { selectCurrentSession } from "../../redux/slices/sessionsListSlice";
import { ParticipantChatTab } from "../../components/molecules/ChatTab/ParticipantChatTab";
import {
  selectChatGptTab,
  selectChatTab,
  selectInstructionsTab
} from "../../redux/slices/tabsSlice";
import { InstructionsTab } from "../../components/molecules/InstructionsTab/InstructionsTab";
import "./MeetingRoom.css";
import { ChatGptTab } from "../../components/molecules/ChatGptTab/ChatGptTab";
import { getParticipantById } from "../../utils/utils";

function MeetingRoom({ localStream, connection, onGetSession, onChat }) {
  const videoElement = useRef(null);
  const [connectionState, setConnectionState] = useState(null);
  const [glassDetected, setGlassDetected] = useState(null);
  const [connectedParticipants, setConnectedParticipants] = useState([]);
  const sessionData = useAppSelector(selectCurrentSession);
  const [participantStream, setParticipantStream] = useState(null);
  const isChatModalActive = useAppSelector(selectChatTab);
  const isInstructionsModalActive = useAppSelector(selectInstructionsTab);
  const isChatGptModalActive = useAppSelector(selectChatGptTab);
  const [searchParams, setSearchParams] = useSearchParams();
  const sessionIdParam = searchParams.get("sessionId");
  const participantIdParam = searchParams.get("participantId");

  useEffect(() => {
    if (connection && connectionState === ConnectionState.CONNECTED) {
      onGetSession(sessionIdParam);
    }
  }, [connection, connectionState, onGetSession, sessionIdParam]);

  const connectedPeersChangeHandler = async (peers) => {
    console.groupCollapsed("%cConnection peer streams change Handler", "color:blue");
    console.groupEnd();
    setConnectedParticipants(peers);
  };

  const handleGetFiltersData = (data) => {
    const glassFilter = data[participantIdParam].video.find(
      (obj) => obj.id === "simple-glasses-detection"
    );
    setGlassDetected(glassFilter.data["Glasses Detected"]);
    connection.sendMessage("GET_FILTERS_DATA", data);
  };

  useEffect(() => {
    connection.on("remoteStreamChange", streamChangeHandler);
    connection.on("connectionStateChange", stateChangeHandler);
    connection.on("connectedPeersChange", connectedPeersChangeHandler);
    connection.api.on("GET_FILTERS_DATA", handleGetFiltersData);
    return () => {
      // Remove event handlers when component is deconstructed
      connection.off("remoteStreamChange", streamChangeHandler);
      connection.off("connectionStateChange", stateChangeHandler);
      connection.off("connectedPeersChange", connectedPeersChangeHandler);
      connection.api.off("GET_FILTERS_DATA", handleGetFiltersData);
    };
  }, [connection]);

  useEffect(() => {
    if (sessionData) {
      const participant = getParticipantById(participantIdParam, sessionData);
      if (participant.local_stream) {
        setParticipantStream(localStream);
      } else {
        setParticipantStream(connection.remoteStream);
      }
    }
  }, [localStream, sessionData]);

  useEffect(() => {
    if (participantStream && videoElement.current) {
      videoElement.current.srcObject = localStream;
    }
  }, [localStream, participantStream]);

  const streamChangeHandler = async () => {
    console.log("%cRemote Stream Change Handler", "color:blue");
  };
  /** Handle `connectionStateChange` event of {@link Connection} */
  const stateChangeHandler = async (state) => {
    setConnectionState(state);
  };

  return (
    <>
      {/* Grid takes up screen space left from the AppToolbar */}
      <div className="flex h-[calc(100vh-84px)]">
        <div className="px-6 py-4 w-3/4 flex flex-col">
          {participantStream ? (
            sessionData && connectedParticipants ? (
              <VideoCanvas
                connectedParticipants={connectedParticipants}
                sessionData={sessionData}
                localStream={participantStream}
                ownParticipantId={participantIdParam}
              />
            ) : (
              <video ref={videoElement} autoPlay playsInline width="100%" height="100%"></video>
            )
          ) : (
            <Typography>
              Unable to access your video. Please check that you have allowed access to your camera
              and microphone.
            </Typography>
          )}
        </div>
        <div className="w-1/4">
          {connectionState !== ConnectionState.CONNECTED && <div>Trying to connect...</div>}
          {connectionState === ConnectionState.CONNECTED && isChatModalActive && (
            <ParticipantChatTab
              onChat={onChat}
              onGetSession={onGetSession}
              currentUser="participant"
              participantId={participantIdParam}
            />
          )}

          {connectionState === ConnectionState.CONNECTED && isInstructionsModalActive && (
            <InstructionsTab displayMode />
          )}

          {connectionState === ConnectionState.CONNECTED && isChatGptModalActive && <ChatGptTab />}
        </div>
      </div>
    </>
  );
}

export default MeetingRoom;
