import {
  Box,
  Group,
  Participant,
  Session,
  Shape,
  CanvasElement,
  Filter,
  AsymmetricFilter
} from "../types";
import moment from "moment";

export const getRandomColor = () => {
  const letters = "0123456789ABCDEF";
  let color = "#";
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
};

export const filterListByIndex = <T>(list: T[], index: number): T[] => {
  const filteredList = list.filter((_, i) => {
    return i !== index;
  });

  return filteredList;
};

export const filterListById = <T extends { id: string }>(list: T[], id: string): T[] => {
  const filteredList = list.filter((obj) => {
    return obj.id !== id;
  });

  return filteredList;
};

export const getSessionById = (id: string, list: Session[]) => {
  const session = list.filter((obj) => {
    return obj.id === id;
  });
  if (session && session.length >= 1) {
    return session[0];
  }
  return null;
};

export const getParticipantById = (id: string, sessionData: Session) => {
  const participants = sessionData.participants;
  const participant = participants.filter((participant) => {
    return participant.id === id;
  });
  return participant[0];
};

export const integerToDateTime = (integerDate: number) => {
  return new Date(integerDate).toLocaleString();
};

export const getTotalBox = (boxes: Box[]): Box => {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  boxes.forEach((box) => {
    minX = Math.min(minX, box.x);
    minY = Math.min(minY, box.y);
    maxX = Math.max(maxX, box.x + box.width);
    maxY = Math.max(maxY, box.y + box.height);
  });

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY
  };
};

export const getLocalStream = async () => {
  // TODO: allow the user to select a specific camera / audio device?
  const constraints = {
    video: true,
    audio: true
  };
  try {
    return await navigator.mediaDevices.getUserMedia(constraints);
  } catch (error) {
    console.error("Error opening video camera.", error);
  }
};

export const getParticipantDimensions = (
  participants: Participant[]
): Array<{ shapes: Shape; groups: Group; id: string }> => {
  const dimensions: Array<{ shapes: Shape; groups: Group; id: string }> = [];

  participants.forEach((participant: Participant) => {
    dimensions.push({
      id: participant.canvas_id,
      shapes: {
        x: 0,
        y: 0,
        fill: generateRandomColor(participant.canvas_id),
        participant_name: participant.participant_name
      },
      groups: {
        x: participant.position.x,
        y: participant.position.y,
        width: participant.size.width,
        height: participant.size.height
      }
    });
  });

  return dimensions;
};

export const getAsymmetricParticipantDimensions = (
  view: CanvasElement[]
): Array<{ shapes: Shape; groups: Group; id: string }> => {
  const dimensions: Array<{ shapes: Shape; groups: Group; id: string }> = [];

  view.forEach((canvasElement: CanvasElement) => {
    dimensions.push({
      shapes: {
        x: 0,
        y: 0,
        fill: generateRandomColor(canvasElement.id),
        participant_name: canvasElement.participant_name
      },
      groups: {
        x: canvasElement.position.x,
        y: canvasElement.position.y,
        width: canvasElement.size.width,
        height: canvasElement.size.height
      },
      id: canvasElement.id
    });
  });

  return dimensions;
};

export const getAsymmetricViewArray = (
  asymmetricParticipantDimensions: Array<{ shapes: Shape; groups: Group; id: string }>
): CanvasElement[] => {
  const view: CanvasElement[] = [];

  asymmetricParticipantDimensions.forEach(
    (dimension: { shapes: Shape; groups: Group; id: string }) => {
      const { shapes, groups, id } = dimension;

      view.push({
        id,
        participant_name: shapes.participant_name,
        size: {
          width: groups.width,
          height: groups.height
        },
        position: {
          x: groups.x,
          y: groups.y,
          z: 0
        }
      });
    }
  );

  return view;
};

export const getParticipantIdentifiers = (participants: Participant[]) => {
  return participants.map((participant) => {
    return {
      id: participant.asymmetric_filters_id,
      name: participant.participant_name,
      audio_filters: participant.audio_filters,
      video_filters: participant.video_filters
    };
  });
};

export const getAsymmetricParticipantIdentifiers = (asymmetricFilters: AsymmetricFilter[]) => {
  return asymmetricFilters.map((filter) => {
    return {
      id: filter.id,
      name: filter.participant_name,
      audio_filters: filter.audio_filters,
      video_filters: filter.video_filters
    };
  });
};

export const getAsymmetricFiltersArray = (
  participantIdentifiers: Array<{
    id: string;
    name: string;
    audio_filters: Filter[];
    video_filters: Filter[];
  }>,
  asymmetric_filters_id: string | undefined
): AsymmetricFilter[] => {
  const filters: AsymmetricFilter[] = [];

  participantIdentifiers.forEach((p) => {
    if (asymmetric_filters_id !== p.id) {
      filters.push({
        id: p.id,
        participant_name: p.name,
        audio_filters: [...p.audio_filters],
        video_filters: [...p.video_filters]
      });
    }
  });

  return filters;
};

/*
 * Correct format: YYYY-MM-DDTHH:MM, e.g. 2018-06-07T00:00
 * date - Date input in form of an integer
 */
export const formatDate = (date: number): string => {
  const formattedDate = moment(date).format("YYYY-MM-DDTHH:mm");

  return formattedDate;
};

export const sortSessions = (sessions: Session[]) => {
  return sessions.sort((a: Session, b: Session) => moment(a.date).diff(b.date));
};

export const getPastAndFutureSessions = (sessionsList: Session[]) => {
  const pastSessions: Session[] = [];
  const futureSessions: Session[] = [];

  const today = new Date().getTime();

  sessionsList.forEach((session) => {
    // Sessions in the past are in the past and cannot be started.
    // end_time needs to be > 0 for a session to be past as well.
    if (session.date < today || session.end_time > 0) {
      pastSessions.push(session);
    } else {
      futureSessions.push(session);
    }
  });

  return { pastSession: pastSessions, futureSession: futureSessions };
};

// Required: "title", "description", "date", "time_limit"
export const checkValidSession = (sessionData: Session) => {
  return (
    sessionData.title !== "" &&
    sessionData.description !== "" &&
    // TO DO : remove session time_limit from the check and session.json, as it is no longer needed.
    // Because the session is not going to end after the session duration has passed.
    // sessionData.time_limit !== 0 &&
    sessionData.date !== 0
  );
};

export const isFutureSession = (sessionData: Session) => {
  const today = new Date().getTime();

  return today < sessionData.date;
};

export const getVideoTitle = (peer: any, index: number) => {
  if (peer) {
    return `${peer.participant_name}`;
  }
  return `Peer stream ${index + 1}`;
};

// Generating the dynamic participant invite link based on the host domain.
export const getParticipantInviteLink = (participantId: string, sessionId: string) => {
  return `${window.location.origin}/consent?participantId=${participantId}&sessionId=${sessionId}`;
};

export const getParticipantName = (participantId: string, participants: Array<Participant>) => {
  if (participantId === "experimenter" || participantId === "participants") {
    return;
  }
  return participants.find((p, i) => p.id === participantId).participant_name;
};

export const generateRandomColor = (canvasId: string): string => {
  const hash = hashCode(canvasId);

  // Convert the hash into a hexadecimal color code
  const color = "#" + ((hash & 0xffffff) | 0x1000000).toString(16).slice(1);

  return color;
};

// Generate a numeric hash based on a string
const hashCode = (str: string): number => {
  let hash = 0;

  if (str.length === 0) {
    return hash;
  }

  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32bit integer
  }

  return hash;
};
