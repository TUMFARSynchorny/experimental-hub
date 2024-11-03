import logging

from aiortc import (RTCPeerConnection, MediaStreamTrack,
                    RTCSessionDescription, RTCIceCandidate)
from pyee.asyncio import AsyncIOEventEmitter

from connection.messages import (
    ConnectionAnswerDict,
    ConnectionProposalDict,
    RTCSessionDescriptionDict,
)
from hub.track_handler import TrackHandler
from session.data.participant.participant_summary import ParticipantSummaryDict


class SubConnection(AsyncIOEventEmitter):
    """SubConnection used to send additional stream to a client.

    Each SubConnection has an audio and video track -> one stream which they send to the
    client.  For communication, it used the datachannel of the parent
    module.connection.Connection.

    Extends AsyncIOEventEmitter, providing the following events:
    - `connection_closed` : str
        Emitted when this SubConnection closes.  Data is the ID of this SubConnection.
    """

    id: str
    _participant_summary: ParticipantSummaryDict | str | None
    _pc: RTCPeerConnection

    _audio_track: MediaStreamTrack | TrackHandler
    _video_track: MediaStreamTrack | TrackHandler

    _closed: bool
    _logger: logging.Logger

    def __init__(
            self,
            id: str,
            video_track: MediaStreamTrack | TrackHandler,
            audio_track: MediaStreamTrack | TrackHandler,
            participant_summary: ParticipantSummaryDict | str | None,
            log_name_suffix: str,
    ) -> None:
        """Initialize new SubConnection.

        Parameters
        ----------
        id : str
        video_track : aiortc.MediaStreamTrack
            Video track that will be sent in this SubConnection.
        audio_track : aiortc.MediaStreamTrack
            Audio track that will be sent in this SubConnection.
        participant_summary : None or custom_types.participant_summary.ParticipantSummaryDict
            Participant summary or ID send to the client with the initial offer.
        """
        super().__init__()
        self._logger = logging.getLogger(f"SubConnection-{log_name_suffix}")
        self.id = id
        self._audio_track = audio_track
        self._video_track = video_track
        self._closed = False
        self._participant_summary = participant_summary

        self._pc = RTCPeerConnection()
        self._pc.addTrack(video_track)
        self._pc.addTrack(audio_track)
        self._pc.on("connectionstatechange", self._on_connection_state_change)

        # Stop SubConnection if one of the tracks ends
        # audio_track.on("ended", self.stop)
        # video_track.on("ended", self.stop)

    @property
    def proposal(self):
        """Get a custom_types.connection.ConnectionProposalDict for this SubConnection.

        See Also
        --------
        Connection Protocol Wiki :
            https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
        """
        return ConnectionProposalDict(
            id=self.id, participant_summary=self._participant_summary
        )

    async def stop(self) -> None:
        """Stop the SubConnection and its associated tracks.

        Emits a `connection_closed` event with the ID of this SubConnection.  When
        finished, it removes all event listeners from this Connection, as no more events
        will be emitted.
        """
        if self._closed:
            return
        self.emit("connection_closed", self.id)

        await self._audio_track.stop()
        await self._video_track.stop()

        self._logger.debug("Closing SubConnection")
        self._closed = True
        await self._pc.close()
        self.remove_all_listeners()

    async def handle_offer(self, offer: RTCSessionDescription) -> ConnectionAnswerDict:
        """Handle a `CONNECTION_OFFER` message for this SubConnection.

        Parameters
        ----------
        offer : aiortc.RTCSessionDescription

        Returns
        -------
        connection.messages.connection_answer_dict.ConnectionAnswerDict
            Answer that should be sent as a response to the offer.

        See Also
        --------
        Connection Protocol Wiki :
            https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
        """
        await self._pc.setRemoteDescription(offer)

        answer = await self._pc.createAnswer()
        await self._pc.setLocalDescription(answer)  # type: ignore

        answer_dict = RTCSessionDescriptionDict(
            sdp=self._pc.localDescription.sdp, type=self._pc.localDescription.type  # type: ignore
        )
        return ConnectionAnswerDict(id=self.id, answer=answer_dict)

    async def _on_connection_state_change(self):
        """Handle connection state change."""
        self._logger.debug(f"Peer Connection state change: {self._pc.connectionState}")
        if self._pc.connectionState in ["closed", "failed"]:
            await self.stop()

    async def handle_add_ice_candidate(self, candidate: RTCIceCandidate):
        """Handle a `ADD_ICE_CANDIDATE` message for this SubConnection.

        Parameters
        ----------
        candidate : aiortc.RTCIceCandidate
            New ICE candidate.

        See Also
        --------
        Connection Protocol Wiki :
        """
        await self._pc.addIceCandidate(candidate)
