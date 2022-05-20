import * as React from "react";
import { useRef, useEffect, useState } from "react";

import "./ConnectionTest.css";
import Connection, { ConnectionState } from "../../networking/Connection";


const ConnectionTest = (props: {
  localStream?: MediaStream,
  connection: Connection,
  setConnection: (connection: Connection) => void,
}) => {
  const connection = props.connection;
  const [connectionState, setConnectionState] = useState(connection.state);
  const [peerStreams, setPeerStreams] = useState<MediaStream[]>([]);

  const streamChangeHandler = (_: MediaStream) => {
    console.log("%cRemote Stream Change Handler", "color:blue");
  };
  const stateChangeHandler = (state: ConnectionState) => {
    console.log(`%cConnection state change Handler: ${state}`, "color:blue");
    setConnectionState(state);
  };
  const peerStreamChangeHandler = (streams: MediaStream[]) => {
    console.log(`%cConnection peer streams change Handler: ${streams}`, "color:blue");
    setPeerStreams(streams);
  };

  useEffect(() => {
    connection.remoteStreamChange.on(streamChangeHandler);
    connection.connectionStateChange.on(stateChangeHandler);
    connection.remotePeerStreamsChange.on(peerStreamChangeHandler);
    return () => {
      // Remove event handlers when component is deconstructed
      connection.remoteStreamChange.off(streamChangeHandler);
      connection.connectionStateChange.off(stateChangeHandler);
      connection.remotePeerStreamsChange.off(peerStreamChangeHandler);
    };
  }, [
    connection.connectionStateChange,
    connection.remotePeerStreamsChange,
    connection.remoteStreamChange
  ]);


  return (
    <div className="ConnectionTestPageWrapper">
      <h1>ConnectionTest</h1>
      <p>Connection State:
        <span className={`connectionState ${ConnectionState[connectionState]}`}>{ConnectionState[connectionState]}</span>
      </p>
      <button onClick={() => connection.start(props.localStream)} disabled={connection.state !== ConnectionState.NEW}>Start Connection</button>
      <button onClick={() => connection.stop()} disabled={connection.state !== ConnectionState.CONNECTED}>Stop Connection</button>
      {connection.state === ConnectionState.NEW ? <ReplaceConnection connection={connection} setConnection={props.setConnection} /> : ""}
      <div className="ownStreams">
        <Video title="local stream" srcObject={props.localStream ?? new MediaStream()} />
        <Video title="remote stream" srcObject={connection.remoteStream} />
      </div>
      <p>Peer Streams ({peerStreams.length}):</p>
      {peerStreams.map((stream, i) => <Video title={`Peer stream ${i}`} srcObject={stream} key={i} />)}
      <ApiTests connection={connection} />
    </div>
  );
};

export default ConnectionTest;


