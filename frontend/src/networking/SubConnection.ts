import Connection from "./Connection";
import ConnectionBase from "./ConnectionBase";
import { ConnectionAnswer, ConnectionOffer, ConnectionProposal } from "./typing";

/**
 * SubConnection class used by {@link Connection} to get streams of other users from the backend.
 * 
 * Not intended for use outside of {@link Connection}.
 * 
 * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol for details about the connection protocol.
 * @extends ConnectionBase
 */
export default class SubConnection extends ConnectionBase<MediaStream | string> {
  readonly id: string;

  private connection: Connection;
  private stopped: boolean;

  /**
   * TODO update docs 
   * 
   * Initialize new SubConnection.
   * @param offer ConnectionOffer received from the backend, with information on how to open the SubConnection.
   * @param connection parent Connection, used to send data to the backend.
   * @param logging Whether logging should be enabled.
   * 
   * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol for details about the connection protocol.
   */
  constructor(proposal: ConnectionProposal, connection: Connection, logging: boolean) {
    super(true, `SubConnection - ${proposal.id}`, logging);
    this.id = proposal.id;
    this.connection = connection;
    this.stopped = false;
    this._participantSummary = proposal.participant_summary;

    this.log("Initiating SubConnection");
  }

  /**
   * Start the subconnection.
   * 
   * TODO update docs
   * 
   * Create and send an Answer to the initial offer set in the constructor and send 
   * it to the backend using the connection set in the constructor.
   * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol for details about the connection protocol.
   */
  public async sendOffer() {
    this.log("Generating & sending offer");
    const offer = await this.createOffer();
    const connectionOffer: ConnectionOffer = {
      id: this.id,
      offer: offer
    };
    this.connection.sendMessage("CONNECTION_OFFER", connectionOffer);
  }

  /** TODO document */
  public async handleAnswer(answer: ConnectionAnswer) {
    // TODO Check if answer already handled
    await this.pc.setRemoteDescription(answer.answer);
  }

  /**
   * Stop the SubConnection.
   * 
   * Stop all transceivers associated with this SubConnection and its peer connection. 
   * 
   * Multiple calls to this functions are ignored.
   * @see https://github.com/TUMFARSynchorny/experimental-hub/wiki/Connection-Protocol for details about the connection protocol.
   */
  public stop() {
    if (this.stopped) {
      return;
    }
    this.stopped = true;
    this.log("Stopping");

    // close transceivers
    this.pc.getTransceivers().forEach(function (transceiver) {
      if (transceiver.stop) {
        transceiver.stop();
      }
    });

    this.pc.close();
    this.emit("connectionClosed", this.id);
  }

  protected handleSignalingStateChange(): void {
    this.log(`SignalingState: ${this.pc.signalingState}`);
    if (this.pc.signalingState === "closed") {
      this.stop();
    }
  }

  protected handleIceConnectionStateChange(): void {
    this.log(`IceConnectionState: ${this.pc.iceConnectionState}`);
    if (["disconnected", "closed", "failed"].includes(this.pc.iceConnectionState)) {
      this.stop();
    }
  }
}
