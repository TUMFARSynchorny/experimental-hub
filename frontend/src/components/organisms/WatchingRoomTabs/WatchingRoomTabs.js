import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import "react-tabs/style/react-tabs.css";
import NotesTab from "../../molecules/NotesTab/NotesTab";
import ParticipantsTab from "../../molecules/ParticipantsTab/ParticipantsTab";
import OverviewTab from "../../molecules/OverviewTab/OverviewTab";

function WatchingRoomTabs({
  connectedParticipants,
  onKickBanParticipant,
  onAddNote,
  onLeaveExperiment,
  onStartExperiment,
  onMuteParticipant,
  onEndExperiment
}) {
  return (
    <>
      <Tabs>
        <TabList>
          <Tab>Overview</Tab>
          <Tab>Notes</Tab>
          <Tab>Participants</Tab>
        </TabList>

        <TabPanel>
          <OverviewTab
            onLeaveExperiment={onLeaveExperiment}
            onStartExperiment={onStartExperiment}
            onEndExperiment={onEndExperiment}
          />
        </TabPanel>
        <TabPanel>
          <NotesTab onAddNote={onAddNote} />
        </TabPanel>
        <TabPanel>
          <ParticipantsTab
            connectedParticipants={connectedParticipants}
            onKickBanParticipant={onKickBanParticipant}
            onMuteParticipant={onMuteParticipant}
          />
        </TabPanel>
      </Tabs>
    </>
  );
}

export default WatchingRoomTabs;
