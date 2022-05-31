import { useState } from "react";
import Heading from "../../components/atoms/Heading/Heading";
import WatchingRoomTabs from "../../components/organisms/WatchingRoomTabs/WatchingRoomTabs";
import "./WatchingRoom.css";

function WatchingRoom() {
  const [state, setState] = useState("WAITING");
  return (
    <div className="watchingRoomContainer">
      <div className="watchingRoomHeader">
        <Heading heading={"State: " + state} />
      </div>
      <div className="watchingRoomData">
        <div className="participantLiveStream"></div>
        <div className="watchingRoomTabs">
          <WatchingRoomTabs />
        </div>
      </div>
    </div>
  );
}

export default WatchingRoom;
