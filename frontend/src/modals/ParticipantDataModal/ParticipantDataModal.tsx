import Box from "@mui/material/Box";
import Checkbox from "@mui/material/Checkbox";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import FormControlLabel from "@mui/material/FormControlLabel";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Switch from "@mui/material/Switch";
import TextField from "@mui/material/TextField";
import React, { useEffect, useState } from "react";
import { ActionButton } from "../../components/atoms/Button";
import CustomSnackbar from "../../components/atoms/CustomSnackbar/CustomSnackbar";
import { initialSnackbar } from "../../utils/constants";
import { getAsymmetricFiltersArray, getParticipantInviteLink } from "../../utils/utils";
import { useAppSelector } from "../../redux/hooks";
import {
  Filter,
  ChatFilter,
  FilterConfigArray,
  Participant,
  Shape,
  Group,
  AsymmetricFilter
} from "../../types";
import {
  selectFiltersDataSession,
  selectNumberOfParticipants
} from "../../redux/slices/openSessionSlice";
import { v4 as uuid } from "uuid";
import DragAndDrop from "../../components/organisms/DragAndDrop/DragAndDrop";
import { getAsymmetricParticipantDimensions, getAsymmetricViewArray } from "../../utils/utils";
import chatFiltersData from "../../chat_filters.json";
import Grid from "@mui/material/Grid";
import { FilterList } from "../../components/molecules/FilterList/FilterList";
import { FilterGroupDropdown } from "../../components/molecules/FilterGroupDropdown/FilterGroupDropdown";
import { Tooltip } from "@nextui-org/react";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import HelpOutlineOutlinedIcon from "@mui/icons-material/HelpOutlineOutlined";

const chatFilters: ChatFilter[] = chatFiltersData.chat_filters.map((filter: ChatFilter) => {
  return filter;
});

const defaultChatFilter = {
  id: "",
  name: "Placeholder",
  config: {}
};

type Props = {
  originalParticipant: Participant;
  sessionId: string;
  index: number;
  showParticipantInput: boolean;
  setShowParticipantInput: React.Dispatch<React.SetStateAction<boolean>>;
  onDeleteParticipant: (index: number) => void;
  handleParticipantChange: (index: number, participant: Participant) => void;
  handleCanvasPlacement: (participantCount: number) => void;
  setSnackbarResponse: React.Dispatch<
    React.SetStateAction<{
      newParticipantInputEmpty: boolean;
      requiredInformationMissing: boolean;
      participantOriginalEmpty: boolean;
      newInputEqualsOld: boolean;
    }>
  >;
  participantDimensions: {
    shapes: Shape;
    groups: Group;
  }[];
  participantIdentifiers: {
    id: string;
    name: string;
    audio_filters: Filter[];
    video_filters: Filter[];
  }[];
};

enum ParticipantDataModalTab {
  AsymmetricCanvas,
  AsymmetricFilters
}

