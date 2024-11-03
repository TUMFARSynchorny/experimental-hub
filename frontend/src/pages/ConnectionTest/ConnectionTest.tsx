import * as React from "react";
import { useEffect, useRef, useState } from "react";

import Connection from "../../networking/Connection";
import ConnectionState from "../../networking/ConnectionState";
import { ConnectedPeer } from "../../networking/typing";
import { getLocalStream } from "../../utils/utils";
import "./ConnectionTest.css";

/**
 * Test page for testing the {@link Connection} & api.
 */
function ConnectionTest(props: {
  localStream?: MediaStream;
  setLocalStream: (localStream: MediaStream) => void;
  connection: Connection;
  setConnection: (connection: Connection) => void;
}) {
  const { connection } = props;
  const [audioIsMuted, setAudioIsMuted] = useState(
    !props.localStream?.getAudioTracks()[0].enabled ?? false
  );
  const [videoIsMuted, setVideoIsMuted] = useState(
    !props.localStream?.getVideoTracks()[0].enabled ?? false
  );
  const [connectionState, setConnectionState] = useState(connection.state);
  const [connectedPeers, setConnectedPeers] = useState<ConnectedPeer[]>([]);

  /** Handle `remoteStreamChange` event of {@link Connection}. */
  const streamChangeHandler = async () => {
    console.log("%cRemote Stream Change Handler");
  };

  /** Handle `connectionStateChange` event of {@link Connection}. */
  const stateChangeHandler = async (state: ConnectionState) => {
    console.log(`%cConnection state change Handler: ${ConnectionState[state]}`, "color:blue");
    setConnectionState(state);
  };

  /** Handle `connectedPeersChange` event of {@link Connection}. */
  const connectedPeersChangeHandler = async (peers: ConnectedPeer[]) => {
    console.groupCollapsed("%cConnection peer streams change Handler", "color:blue");
    console.log(peers);
    console.groupEnd();
    setConnectedPeers(peers);
  };

  // Register Connection event handlers
  useEffect(() => {
    connection.on("remoteStreamChange", streamChangeHandler);
    connection.on("connectionStateChange", stateChangeHandler);
    connection.on("connectedPeersChange", connectedPeersChangeHandler);
    return () => {
      // Remove event handlers when component is deconstructed
      connection.off("remoteStreamChange", streamChangeHandler);
      connection.off("connectionStateChange", stateChangeHandler);
      connection.off("connectedPeersChange", connectedPeersChangeHandler);
    };
  }, [connection]);

  // Update audioIsMuted and videoIsMuted when localStream changes
  useEffect(() => {
    if (props.localStream) {
      setAudioIsMuted(!props.localStream.getAudioTracks()[0].enabled);
      setVideoIsMuted(!props.localStream.getVideoTracks()[0].enabled);
    }
  }, [props.localStream]);

  /**
   * Mute audio in localstream.
   * @See {@link https://developer.mozilla.org/en-US/docs/Web/API/MediaStreamTrack/enabled}
   */
  const muteAudio = () => {
    if (props.localStream) {
      console.log(`${audioIsMuted ? "Unmute" : "Mute"} Audio`, audioIsMuted);
      props.localStream.getAudioTracks()[0].enabled = audioIsMuted;
      setAudioIsMuted(!audioIsMuted);
    }
  };

  /**
   * Mute video in localstream.
   * @See {@link https://developer.mozilla.org/en-US/docs/Web/API/MediaStreamTrack/enabled}
   */
  const muteVideo = () => {
    if (props.localStream) {
      console.log(`${videoIsMuted ? "Unmute" : "Mute"} Video`, videoIsMuted);
      props.localStream.getVideoTracks()[0].enabled = videoIsMuted;
      setVideoIsMuted(!videoIsMuted);
    }
  };

  /** Get the title displayed in a {@link Video} element for `peer`. */
  const getVideoTitle = (peer: ConnectedPeer, index: number) => {
    if (peer.summary) {
      if (peer.summary instanceof Object) {
        return `${peer.summary.participant_name}`;
      }
      return `UserID: ${peer.summary}`;
    }
    return `Peer stream ${index + 1}`;
  };

  /** Get the title displayed in a {@link Video} element for the remote stream of this client. */
  const getRemoteStreamTitle = () => {
    if (connection.participantSummary) {
      if (connection.participantSummary instanceof Object) {
        return `remote stream (${connection.participantSummary.participant_name})`;
      }
      return `remote stream: ${connection.participantSummary}`;
    }
    return "remote stream";
  };

  return (
    <div className="ConnectionTestPageWrapper">
      <h1>ConnectionTest</h1>
      <p>
        Connection State:
        <span className={`connectionState ${ConnectionState[connectionState]}`}>
          {ConnectionState[connectionState]}
        </span>
      </p>
      <button
        onClick={() => connection.start(props.localStream)}
        disabled={connection.state !== ConnectionState.NEW}
      >
        Start Connection
      </button>
      <button
        onClick={() => connection.stop()}
        disabled={connection.state !== ConnectionState.CONNECTED}
      >
        Stop Connection
      </button>
      {connection.state === ConnectionState.NEW ? (
        <ReplaceConnection
          connection={connection}
          setConnection={props.setConnection}
          localStream={props.localStream}
          setLocalStream={props.setLocalStream}
        />
      ) : (
        ""
      )}
      <div className="ownStreams">
        <Video
          title="local stream"
          srcObject={props.localStream ?? new MediaStream()}
          ignoreAudio
        />
        <Video title={getRemoteStreamTitle()} srcObject={connection.remoteStream} ignoreAudio />
      </div>
      {props.localStream ? (
        <>
          <button onClick={muteAudio}>{audioIsMuted ? "Unmute" : "Mute"} localStream Audio</button>
          <button onClick={muteVideo}>{videoIsMuted ? "Unmute" : "Mute"} localStream Video</button>
        </>
      ) : (
        ""
      )}
      <button onClick={() => console.log(connection)}>Log Connection</button>
      <p>
        <b>Peer Connections</b> ({connectedPeers.length}):
      </p>
      <div className="peerStreams">
        {connectedPeers.map((peer, i) => (
          <Video title={getVideoTitle(peer, i)} srcObject={peer.stream} key={i} />
        ))}
      </div>
      <ApiTests connection={connection} />
    </div>
  );
}

