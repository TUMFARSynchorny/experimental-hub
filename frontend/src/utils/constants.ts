import { ChatMessage, Note, Participant, Session, Snackbar } from "../types";
import { AlertColor } from "@mui/material/Alert";

export const INITIAL_SESSION_DATA: Session = {
  id: "",
  title: "",
  description: "",
  date: 0,
  time_limit: 0,
  record: false,
  participants: [],
  start_time: 0,
  end_time: 0,
  creation_time: 0,
  notes: [],
  log: []
};

export const CANVAS_SIZE = {
  // TODO: make the CANVAS_SIZE responsive
  // after PR #43 making video canvas size static (suited to macbook 13.3 inch) as a temporary workaround
  // for properly alinged display of the konva elements
  // old width: 1138.333, // 1366
  width: 1040,
  height: 640, //768
  scale: 1.2
};

export const INITIAL_PARTICIPANT_DATA: Participant = {
  id: "",
  participant_name: "",
  muted_audio: true,
  muted_video: true,
  local_stream: false,
  banned: false,
  video_filters: [],
  audio_filters: [],
  chat_filters: [],
  audio_group_filters: [],
  video_group_filters: [],
  chat: [],
  lastMessageSentTime: 0,
  lastMessageReadTime: 0,
  position: {
    x: 10,
    y: 10,
    z: 0
  },
  size: {
    width: 250,
    height: 250
  },
  view: [],
  canvas_id: "",
  asymmetric_filters: [],
  asymmetric_filters_id: ""
};

export const INITIAL_NOTE_DATA: Note = {
  time: 0,
  speakers: [],
  content: ""
};

export const INITIAL_CHAT_DATA: ChatMessage = {
  time: 0,
  message: "",
  author: "",
  target: ""
};

/**
 * Environment of the client. Set by CreateReactApp depending on how you start it.
 * @type {("development" | "test" | "production")}
 */
export const ENVIRONMENT = import.meta.env.NODE_ENV; // "development", "test" or "production"

/**
 * Backend address.
 */
export const BACKEND =
  ENVIRONMENT === "production" ? window.location.origin : import.meta.env.VITE_BACKEND;

/**
 * Optional ICE servers.
 * undefined or list of RTCIceServers
 * @see https://developer.mozilla.org/en-US/docs/Web/API/RTCIceServer
 */
export const ICE_SERVERS = parseIceServers();

function parseIceServers() {
  const servers = import.meta.env.VITE_ICE_SERVERS;
  console.log("VITE_ICE_SERVERS", servers);

  if (!servers) {
    return undefined;
  }
  try {
    return JSON.parse(servers);
  } catch (error) {
    console.error("Failed to parse ice servers.", error);
    return undefined;
  }
}

export const PARTICIPANT_HOST = "http://localhost:3000/lobby/";

// Displays the same set of instructions in both the /lobby and in the /experimentOverview.
export const instructionsList = [
  "Please remove any glasses, caps or other such articles if you are wearing any.",
  "Ensure that your surrounding lighting is good.",
  "We would like to know about your experience, so please take 5  minutes at the end to do the Feedback Survey."
];

// Initialising the notification snackbar used in many components.
export const initialSnackbar: Snackbar = {
  open: false,
  text: "",
  severity: "success" as AlertColor
};
