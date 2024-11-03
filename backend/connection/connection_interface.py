"""Provide the abstract `ConnectionInterface`."""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from pyee.asyncio import AsyncIOEventEmitter
from connection.messages.rtc_ice_candidate_dict import RTCIceCandidateDict

from connection.connection_state import ConnectionState
from connection.messages import (
    ConnectionAnswerDict,
    ConnectionOfferDict,
    ConnectionProposalDict,
    AddIceCandidateDict,
)

from filters import FilterDict
from filters.filter_data_dict import FilterDataDict
from custom_types.message import MessageDict
from session.data.participant.participant_summary import ParticipantSummaryDict


class ConnectionInterface(AsyncIOEventEmitter, metaclass=ABCMeta):
    """Abstract interface for connections with clients.

    Notes
    -----
    Do not instantiate directly, use subclasses / implementations of
    `ConnectionInterface` instead.

    See Also
    --------
    hub.connection.Connection : Implementation for ConnectionInterface.
    hub.connection_subprocess.ConnectionSubprocess :
        Implementation for ConnectionInterface.
    """

    @abstractmethod
    async def stop(self) -> None:
        """Stop this connection.

        Stops all incoming and outgoing streams and emits the `state_change` event.
        When finished, it removes all event listeners from this Connection, as no more
        events will be emitted.
        """
        pass

    @abstractmethod
    async def send(self, data: MessageDict | dict) -> None:
        """Send `data` to connected client over the datachannel.

        Parameters
        ----------
        data : custom_types.message.MessageDict or dict
            Data that will be stringified and send to the connected client.
        """
        pass

    @property
    @abstractmethod
    def state(self) -> ConnectionState:
        """Get the hub.connection_state.ConnectionState the Connection is in."""
        pass

    @abstractmethod
    async def create_subscriber_proposal(
        self, participant_summary: ParticipantSummaryDict | str | None,
        subscriber=None
    ) -> ConnectionProposalDict:
        """Create a SubConnection proposal.

        Parameters
        ----------
        participant_summary : custom_types.participant_summary.ParticipantSummaryDict, str or None
            Optional participant summary or participant ID that will be included in the
            resulting proposal.

        Returns
        -------
        connection.messages.ConnectionProposalDict
            Connection proposal including `participant_summary`.  The `id` in the
            returned dict is the `subconnection_id` for this proposal.  If the
            subscriber should be removed manually, this ID is required for
            `stop_subconnection(subconnection_id)`.  This is not required if the user
            disconnects.

        See Also
        --------
        Connection Protocol Wiki :
            Details about the connection protocol this function is part of.
            https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
        """
        pass

    @abstractmethod
    async def handle_add_ice_candidate(self, candidate: RTCIceCandidateDict):
        """Handle an new ice candidate which was send by the client.

        This is used to handle the establishment of new main connections.
        For subconnections, use `handle_subscriber_add_ice_candidate`.

        Parameters
        ----------
        candidate : connection.messages.rtc_ice_candidate_dict.RTCIceCandidateDict
            New ice candidate send by the client.
        """
        pass

    @abstractmethod
    async def handle_subscriber_offer(
        self, offer: ConnectionOfferDict
    ) -> ConnectionAnswerDict:
        """Handle a ConnectionOffer based on a ConnectionProposal from this Connection.

        The offer should be in response to a
        custom_types.connection.ConnectionProposalDict created by this connection and
        send to a different user.

        Parameters
        ----------
        answer : connection.messages.connection_answer_dict.ConnectionAnswerDict
            Answer to a custom_types.connection.ConnectionOfferDict created by this
            connection.  The answer ID must match an offer ID send by this connection.

        Raises
        ------
        ErrorDictException
            If `id` in `offer` is unknown (not a hub.connection.SubConnection ID
            handled by this hub.connection.Connection).

        See Also
        --------
        Connection Protocol Wiki :
            Details about the connection protocol this function is part of.
            https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol
        """
        pass

    @abstractmethod
    async def handle_subscriber_add_ice_candidate(
        self, candidate: AddIceCandidateDict
    ):
        """Handle an new ice candidate which was send by the client.

        This is used to handle the establishment of new sub connections.
        For main connections, use `handle_add_ice_candidate`.

        Parameters
        ----------
        candidate : connection.messages.add_ice_candidate_dict.AddIceCandidateDict
            New ice candidate send by the client, including subconnection ID.
        """
        pass

    @abstractmethod
    async def stop_subconnection(self, subconnection_id: str) -> None:
        """Stop the subconnection with `subconnection_id`.

        This can be used to manually remove a subscriber without disconnecting the user,
        e.g. when an experimenter leaves an experiment.  It is not required if the user
        disconnects.

        The `subconnection_id` is obtained from the result of
        `create_subscriber_proposal` (`id` variable).

        Parameters
        ----------
        subconnection_id : str
            ID of the outgoing SubConnection that will be stopped.

        See Also
        --------
        create_subscriber_proposal :
            Create a new subscriber proposal, containing the subconnection ID.
        """
        pass

    @abstractmethod
    async def set_muted(self, video: bool, audio: bool) -> None:
        """Set the muted state for this connection.

        Parameters
        ----------
        video : bool
            Whether the video track should be muted.
        audio : bool
            Whether the audio track should be muted.
        """
        pass

    @abstractmethod
    async def set_video_filters(self, filters: list[FilterDict]) -> None:
        """Set or update video filters to `filters`.

        Parameters
        ----------
        filters : list of filters.FilterDict
            List of video filter configs.
        """
        pass

    @abstractmethod
    async def set_audio_filters(self, filters: list[FilterDict]) -> None:
        """Set or update audio filters to `filters`.

        Parameters
        ----------
        filters : list of filters.FilterDict
            List of audio filter configs.
        """
        pass

    @abstractmethod
    async def set_video_group_filters(
        self, group_filters: list[FilterDict], ports: list[tuple[int, int]]
    ) -> None:
        """Set or update video filters to `filters`.

        Parameters
        ----------
        filters : list of filters.FilterDict
            List of video filter configs.
        ports: list of tuples of int
            List of tuples of ports that the group filter commnunicates with the aggregator
        """
        pass

    @abstractmethod
    async def set_audio_group_filters(
        self, group_filters: list[FilterDict], ports: list[tuple[int, int]]
    ) -> None:
        """Set or update audio filters to `filters`.

        Parameters
        ----------
        filters : list of filters.FilterDict
            List of audio filter configs.
        ports: list of tuples of int
            List of tuples of ports that the group filter commnunicates with the aggregator
        """
        pass

    @abstractmethod
    async def start_recording(self) -> None:
        """Start recording tracks for this connection.

        Both audio and video media track will be recorded.
        """
        pass

    @abstractmethod
    async def stop_recording(self) -> None:
        """Stop recording tracks for this connection.

        Both audio and video recorder will stop.
        """
        pass

    @abstractmethod
    async def get_video_filters_data(self, id, name) -> list[FilterDataDict]:
        """Get Data from a specific video filter

        Parameters
        ----------
        name: name of the filter
            This is the unique name with which the filter can be identified
        id : id of the filter
            Can be either 'all' for all filters with the name
            or specific id for just one filter
        """
        pass

    @abstractmethod
    async def get_audio_filters_data(self, id, name) -> list[FilterDataDict]:
        """Get Data from a specific audio filter

        Parameters
        ----------
        name: name of the filter
            This is the unique name with which the filter can be identified
        id : id of the filter
            Can be either 'all' for all filters with the name
            or specific id for just one filter
        """
        pass