function ParticipantDataModal({
  originalParticipant,
  sessionId,
  index,
  showParticipantInput,
  setShowParticipantInput,
  handleParticipantChange,
  onDeleteParticipant,
  setSnackbarResponse,
  handleCanvasPlacement,
  participantDimensions,
  participantIdentifiers
}: Props) {
  // We set the 'selectedFilter' to a default filter type, because the MUI Select component requires a default value when the page loads.
  const defaultFilter = {
    id: "",
    name: "Placeholder",
    channel: "",
    groupFilter: false,
    config: {}
  };
  const [participantCopy, setParticipantCopy] = useState(originalParticipant);
  const [selectedFilter, setSelectedFilter] = useState<Filter>(defaultFilter);
  const [selectedChatFilter, setSelectedChatFilter] = useState<ChatFilter>(defaultChatFilter);
  const [selectedAsymmetricFilters, setSelectedAsymmetricFilters] = useState<
    { id: string; filter: Filter }[]
  >([]);
  const filtersData = useAppSelector(selectFiltersDataSession);
  const individualFilters = filtersData.filter((filter) => filter.groupFilter !== true);
  const groupFilters = filtersData.filter((filter) => filter.groupFilter === true);
  const [snackbar, setSnackbar] = useState(initialSnackbar);
  const [requiredFilters, setRequiredFilters] = useState(new Map<string, string>());
  const originalDimensions: any = structuredClone(participantDimensions);
  const originalAsymmetricView = structuredClone(originalParticipant.view);
  const [asymmetricView, setAsymmetricView] = useState(
    originalParticipant.view ? getAsymmetricParticipantDimensions(originalParticipant.view) : []
  );
  const originalIdentifiers = structuredClone(participantIdentifiers);
  const originalAsymmetricFilters = structuredClone(originalParticipant.asymmetric_filters);
  const [asymmetricFilters, setAsymmetricFilters] = useState(
    originalParticipant.asymmetric_filters || []
  );
  const [isAsymmetricFiltersDisabled, setIsAsymmetricFiltersDisabled] = useState(
    participantIdentifiers.length <= 1
  );

  const [activeTab, setActiveTab] = useState(ParticipantDataModalTab.AsymmetricCanvas);
  const numberOfParticipants = useAppSelector(selectNumberOfParticipants);

  // Setting these snackbar response values to display the notification in Session Form Page.
  // These notifications cannot be displayed in this file, since on closing the Participant Modal,
  // this component and the immediate parent are deleted -> hence sending the snackbar responses
  // up to the grandparent.
  const snackbarResponse = {
    newParticipantInputEmpty: false,
    requiredInformationMissing: false,
    participantOriginalEmpty: false,
    newInputEqualsOld: false
  };

  const handleChange = <T extends keyof Participant>(objKey: T, objValue: Participant[T]) => {
    const newParticipantData = { ...participantCopy };
    newParticipantData[objKey] = objValue;
    setParticipantCopy(newParticipantData);
  };

  useEffect(() => {
    setAsymmetricView(getAsymmetricParticipantDimensions(originalParticipant.view));
  }, [originalParticipant.view]);

  useEffect(() => {
    handleChange("view", getAsymmetricViewArray(asymmetricView));
  }, [asymmetricView]);

  useEffect(() => {
    setAsymmetricFilters(originalParticipant?.asymmetric_filters);
  }, [originalParticipant?.asymmetric_filters]);

  useEffect(() => {
    handleChange("asymmetric_filters", asymmetricFilters);
  }, [asymmetricFilters]);

  useEffect(() => {
    setIsAsymmetricFiltersDisabled(participantIdentifiers.length <= 1);
  }, [participantIdentifiers]);

  const handleFilterChange = <T extends keyof Participant | keyof AsymmetricFilter>(
    index: number,
    key: string,
    value: number | string,
    filterTypeKey: T,
    asymmetricFilterId?: string
  ) => {
    if (asymmetricFilterId) {
      handleAsymmetricFilterChange(
        index,
        key,
        value,
        filterTypeKey as keyof AsymmetricFilter,
        asymmetricFilterId
      );
    } else {
      const filtersCopy: any = structuredClone(participantCopy[filterTypeKey]);
      filtersCopy[index]["config"][key]["value"] = value;
      handleChange(filterTypeKey, filtersCopy);
    }
  };

  const handleAsymmetricFilterChange = <T extends keyof AsymmetricFilter>(
    index: number,
    key: string,
    value: number | string,
    keyAsymmetricFilter: T,
    asymmetricFilterId: string
  ) => {
    // change the filter value in asymmetric_filters object
    const asymmetricFiltersCopy: AsymmetricFilter[] = structuredClone(
      participantCopy.asymmetric_filters
    );
    const filters: any = asymmetricFiltersCopy.find((filter) => filter.id === asymmetricFilterId)[
      keyAsymmetricFilter
    ];
    filters[index]["config"][key]["value"] = value;
    const newParticipantData = { ...participantCopy };
    newParticipantData.asymmetric_filters = asymmetricFiltersCopy;
    setParticipantCopy(newParticipantData);
  };

  const handleChatChange = <T extends keyof Participant>(
    index: number,
    key: string,
    value: number | string
  ) => {
    const chatFilters: ChatFilter[] = structuredClone(participantCopy.chat_filters);
    chatFilters[index]["config"][key]["value"] = value;
    handleChange("chat_filters", chatFilters);
  };

  // On closing the edit participant dialog, the entered data is checked (if data is not saved,
  // if required data is missing) to display appropriate notification.
  const onCloseModalWithoutData = () => {
    setShowParticipantInput(!showParticipantInput);
    setAsymmetricView(getAsymmetricParticipantDimensions(originalAsymmetricView));
    setAsymmetricFilters(originalAsymmetricFilters);

    const newParticipantInputEmpty = participantCopy.participant_name === "";
    if (newParticipantInputEmpty) {
      setSnackbarResponse({
        ...snackbarResponse,
        newParticipantInputEmpty: newParticipantInputEmpty
      });
      onDeleteParticipant(index);
      return;
    }

    const requiredInformationMissing = participantCopy.participant_name === "";
    if (requiredInformationMissing) {
      setSnackbarResponse({
        ...snackbarResponse,
        requiredInformationMissing: requiredInformationMissing
      });
      onDeleteParticipant(index);
      return;
    }

    const participantOriginalEmpty = originalParticipant.participant_name.length === 0;
    const newInputEqualsOld =
      JSON.stringify(participantCopy) === JSON.stringify(originalParticipant);

    if (participantOriginalEmpty && !newInputEqualsOld) {
      setSnackbarResponse({
        ...snackbarResponse,
        participantOriginalEmpty: participantOriginalEmpty,
        newInputEqualsOld: newInputEqualsOld
      });
      onDeleteParticipant(index);
      return;
    }

    if (!newInputEqualsOld) {
      setSnackbar({
        open: true,
        text: "You need to save the information first!",
        severity: "warning"
      });
      setParticipantCopy(originalParticipant);
      return;
    }
  };

  const onSaveParticipantData = () => {
    if (participantCopy.participant_name === "") {
      setSnackbar({
        open: true,
        text: "Failed to save participant since required fields are missing!",
        severity: "error"
      });
      return;
    }

    setSnackbar({
      open: true,
      text: `Saved participant: ${participantCopy.participant_name}`,
      severity: "success"
    });
    handleCanvasPlacement(numberOfParticipants);
    setShowParticipantInput(!showParticipantInput);
    handleParticipantChange(index, participantCopy);
  };

  const handleFilterSelect = async (
    filter: Filter,
    isGroupFilter: boolean,
    asymmetricFilterId?: string
  ) => {
    asymmetricFilterId
      ? setSelectedAsymmetricFilters((prevFilters) => {
          const existingIndex = prevFilters.findIndex((f) => f.id === asymmetricFilterId);

          if (existingIndex > -1) {
            // Update existing filter
            const updatedFilters = [...prevFilters];
            updatedFilters[existingIndex] = { id: asymmetricFilterId, filter };
            return updatedFilters;
          } else {
            // Add new filter
            return [...prevFilters, { id: asymmetricFilterId, filter }];
          }
        })
      : setSelectedFilter(filter);

    const newParticipantData = structuredClone(participantCopy);
    console.log(newParticipantData);
    const newFilter = structuredClone(filter);
    newFilter.id = uuid();

    // if a filter requires another filter, then it is added to the correct filter array
    for (const key in filter["config"]) {
      if (Array.isArray(filter["config"][key]["defaultValue"])) {
        if ((filter["config"][key] as FilterConfigArray)["requiresOtherFilter"]) {
          const otherFilter = structuredClone(
            filtersData.find(
              (filteredFilter) =>
                filteredFilter.name === (filter.config[key]["defaultValue"] as string[])[0]
            )
          );
          const id = uuid();
          otherFilter.id = id;
          newFilter["config"][key]["value"] = id;
          // add bidirectional mapping of ids to required filters map; important for deleting filters
          setRequiredFilters(new Map(requiredFilters.set(id, newFilter.id).set(newFilter.id, id)));
          if (otherFilter.channel === "video" || otherFilter.channel === "both") {
            if (asymmetricFilterId) {
              newParticipantData.asymmetric_filters
                .find((item) => item.id === asymmetricFilterId)
                .video_filters.push(otherFilter);
            } else if (otherFilter.groupFilter) {
              newParticipantData.video_group_filters.push(otherFilter);
            } else {
              newParticipantData.video_filters.push(otherFilter);
            }
          }
          if (otherFilter.channel === "audio" || otherFilter.channel === "both") {
            if (asymmetricFilterId) {
              newParticipantData.asymmetric_filters
                .find((item) => item.id === asymmetricFilterId)
                .audio_filters.push(otherFilter);
            } else if (otherFilter.groupFilter) {
              newParticipantData.audio_group_filters.push(otherFilter);
            } else {
              newParticipantData.audio_filters.push(otherFilter);
            }
          }
        }
      }
    }

    if (newFilter.channel === "video" || newFilter.channel === "both") {
      if (asymmetricFilterId) {
        newParticipantData.asymmetric_filters
          .find((item) => item.id === asymmetricFilterId)
          .video_filters.push(newFilter);
      } else if (isGroupFilter) {
        newParticipantData.video_group_filters.push(newFilter);
      } else {
        newParticipantData.video_filters.push(newFilter);
      }
    }
    if (newFilter.channel === "audio" || newFilter.channel === "both") {
      if (asymmetricFilterId) {
        newParticipantData.asymmetric_filters
          .find((item) => item.id === asymmetricFilterId)
          .audio_filters.push(newFilter);
      } else if (isGroupFilter) {
        newParticipantData.audio_group_filters.push(newFilter);
      } else {
        newParticipantData.audio_filters.push(newFilter);
      }
    }
    setParticipantCopy(newParticipantData);
  };

  const handleSelectChatFilter = (chatFilter: ChatFilter) => {
    setSelectedChatFilter(chatFilter);
    const newParticipantData = structuredClone(participantCopy);
    const newFilter = structuredClone(chatFilter);
    newFilter.id = uuid();
    newParticipantData.chat_filters.push(newFilter);
    setParticipantCopy(newParticipantData);
  };

  /**
   * This function deletes the required filters in each filter array.
   * @param filterId - The id of the filter to be deleted.
   * @param otherFilterId - The id of the other filter to be deleted.
   * @param newParticipantData - The participant data to be updated.
   * @returns The updated participant data.
   * @remarks
   * This function is called when a filter should be deleted in each filter array.
   * It looks in all filter arrays and deletes the filters with id.
   * If the id is not found, then the filter is not deleted in the specific filter array.
   * */
  const deleteRequiredFiltersInEachFilterArray = (
    filterId: string,
    otherFilterId: string,
    newParticipantData: Participant
  ) => {
    newParticipantData.video_filters = newParticipantData.video_filters.filter(
      (filteredFilter: Filter) =>
        filteredFilter.id !== filterId && filteredFilter.id !== otherFilterId
    );
    newParticipantData.audio_filters = newParticipantData.audio_filters.filter(
      (filteredFilter: Filter) =>
        filteredFilter.id !== filterId && filteredFilter.id !== otherFilterId
    );

    newParticipantData.video_group_filters = newParticipantData.video_group_filters.filter(
      (filteredFilter: Filter) =>
        filteredFilter.id !== filterId && filteredFilter.id !== otherFilterId
    );

    newParticipantData.audio_group_filters = newParticipantData.audio_group_filters.filter(
      (filteredFilter: Filter) =>
        filteredFilter.id !== filterId && filteredFilter.id !== otherFilterId
    );

    return newParticipantData;
  };

  /**
   * This function deletes all required filters.
   * @param filter - The filter to be deleted.
   * @param newParticipantData - The participant data to be updated.
   * @param isGroupFilter - A boolean value to check if the filter is a group filter.
   * @returns The updated participant data.
   * @remarks
   * This function is called when a filter is deleted.
   * If a filter is required for another filter, then both the filters are deleted.
   * If a filter requires another filter, then both the filters are deleted.
   * */
  const deleteAllRequiredFilters = (filter: Filter, newParticipantData: Participant) => {
    // if filter is required for another filter or requires another filter, removes current filter and other filter
    if (requiredFilters.has(filter.id)) {
      const otherFilterId = requiredFilters.get(filter.id);
      requiredFilters.delete(filter.id);
      requiredFilters.delete(otherFilterId);
      deleteRequiredFiltersInEachFilterArray(filter.id, otherFilterId, newParticipantData);
    }

    return newParticipantData;
  };

  const handleDeleteVideoFilter = (
    videoFilter: Filter,
    filterCopyIndex: number,
    isGroupFilter: boolean,
    asymmetricFilterId?: string
  ) => {
    const newParticipantData = structuredClone(participantCopy);
    if (asymmetricFilterId) {
      newParticipantData.asymmetric_filters
        .find((item) => item.id === asymmetricFilterId)
        .video_filters.splice(filterCopyIndex, 1);
    } else if (isGroupFilter) {
      newParticipantData.video_group_filters.splice(filterCopyIndex, 1);
    } else {
      newParticipantData.video_filters.splice(filterCopyIndex, 1);
    }

    setParticipantCopy(deleteAllRequiredFilters(videoFilter, newParticipantData));
  };

  const handleDeleteAudioFilter = (
    audioFilter: Filter,
    filterCopyIndex: number,
    isGroupFilter: boolean,
    asymmetricFilterId?: string
  ) => {
    const newParticipantData = structuredClone(participantCopy);
    if (asymmetricFilterId) {
      newParticipantData.asymmetric_filters
        .find((item) => item.id === asymmetricFilterId)
        .audio_filters.splice(filterCopyIndex, 1);
    } else if (isGroupFilter) {
      newParticipantData.audio_group_filters.splice(filterCopyIndex, 1);
    } else {
      newParticipantData.audio_filters.splice(filterCopyIndex, 1);
    }

    setParticipantCopy(deleteAllRequiredFilters(audioFilter, newParticipantData));
  };

  const handleDeleteChatFilter = (chatFilter: ChatFilter, filterCopyIndex: number) => {
    const newParticipantData = structuredClone(participantCopy);
    newParticipantData.chat_filters.splice(filterCopyIndex, 1);

    setParticipantCopy(newParticipantData);
  };

  return (
    <>
      <CustomSnackbar
        open={snackbar.open}
        text={snackbar.text}
        severity={snackbar.severity}
        handleClose={() => setSnackbar(initialSnackbar)}
      />
      <Dialog
        open={showParticipantInput}
        onClose={() => onCloseModalWithoutData()}
        sx={{ "& .MuiDialog-paper": { width: "1600px", maxWidth: "1600px" } }}
      >
        <DialogTitle sx={{ textAlign: "center", fontWeight: "bold" }}>
          Participant Details
        </DialogTitle>
        <DialogContent>
          <Grid
            maxWidth={1600}
            minWidth={1600}
            maxHeight={800}
            minHeight={800}
            container
            spacing={{ xs: 3, md: 6 }}
          >
            <Grid item xs={4}>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 5,
                  my: 3
                }}
              >
                <TextField
                  label="Participant Name"
                  value={participantCopy.participant_name}
                  size="small"
                  fullWidth
                  required
                  onChange={(event) => {
                    handleChange("participant_name", event.target.value);
                  }}
                />
              </Box>
              <Box>
                <TextField
                  label="Invite Link"
                  size="small"
                  fullWidth
                  disabled
                  value={
                    !(participantCopy.id.length === 0 || sessionId.length === 0)
                      ? getParticipantInviteLink(participantCopy.id, sessionId)
                      : "Save session to generate link."
                  }
                />
              </Box>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 4,
                  my: 3
                }}
              >
                <TextField label="Width" size="small" value={participantCopy.size.width} disabled />
                <TextField
                  label="Height"
                  size="small"
                  value={participantCopy.size.height}
                  disabled
                />
              </Box>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 4,
                  my: 3
                }}
              >
                <TextField
                  label="x coordinate"
                  size="small"
                  value={participantCopy.position.x}
                  disabled
                />
                <TextField
                  label="y coordinate"
                  size="small"
                  value={participantCopy.position.y}
                  disabled
                />
              </Box>
              <Box sx={{ display: "flex", justifyContent: "center", gap: 2, my: 3 }}>
                <FormControlLabel
                  control={<Checkbox />}
                  label="Mute Audio"
                  checked={participantCopy.muted_audio}
                  onChange={() => {
                    handleChange("muted_audio", !participantCopy.muted_audio);
                  }}
                />
                <FormControlLabel
                  control={<Checkbox />}
                  label="Mute Video"
                  checked={participantCopy.muted_video}
                  onChange={() => {
                    handleChange("muted_video", !participantCopy.muted_video);
                  }}
                />
                <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <FormControlLabel
                    control={<Checkbox />}
                    label="Local Stream"
                    checked={participantCopy.local_stream}
                    onChange={() => {
                      handleChange("local_stream", !participantCopy.local_stream);
                    }}
                  />
                  <Tooltip
                    showArrow
                    style={{ width: 300 }}
                    closeDelay={300}
                    radius={"sm"}
                    placement={"right"}
                    content="Enable local stream option to display the participant's own video stream"
                  >
                    <HelpOutlineOutlinedIcon />
                  </Tooltip>
                </Box>
              </Box>
              {/* Displays the list of filters available in the backend in a dropdown */}
              <FilterGroupDropdown
                selectedFilter={selectedFilter}
                selectedChatFilter={selectedChatFilter}
                handleFilterSelect={handleFilterSelect}
                handleSelectChatFilter={handleSelectChatFilter}
              />
              <Box>
                {/* Displays applied audio filters */}
                <FilterList
                  title="Audio Filters"
                  filterType="audio_filters"
                  filters={participantCopy.audio_filters}
                  handleFilterChange={handleFilterChange}
                  handleDelete={handleDeleteAudioFilter}
                />
                {/* Displays applied video filters */}
                <FilterList
                  title="Video Filters"
                  filterType="video_filters"
                  filters={participantCopy.video_filters}
                  handleFilterChange={handleFilterChange}
                  handleDelete={handleDeleteVideoFilter}
                />
                {/* Displays applied group audio filters */}
                <FilterList
                  title="Group Audio Filters"
                  filterType="audio_filters"
                  filters={participantCopy.audio_group_filters}
                  handleFilterChange={handleFilterChange}
                  handleDelete={handleDeleteAudioFilter}
                />
                {/* Displays applied group video filters */}
                <FilterList
                  title="Group Video Filters"
                  filterType="video_filters"
                  filters={participantCopy.video_group_filters}
                  handleFilterChange={handleFilterChange}
                  handleDelete={handleDeleteVideoFilter}
                />
                {/* Displays applied chat filters */}
                <FilterList
                  title="Chat Filters"
                  filterType="chat_filters"
                  filters={participantCopy.chat_filters}
                  handleFilterChange={handleFilterChange}
                  handleDelete={handleDeleteChatFilter}
                />
              </Box>
            </Grid>
            <Grid item xs={8}>
              <Tabs value={activeTab} onChange={(event, value) => setActiveTab(value)}>
                <Tab label={"Asymmetric Canvas"} />
                <Tab label={"Asymmetric Filters"} />
              </Tabs>
              {activeTab === ParticipantDataModalTab.AsymmetricCanvas && (
                <Grid container direction="column" justifyContent="center">
                  <FormControlLabel
                    control={<Switch />}
                    checked={asymmetricView.length > 0}
                    onChange={(event) => {
                      const isChecked = (event.target as HTMLInputElement).checked;

                      isChecked ? setAsymmetricView(originalDimensions) : setAsymmetricView([]);
                    }}
                    label="Asymmetric View"
                  />
                  {asymmetricView.length > 0 && (
                    <DragAndDrop
                      participantDimensions={asymmetricView}
                      setParticipantDimensions={setAsymmetricView}
                      asymmetricView={true}
                    />
                  )}
                </Grid>
              )}
              {activeTab === ParticipantDataModalTab.AsymmetricFilters && (
                <Grid container direction="column" justifyContent="center">
                  <Grid container alignItems="center">
                    <FormControlLabel
                      disabled={isAsymmetricFiltersDisabled}
                      control={<Switch />}
                      checked={asymmetricFilters.length > 0}
                      onChange={(event) => {
                        const isChecked = (event.target as HTMLInputElement).checked;
                        if (isChecked) {
                          setAsymmetricFilters(
                            getAsymmetricFiltersArray(
                              originalIdentifiers,
                              originalParticipant?.asymmetric_filters_id
                            )
                          );
                        } else {
                          setAsymmetricFilters([]);
                          setSelectedAsymmetricFilters([]);
                        }
                      }}
                      label="Asymmetric Filters"
                    />
                    {isAsymmetricFiltersDisabled && (
                      <Tooltip
                        showArrow
                        style={{ width: 300 }}
                        closeDelay={300}
                        radius={"sm"}
                        placement={"bottom"}
                        content="To enable asymmetric filters, please ensure that the experiment includes at least two participants."
                      >
                        <InfoOutlinedIcon color={"info"} />
                      </Tooltip>
                    )}
                  </Grid>

                  <Grid>
                    {asymmetricFilters.length > 0 &&
                      asymmetricFilters.map((a) => {
                        return (
                          <Box
                            key={a.id}
                            sx={{
                              width: 800,
                              marginBottom: 2,
                              padding: 2,
                              borderRadius: 1,
                              borderWidth: 1,
                              bgcolor: "#fcfcfc"
                            }}
                          >
                            <div>{a.participant_name}</div>
                            <FilterGroupDropdown
                              asymmetricFiltersId={a.id}
                              selectedFilter={
                                selectedAsymmetricFilters.find((f) => f.id === a.id)?.filter ||
                                defaultFilter
                              }
                              handleFilterSelect={handleFilterSelect}
                            />
                            <Box>
                              {/* Displays applied audio filters */}
                              <FilterList
                                asymmetricFilterId={a.id}
                                title="Audio Filters"
                                filterType="audio_filters"
                                filters={
                                  participantCopy.asymmetric_filters.find(
                                    (item) => item.id === a.id
                                  )?.audio_filters
                                }
                                handleFilterChange={handleFilterChange}
                                handleDelete={handleDeleteAudioFilter}
                              />
                              {/* Displays applied video filters */}
                              <FilterList
                                asymmetricFilterId={a.id}
                                title="Video Filters"
                                filterType="video_filters"
                                filters={
                                  participantCopy.asymmetric_filters.find(
                                    (item) => item.id === a.id
                                  )?.video_filters
                                }
                                handleFilterChange={handleFilterChange}
                                handleDelete={handleDeleteVideoFilter}
                              />
                            </Box>
                          </Box>
                        );
                      })}
                  </Grid>
                </Grid>
              )}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ alignSelf: "center" }}>
          <ActionButton
            text="CANCEL"
            variant="contained"
            color="error"
            size="medium"
            onClick={() => onCloseModalWithoutData()}
          />
          <ActionButton
            text="SAVE"
            variant="contained"
            color="success"
            size="medium"
            onClick={() => onSaveParticipantData()}
          />
        </DialogActions>
      </Dialog>
    </>
  );
}

export default ParticipantDataModal;
