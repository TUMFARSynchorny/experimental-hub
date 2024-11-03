import { PayloadAction, createSlice } from "@reduxjs/toolkit";
import { RootState } from "../../store";
import { Filter, Participant, Session } from "../../types";

type OpenSessionState = {
  session: Session;
  filtersData: { TEST: Filter[]; SESSION: Filter[] };
};

const initialState: OpenSessionState = {
  session: {
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
  },
  filtersData: { TEST: [], SESSION: [] }
};

export const openSessionSlice = createSlice({
  name: "openSession",
  initialState,
  reducers: {
    initializeSession: (state, { payload }) => {
      state.session = payload;
    },

    initializeFiltersData: (state, { payload }) => {
      state.filtersData = payload;
    },

    saveSession: (state, { payload }) => {
      state.session = payload;
    },

    changeValue: (state, { payload }) => {
      // todo: find a better approach to modify object props to type properly
      state.session = {
        ...state.session,
        [payload.objKey]: payload.objValue
      };
    },

    addParticipant: (state, { payload }: PayloadAction<Participant>) => {
      state.session.participants.push(payload);

      state.session.participants.map(({ view }) => {
        if (view.length > 0) {
          view.push({
            id: payload.canvas_id,
            participant_name: payload.participant_name,
            size: {
              width: payload.size.width,
              height: payload.size.height
            },
            position: {
              x: payload.position.x,
              y: payload.position.y,
              z: 0
            }
          });
        }
      });

      state.session.participants.map(({ asymmetric_filters }) => {
        if (asymmetric_filters.length > 0) {
          asymmetric_filters.push({
            id: payload.asymmetric_filters_id,
            participant_name: payload.participant_name,
            audio_filters: payload.audio_filters,
            video_filters: payload.video_filters
          });
        }
      });
    },

    changeParticipant: (
      state,
      { payload }: PayloadAction<{ index: number; participant: Participant }>
    ) => {
      const { index, participant } = payload;
      state.session.participants[index] = participant;

      state.session.participants.map(({ view }) => {
        if (view.length > 0) {
          const changedParticipantAsymmetryIndex = view.findIndex(
            (canvasElement) => canvasElement.id === participant.canvas_id
          );

          if (changedParticipantAsymmetryIndex !== -1) {
            view[changedParticipantAsymmetryIndex].participant_name = participant.participant_name;
          }
        }
      });

      state.session.participants.map(({ asymmetric_filters }) => {
        if (asymmetric_filters.length > 0) {
          const changedParticipantAsymmetryIndex = asymmetric_filters.findIndex(
            (asymmetricFilter) => asymmetricFilter.id === participant.asymmetric_filters_id
          );

          if (changedParticipantAsymmetryIndex !== -1) {
            asymmetric_filters[changedParticipantAsymmetryIndex].participant_name =
              participant.participant_name;
          }
        }
      });
    },

    deleteParticipant: (state, { payload }: PayloadAction<number>) => {
      const participantIndex = payload;

      const deletedParticipant = state.session.participants.find(
        (_, index) => index === participantIndex
      );

      state.session.participants.map(({ view }, index) => {
        state.session.participants[index].view = view.filter(
          (canvasElement) => canvasElement.id !== deletedParticipant.canvas_id
        );
      });

      state.session.participants.map(({ asymmetric_filters }, index) => {
        state.session.participants[index].asymmetric_filters = asymmetric_filters.filter(
          (asymmetricFilter) => asymmetricFilter.id !== deletedParticipant.asymmetric_filters_id
        );
      });

      state.session.participants = state.session.participants.filter(
        (_, index) => index !== participantIndex
      );
    },

    changeParticipantDimensions: (state, { payload }) => {
      const { index, position, size } = payload;
      state.session.participants[index].position = position;
      state.session.participants[index].size = size;
    },

    copySession: (state, { payload }: PayloadAction<Session>) => {
      state.session = {
        ...payload,
        id: "",
        creation_time: 0,
        end_time: 0,
        start_time: 0,
        notes: [],
        log: [],
        participants: payload.participants.map((p) => ({
          ...p,
          id: "",
          chat: [],
          lastMessageSentTime: 0,
          lastMessageReadTime: 0
        }))
      };
    }
  }
});

export const {
  initializeSession,
  initializeFiltersData,
  saveSession,
  changeValue,
  addParticipant,
  changeParticipant,
  deleteParticipant,
  changeParticipantDimensions,
  copySession
} = openSessionSlice.actions;

export default openSessionSlice.reducer;

export const selectOpenSession = (state: RootState): Session => state.openSession.session;

export const selectFiltersDataSession = (state: RootState): Filter[] =>
  state.openSession.filtersData.SESSION;

export const selectFiltersDataTest = (state: RootState): Filter[] =>
  state.openSession.filtersData.TEST;

export const selectNumberOfParticipants = (state: RootState): number =>
  state.openSession.session.participants.length;