export default ConnectionTest;

/**
 * Component to send test requests to the backend API and display responses.
 */
function ApiTests(props: { connection: Connection }): JSX.Element {
  const [responses, setResponses] = useState<{ endpoint: string; data: string }[]>([]);
  const [highlightedResponse, setHighlightedResponse] = useState(0);
  const [sessionId, setSessionId] = useState(props.connection.sessionId ?? "");
  const [participantId, setParticipantId] = useState(props.connection.participantId ?? "");
  const [mutedVideo, setMutedVideo] = useState(false);
  const [mutedAudio, setMutedAudio] = useState(false);
  const [videoFilename, setVideoFilename] = useState("");

  useEffect(() => {
    /**
     * Save and display a messages from the backend
     * @param endpoint endpoint to which `messageData` was send. Used as a title for this response.
     * @param messageData data that should be displayed.
     */
    const saveGenericApiResponse = async (endpoint: string, messageData: any) => {
      setResponses([{ endpoint, data: messageData }, ...responses]);
      setHighlightedResponse(0);
    };

    // Message listeners to messages from the backend.
    const handleTest = (data: any) => saveGenericApiResponse("TEST", data);
    const handleSessionChange = (data: any) => saveGenericApiResponse("SESSION_CHANGE", data);
    const handleSessionList = (data: any) => saveGenericApiResponse("SESSION_LIST", data);
    const handleSuccess = (data: any) => saveGenericApiResponse("SUCCESS", data);
    const handleError = (data: any) => saveGenericApiResponse("ERROR", data);
    const handleExperimentCreated = (data: any) =>
      saveGenericApiResponse("EXPERIMENT_CREATED", data);
    const handleExperimentEnded = (data: any) => saveGenericApiResponse("EXPERIMENT_ENDED", data);
    const handleExperimentStarted = (data: any) =>
      saveGenericApiResponse("EXPERIMENT_STARTED", data);
    const handleKickNotification = (data: any) => saveGenericApiResponse("KICK_NOTIFICATION", data);
    const handleRecordingList = (data: any) => saveGenericApiResponse("RECORDING_LIST", data);
    const handlePong = async (data: any) => {
      saveGenericApiResponse("PONG", data);
      if ("time" in data.ping_data) {
        const rtt = new Date().getTime() - data.ping_data.time;
        console.log("Ping RTT:", rtt, "ms");
      }
    };
    const handleFiltersConfig = (data: any) => saveGenericApiResponse("FILTERS_CONFIG", data);
    const handleGetFiltersData = (data: any) => saveGenericApiResponse("GET_FILTERS_DATA", data);
    const handleGetFiltersDataSendToParticipant = (data: any) =>
      saveGenericApiResponse("GET_FILTERS_DATA_SEND_TO_PARTICIPANT", data);
    const handleFiltersData = (data: any) => saveGenericApiResponse("FILTERS_DATA", data);

    // Add listeners to connection
    props.connection.api.on("TEST", handleTest);
    props.connection.api.on("SESSION_CHANGE", handleSessionChange);
    props.connection.api.on("SESSION_LIST", handleSessionList);
    props.connection.api.on("SUCCESS", handleSuccess);
    props.connection.api.on("ERROR", handleError);
    props.connection.api.on("EXPERIMENT_CREATED", handleExperimentCreated);
    props.connection.api.on("EXPERIMENT_ENDED", handleExperimentEnded);
    props.connection.api.on("EXPERIMENT_STARTED", handleExperimentStarted);
    props.connection.api.on("KICK_NOTIFICATION", handleKickNotification);
    props.connection.api.on("PONG", handlePong);
    props.connection.api.on("RECORDING_LIST", handleRecordingList);
    props.connection.api.on("FILTERS_CONFIG", handleFiltersConfig);
    props.connection.api.on("GET_FILTERS_DATA", handleGetFiltersData);
    props.connection.api.on(
      "GET_FILTERS_DATA_SEND_TO_PARTICIPANT",
      handleGetFiltersDataSendToParticipant
    );
    props.connection.api.on("FILTERS_DATA", handleFiltersData);

    return () => {
      // Remove listeners from connection
      props.connection.api.off("TEST", handleTest);
      props.connection.api.off("SESSION_CHANGE", handleSessionChange);
      props.connection.api.off("SESSION_LIST", handleSessionList);
      props.connection.api.off("SUCCESS", handleSuccess);
      props.connection.api.off("ERROR", handleError);
      props.connection.api.off("EXPERIMENT_CREATED", handleExperimentCreated);
      props.connection.api.off("EXPERIMENT_ENDED", handleExperimentEnded);
      props.connection.api.off("EXPERIMENT_STARTED", handleExperimentStarted);
      props.connection.api.off("KICK_NOTIFICATION", handleKickNotification);
      props.connection.api.off("PONG", handlePong);
      props.connection.api.off("RECORDING_LIST", handleRecordingList);
      props.connection.api.off("FILTERS_CONFIG", handleFiltersConfig);
      props.connection.api.off("GET_FILTERS_DATA", handleGetFiltersData);
      props.connection.api.off(
        "GET_FILTERS_DATA_SEND_TO_PARTICIPANT",
        handleGetFiltersDataSendToParticipant
      );
      props.connection.api.off("FILTERS_DATA", handleFiltersData);
    };
  }, [props.connection.api, responses]);

  return (
    <>
      {props.connection.userType === "participant" ? (
        <p className="apiWarning">
          <b>Note:</b> API should only work for experimenters
        </p>
      ) : (
        <p className="apiSubsectionHeader">API Testing:</p>
      )}
      <div className="requestButtons">
        <button
          onClick={() => props.connection.sendMessage("GET_SESSION_LIST", {})}
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          GET_SESSION_LIST
        </button>
        <button
          onClick={() => props.connection.sendMessage("GET_FILTERS_CONFIG", {})}
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          GET_FILTERS_CONFIG
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("GET_FILTERS_DATA", {
              filter_id: "simple-glasses-detection",
              filter_channel: "video",
              filter_name: "SIMPLE_GLASSES_DETECTION"
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          GET_FILTERS_DATA
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("GET_FILTERS_DATA_SEND_TO_PARTICIPANT", {
              participant_id: "all",
              filter_id: "simple-glasses-detection",
              filter_channel: "video",
              filter_name: "SIMPLE_GLASSES_DETECTION"
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          GET_FILTERS_DATA_SEND_TO_PARTICIPANT
        </button>
        <button
          onClick={() => props.connection.sendMessage("START_EXPERIMENT", {})}
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          START_EXPERIMENT
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
            placeholder="bbbef1d7d0"
            onChange={(e) => setSessionId(e.target.value)}
            value="bbbef1d7d0"
          />
          <button
            onClick={() =>
              props.connection.sendMessage("CREATE_EXPERIMENT", {
                session_id: "bbbef1d7d0"
              })
            }
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            CREATE_EXPERIMENT
          </button>
          <button
            onClick={() =>
              props.connection.sendMessage("JOIN_EXPERIMENT", {
                session_id: sessionId
              })
            }
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            JOIN_EXPERIMENT
          </button>
        </div>
        <button
          onClick={() => props.connection.sendMessage("LEAVE_EXPERIMENT", {})}
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          LEAVE_EXPERIMENT
        </button>
        <div className="inputBtnBox">
          <input
            type="text"
            placeholder="Participant ID"
            onChange={(e) => setParticipantId(e.target.value)}
            value={participantId}
          />
          <button
            onClick={() =>
              props.connection.sendMessage("KICK_PARTICIPANT", {
                participant_id: participantId,
                reason: "Testing."
              })
            }
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            KICK_PARTICIPANT
          </button>
          <button
            onClick={() =>
              props.connection.sendMessage("BAN_PARTICIPANT", {
                participant_id: participantId,
                reason: "Testing."
              })
            }
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            BAN_PARTICIPANT
          </button>
        </div>
        <div className="inputBtnBox">
          <input
            type="text"
            placeholder="Participant ID"
            onChange={(e) => setParticipantId(e.target.value)}
            value={participantId}
          />
          <label>
            Mute Audio
            <input
              type="checkbox"
              onChange={(e) => setMutedAudio(e.target.checked)}
              checked={mutedAudio}
            />
          </label>
          <label>
            Mute Video
            <input
              type="checkbox"
              onChange={(e) => setMutedVideo(e.target.checked)}
              checked={mutedVideo}
            />
          </label>
          <button
            onClick={() =>
              props.connection.sendMessage("MUTE", {
                participant_id: participantId,
                mute_video: mutedVideo,
                mute_audio: mutedAudio
              })
            }
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            MUTE
          </button>
        </div>
        <button
          onClick={() => props.connection.sendMessage("PING", { time: new Date().getTime() })}
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          PING
        </button>
      </div>
      <SetFilterPresets connection={props.connection} />
      <p className="apiSubsectionHeader">Post-processing:</p>
      <div className="requestButtons">
        <button
          onClick={() => props.connection.sendMessage("GET_RECORDING_LIST", {})}
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          GET_RECORDING_LIST
        </button>
        <div className="inputBtnBox">
          <input
            type="text"
            placeholder="Session ID"
            onChange={(e) => setSessionId(e.target.value)}
            value={sessionId}
          />
          <button
            onClick={() =>
              props.connection.sendMessage("POST_PROCESSING_VIDEO", {
                session_id: sessionId
              })
            }
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            POST_PROCESSING_VIDEO
          </button>
          <button
            onClick={() => props.connection.sendMessage("CHECK_POST_PROCESSING", {})}
            disabled={props.connection.state !== ConnectionState.CONNECTED}
          >
            CHECK_POST_PROCESSING
          </button>
        </div>
      </div>
      <div className="basicTabs">
        <span className="tabsTitle">Responses:</span>
        {responses.map((response, index) => {
          return (
            <button
              key={index}
              onClick={() => setHighlightedResponse(index)}
              className={index === highlightedResponse ? "" : "secondary"}
            >
              {response.endpoint}
            </button>
          );
        })}
      </div>
      {responses.length > 0 ? <PrettyJson json={responses[highlightedResponse].data} /> : ""}
    </>
  );
}

function SetFilterPresets(props: { connection: Connection }): JSX.Element {
  return (
    <>
      <p className="apiSubsectionHeader">Filter Presets:</p>
      <div className="requestButtons">
        <button
          onClick={() => {
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: []
            });
            props.connection.sendMessage("SET_GROUP_FILTERS", {
              audio_group_filters: [],
              video_group_filters: []
            });
          }}
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          None
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: [
                {
                  name: "FILTER_API_TEST",
                  id: "test",
                  channel: "both",
                  groupFilter: false,
                  config: {}
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          Filter API Test
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: [
                {
                  name: "EDGE_OUTLINE",
                  id: "edge",
                  channel: "video",
                  groupFilter: false,
                  config: {}
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          Edge Outline
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: [
                {
                  name: "ROTATION",
                  id: "rotation",
                  channel: "video",
                  groupFilter: false,
                  config: {
                    direction: {
                      defaultValue: ["clockwise", "anti-clockwise"],
                      value: "clockwise"
                    },
                    angle: {
                      min: 1,
                      max: 180,
                      step: 1,
                      value: 45,
                      defaultValue: 45
                    }
                  }
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          Rotation
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: [
                {
                  name: "EDGE_OUTLINE",
                  id: "edge",
                  channel: "both",
                  groupFilter: false,
                  config: {}
                },
                {
                  name: "ROTATION",
                  id: "rotation",
                  channel: "video",
                  groupFilter: false,
                  config: {
                    direction: {
                      defaultValue: ["clockwise", "anti-clockwise"],
                      value: "clockwise"
                    },
                    angle: {
                      min: 1,
                      max: 180,
                      step: 1,
                      value: 45,
                      defaultValue: 45
                    }
                  }
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          Edge Outline + Rotation
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: [
                {
                  name: "ROTATION",
                  id: "rotation",
                  channel: "video",
                  groupFilter: false,
                  config: {
                    direction: {
                      defaultValue: ["clockwise", "anti-clockwise"],
                      value: "clockwise"
                    },
                    angle: {
                      min: 1,
                      max: 180,
                      step: 1,
                      value: 45,
                      defaultValue: 45
                    }
                  }
                },
                {
                  name: "EDGE_OUTLINE",
                  id: "edge",
                  channel: "both",
                  groupFilter: false,
                  config: {}
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          Rotation + Edge Outline
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: [
                {
                  name: "OPENFACE_AU",
                  id: "zmq",
                  channel: "both",
                  groupFilter: false,
                  config: {}
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          OPENFACE AU
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: [
                {
                  name: "PING",
                  id: "ping-v",
                  channel: "both",
                  groupFilter: false,
                  config: {
                    period: {
                      min: 10,
                      max: 60000,
                      step: 1,
                      value: 1000,
                      defaultValue: 1000
                    },
                    bufferLength: {
                      min: 1,
                      max: 300,
                      step: 1,
                      value: 10,
                      defaultValue: 10
                    }
                  }
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          PING
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: [
                {
                  name: "DELAY",
                  id: "delay-v",
                  channel: "both",
                  groupFilter: false,
                  config: {
                    size: {
                      min: 0,
                      max: 120,
                      step: 1,
                      value: 60,
                      defaultValue: 60
                    }
                  }
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          60 Frame Video Delay
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [
                {
                  name: "DELAY",
                  id: "delay-a",
                  channel: "both",
                  groupFilter: false,
                  config: {
                    size: {
                      min: 0,
                      max: 120,
                      step: 1,
                      value: 60,
                      defaultValue: 60
                    }
                  }
                }
              ],
              video_filters: []
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          60 Frame Audio Delay
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [
                {
                  name: "DELAY",
                  id: "delay-a",
                  channel: "both",
                  groupFilter: false,
                  config: {
                    size: {
                      min: 0,
                      max: 120,
                      step: 1,
                      value: 60,
                      defaultValue: 60
                    }
                  }
                }
              ],
              video_filters: [
                {
                  name: "DELAY",
                  id: "delay-v",
                  channel: "both",
                  groupFilter: false,
                  config: {
                    size: {
                      min: 0,
                      max: 120,
                      step: 1,
                      value: 60,
                      defaultValue: 60
                    }
                  }
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          60 Frame audio + video Delay
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              video_filters: [],
              audio_filters: [
                {
                  name: "AUDIO_SPEAKING_TIME",
                  id: "audio-speaking-time",
                  channel: "both",
                  groupFilter: false,
                  config: {}
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          Speaking Time
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [
                {
                  name: "AUDIO_SPEAKING_TIME",
                  id: "audio-speaking-time",
                  channel: "both",
                  groupFilter: false,
                  config: {}
                }
              ],
              video_filters: [
                {
                  name: "DISPLAY_SPEAKING_TIME",
                  id: "display-speaking-time",
                  channel: "video",
                  groupFilter: false,
                  config: {
                    filterId: {
                      defaultValue: ["audio-speaking-time"],
                      value: "audio-speaking-time"
                    }
                  }
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          Display Speaking Time
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_FILTERS", {
              participant_id: "all",
              audio_filters: [],
              video_filters: [
                {
                  name: "SIMPLE_GLASSES_DETECTION",
                  id: "simple-glasses-detection",
                  channel: "video",
                  groupFilter: false,
                  config: {}
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          Simple Glasses Detection
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_GROUP_FILTERS", {
              audio_group_filters: [],
              video_group_filters: [
                {
                  name: "TEMPLATE_GF",
                  id: "template_gf",
                  channel: "video",
                  groupFilter: true,
                  config: {}
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          TEMPLATE GF
        </button>
        <button
          onClick={() =>
            props.connection.sendMessage("SET_GROUP_FILTERS", {
              audio_group_filters: [],
              video_group_filters: [
                {
                  name: "SYNC_SCORE_GF",
                  id: "sync_score_gf",
                  channel: "video",
                  groupFilter: true,
                  config: {}
                }
              ]
            })
          }
          disabled={props.connection.state !== ConnectionState.CONNECTED}
        >
          SYNC SCORE GF
        </button>
      </div>
    </>
  );
}

/**
 * Component to display an readable, indented version of `json`.
 */
function PrettyJson(props: { json: any }) {
  return (
    <div className="prettyJson">
      <pre>{JSON.stringify(props.json, null, 4)}</pre>
    </div>
  );
}

/**
 * Component with inputs to replace the current {@link Connection} with a new one.
 * Used to change session-, participant-ids or user type.
 *
 * Do not use after the connection has been started.
 */
function ReplaceConnection(props: {
  connection: Connection;
  setConnection: (connection: Connection) => void;
  localStream: MediaStream;
  setLocalStream: (localStream: MediaStream) => void;
}) {
  const [userType, setUserType] = useState<"participant" | "experimenter">(
    props.connection.userType
  );
  const [sessionId, setSessionId] = useState(props.connection.sessionId ?? "");
  const [participantId, setParticipantId] = useState(props.connection.participantId ?? "");
  const [experimenterPassword, setExperimenterPassword] = useState(
    props.connection.experimenterPassword ?? ""
  );

  const updateConnection = async (
    userType: "participant" | "experimenter",
    sessionId: string,
    participantId: string,
    experimenterPassword: string
  ) => {
    if (userType === "participant") {
      if (sessionId === "") sessionId = "placeholderId";
      if (participantId === "") participantId = "placeholderId";
      if (experimenterPassword === "") experimenterPassword = "placeholderId";
      // request local stream if it does not exist.
      if (!props.localStream) {
        const stream = await getLocalStream();
        if (stream) props.setLocalStream(stream);
      }
    }
    console.log(
      `%c[ReplaceConnection] Replaced connection with new parameters: ${userType}, ${sessionId}, ${participantId}`,
      "color:darkgreen"
    );
    const connection = new Connection(
      userType,
      sessionId,
      participantId,
      experimenterPassword,
      props.connection.logging
    );
    props.setConnection(connection);
  };

  const handleUserType = (e: React.ChangeEvent<HTMLSelectElement>) => {
    e.preventDefault();
    const newUserType = e.target.value as "participant" | "experimenter";
    setUserType(newUserType);
    updateConnection(newUserType, sessionId, participantId, experimenterPassword);
  };

  const handleSessionId = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    setSessionId(e.target.value);
    updateConnection(userType, e.target.value, participantId, experimenterPassword);
  };

  const handleParticipantId = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    setParticipantId(e.target.value);
    updateConnection(userType, sessionId, e.target.value, experimenterPassword);
  };

  const handleExperimenterPassword = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    setExperimenterPassword(e.target.value);
    updateConnection(userType, sessionId, participantId, e.target.value);
  };

  const info =
    "Replace connection before connecting to change the user type, session id or participant id";

  return (
    <div className="replaceConnectionWrapper">
      <span title={info}>Replace Connection:</span>
      <form className="replaceConnectionForm">
        <label>
          Type:&nbsp;&nbsp;
          <select defaultValue={props.connection.userType} onChange={handleUserType}>
            <option value="participant">Participant</option>
            <option value="experimenter">Experimenter</option>
          </select>
        </label>
        {userType === "participant" ? (
          <>
            <label>
              Session ID:&nbsp;&nbsp;
              <input
                type="text"
                onChange={handleSessionId}
                placeholder="bbbef1d7d0"
                defaultValue={sessionId}
              />
            </label>
            <label>
              ParticipantID:&nbsp;&nbsp;
              <input type="text" onChange={handleParticipantId} defaultValue={participantId} />
            </label>
          </>
        ) : (
          <label>
            Experimenter Password:&nbsp;&nbsp;
            <input
              type="text"
              onChange={handleExperimenterPassword}
              defaultValue={experimenterPassword}
            />
          </label>
        )}
      </form>
    </div>
  );
}

/**
 * Component to display a video with a title.
 * @param props.title title that is displayed above the video
 * @param props.srcObject video and audio source
 * @param props.ignoreAudio if true, audio tracks in `srcObject` will be ignored.
 */
export function Video(props: {
  title: string;
  srcObject: MediaStream;
  ignoreAudio?: boolean;
}): JSX.Element {
  const refVideo = useRef<HTMLVideoElement>(null);
  const [info, setInfo] = useState("");

  // Set source object for video tag
  useEffect(() => {
    const setSrcObj = (srcObj: MediaStream) => {
      if (refVideo.current && srcObj.active) {
        if (props.ignoreAudio) {
          refVideo.current.srcObject = new MediaStream(srcObj.getVideoTracks());
        } else {
          refVideo.current.srcObject = srcObj;
        }
      }
    };

    setSrcObj(props.srcObject);

    const handler = () => setSrcObj(props.srcObject);
    props.srcObject.addEventListener("active", handler);
    return () => {
      props.srcObject.removeEventListener("active", handler);
    };
  }, [props.ignoreAudio, props.srcObject]);

  // Update makeshift fps counter
  useEffect(() => {
    /** Update info string containing the fps counter */
    const interval = setInterval(() => {
      if (refVideo.current?.srcObject === null) return;

      const videoTracks = props.srcObject.getVideoTracks();
      if (videoTracks.length === 0) return;

      const fps = videoTracks[0].getSettings().frameRate;
      if (!fps) {
        if (info !== "") {
          setInfo("");
        }
        return;
      }
      const newInfo = `${fps.toFixed(3)} fps`;
      if (info !== newInfo) {
        setInfo(newInfo);
      }
    }, 1000);

    return () => {
      clearInterval(interval);
    };
  }, [info, props.srcObject]);

  return (
    <div className="videoWrapper">
      <p>
        {props.title}
        {props.srcObject.active ? "" : " [inactive]"}
      </p>
      <video ref={refVideo} autoPlay playsInline width={300} />
      <div className="fpsCounter">{info}</div>
    </div>
  );
}