function ApiTests(props: { connection: Connection; }): JSX.Element {
  const [responses, setResponses] = useState<{ endpoint: string, data: string; }[]>([]);
  const [highlightedResponse, setHighlightedResponse] = useState(0);
  const [sessionId, setSessionId] = useState(props.connection.sessionId ?? "");
  const [participantId, setParticipantId] = useState(props.connection.participantId ?? "");

  useEffect(() => {
    const saveGenericApiResponse = async (endpoint: string, response_Data: any) => {
      // Add message received by api to responses and reset highlightedResponse  
      setResponses([{ endpoint: endpoint, data: response_Data }, ...responses]);
      setHighlightedResponse(0);
    };

    const handleSessionList = (data: any) => saveGenericApiResponse("SESSION_LIST", data);
    const handleSuccess = (data: any) => saveGenericApiResponse("SUCCESS", data);
    const handleError = (data: any) => saveGenericApiResponse("ERROR", data);
    const handleExperimentEnded = (data: any) => saveGenericApiResponse("EXPERIMENT_ENDED", data);
    const handleExperimentStarted = (data: any) => saveGenericApiResponse("EXPERIMENT_STARTED", data);
    const handleKickNotification = (data: any) => saveGenericApiResponse("KICK_NOTIFICATION", data);

    props.connection.api.on("SESSION_LIST", handleSessionList);
    props.connection.api.on("SUCCESS", handleSuccess);
    props.connection.api.on("ERROR", handleError);
    props.connection.api.on("EXPERIMENT_ENDED", handleExperimentEnded);
    props.connection.api.on("EXPERIMENT_STARTED", handleExperimentStarted);
    props.connection.api.on("KICK_NOTIFICATION", handleKickNotification);

    return () => {
      props.connection.api.off("SESSION_LIST", handleSessionList);
      props.connection.api.off("SUCCESS", handleSuccess);
      props.connection.api.off("ERROR", handleError);
      props.connection.api.off("EXPERIMENT_ENDED", handleExperimentEnded);
      props.connection.api.off("EXPERIMENT_STARTED", handleExperimentStarted);
      props.connection.api.off("KICK_NOTIFICATION", handleKickNotification);
    };
  }, [props.connection.api, responses]);

  return (
    <>
      <div className="requestButtons">
        <button
          onClick={() => props.connection.sendMessage("GET_SESSION_LIST", {})}
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          GET_SESSION_LIST
        </button>
        <button
          onClick={() => props.connection.sendMessage("STOP_EXPERIMENT", {})}
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          STOP_EXPERIMENT
        </button>
        <div className="inputBtnBox">
          <input
            type="text"
            placeholder="Session ID"
            onChange={(e) => setSessionId(e.target.value)}
            value={sessionId}
          />
          <button
            onClick={() => props.connection.sendMessage("CREATE_EXPERIMENT", { session_id: sessionId })}
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            CREATE_EXPERIMENT
          </button>
          <button
            onClick={() => props.connection.sendMessage("JOIN_EXPERIMENT", { session_id: sessionId })}
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            JOIN_EXPERIMENT
          </button>
        </div>
        <div className="inputBtnBox">
          <input
            type="text"
            placeholder="Participant ID"
            onChange={(e) => setParticipantId(e.target.value)}
            value={participantId}
          />
          <button
            onClick={() => props.connection.sendMessage("KICK_PARTICIPANT", { participant_id: participantId, reason: "Testing." })}
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            KICK_PARTICIPANT
          </button>
          <button
            onClick={() => props.connection.sendMessage("BAN_PARTICIPANT", { participant_id: participantId, reason: "Testing." })}
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            BAN_PARTICIPANT
          </button>
        </div>
      </div>
      <div className="basicTabs">
        <span className="tabsTitle">Responses:</span>
        {responses.map((response, index) => {
          return <button key={index}
            onClick={() => setHighlightedResponse(index)}
            className={index === highlightedResponse ? "" : "secondary"}
          >{response.endpoint}
          </button>;
        })}
      </div>
      {responses.length > 0 ? <PrettyJson json={responses[highlightedResponse].data} /> : ""}
    </>
  );
}

function PrettyJson(props: { json: any; }) {
  return (
    <div className="prettyJson">
      <pre>{JSON.stringify(props.json, null, 4)}</pre>
    </div>
  );
}

function ReplaceConnection(props: {
  connection: Connection,
  setConnection: (connection: Connection) => void,
}) {
  const [userType, setUserType] = useState<"participant" | "experimenter">(props.connection.userType);
  const [sessionId, setSessionId] = useState(props.connection.sessionId ?? "");
  const [participantId, setParticipantId] = useState(props.connection.participantId ?? "");

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const connection = new Connection(userType, sessionId, participantId);
    props.setConnection(connection);
    console.log("Updated connection");
  };

  const info = "Replace connection before connecting to change the user type, session id or participant id";

  return (
    <div className="replaceConnectionWrapper">
      <span title={info}>Replace Connection:</span>
      <form onSubmit={handleSubmit} className="replaceConnectionForm">
        <label>Type:&nbsp;&nbsp;
          <select
            defaultValue={props.connection.userType}
            onChange={(e) => setUserType(e.target.value as "participant" | "experimenter")}
          >
            <option value="participant">Participant</option>
            <option value="experimenter">Experimenter</option>
          </select>
        </label>
        {
          userType === "participant" ? <>
            <label>Session ID:&nbsp;&nbsp;
              <input
                type="text"
                onChange={(e) => setSessionId(e.target.value)}
                defaultValue={props.connection.sessionId}
              />
            </label>
            <label>ParticipantID:&nbsp;&nbsp;
              <input
                type="text"
                onChange={(e) => setParticipantId(e.target.value)}
                defaultValue={props.connection.participantId}
              />
            </label>
          </> : ""
        }
        <input type="submit" value="Apply" />
      </form>
    </div>
  );
}

function Video(props: {
  title: string;
  srcObject: MediaStream,
  className?: string;
  style?: React.CSSProperties;
}): JSX.Element {
  const refVideo = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (refVideo.current) {
      refVideo.current.srcObject = props.srcObject;
    }
  }, [props.srcObject]);

  return (
    <div className={"videoWrapper " + props.className ?? ""} style={props.style}>
      <p>{props.title}</p>
      <video ref={refVideo} autoPlay playsInline height={255} width={300}></video>
    </div>
  );
}
