import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import Grid from "@mui/material/Grid";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Alert from "@mui/material/Alert";
import { useEffect, useState } from "react";
import ConnectionState from "../../networking/ConnectionState";
import { Button, IconButton } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import Tooltip from "@mui/material/Tooltip";
import { useAppSelector } from "../../redux/hooks";
import { selectFiltersDataSession } from "../../redux/slices/openSessionSlice";
import ListSubheader from "@mui/material/ListSubheader";
import CircularProgress from "@mui/material/CircularProgress";

function PostProcessing({
  status,
  recordings,
  connection,
  connectionState,
  errorMessage,
  successMessage,
  onPostProcessingVideo,
  onCheckPostProcessing,
  onGetRecordingList,
  onGetFiltersConfig,
  onApplyFiltersToVideos,
  onProcessingComplete
}) {
  const [selectedSession, setSelectedSession] = useState("");
  const [selectedVideos, setSelectedVideos] = useState([]);
  const [selectedFilters, setSelectedFilters] = useState([{ filter: null, videos: [] }]);
  const [totalSelectedVideos, setTotalSelectedVideos] = useState(0);
  const MAX_VIDEOS = 5;
  const [isProcessing, setIsProcessing] = useState(false);
  const [loop, setLoop] = useState(null);
  const [videos, setVideos] = useState([]);
  const filtersData = useAppSelector(selectFiltersDataSession);
  const individualFilters = filtersData.filter((filter) => filter.groupFilter !== true);
  console.log("Filters Data:", filtersData); // Add this line to check filters data
  const groupFilters = filtersData.filter((filter) => filter.groupFilter === true);
  const [requiredFilters, setRequiredFilters] = useState(new Map());

  useEffect(() => {
    onGetFiltersConfig();
  }, []);
  useEffect(() => {
    if (connection && connectionState === ConnectionState.CONNECTED) {
      onGetRecordingList();
      onCheckPostProcessing();
    }
  }, [connection, connectionState]);

  useEffect(() => {
    if (status) {
      setIsProcessing(status.is_processing);
    }
  }, [status]);

  useEffect(() => {
    if (status && status.is_processing && !loop) {
      setLoop(
        setInterval(() => {
          onCheckPostProcessing();
        }, 10000)
      );
    } else {
      if (status && !status.is_processing && loop) {
        clearInterval(loop);
        setLoop(null);
      }
    }
  }, [status]);

  useEffect(() => {
    const handleVideoList = (data) => {
      console.log("[EventHandler] Received VIDEO_LIST with data:", data);
      setVideos(data.videos || []);
    };

    if (connection && connection.api) {
      connection.api.on("VIDEO_LIST", handleVideoList);
    } else {
      console.error("Connection or connection.api is not defined.");
    }

    return () => {
      if (connection && connection.api) {
        connection.api.off("VIDEO_LIST", handleVideoList);
        console.log("Removing VIDEO_LIST listener");
      }
    };
  }, [connection, selectedSession]); // Ensure useEffect re-runs if connection or selectedSession changes

  useEffect(() => {
    if (onProcessingComplete) {
      setIsProcessing(false);
    }
  }, [onProcessingComplete]);

  const handleSelectSession = (session_id) => {
    setSelectedSession(session_id);
    if (session_id && connection) {
      connection.sendMessage("GET_VIDEO_LIST", { session_id });
    }
    setSelectedVideos([]);
  };

  const handleSelectFilter = (index, event) => {
    const filterId = event.target.value;
    const filter = filtersData.find((f) => f.id === filterId);
    if (!filter) {
      console.warn("No filter found with the given ID:", filterId);
      return;
    }

    const newSelectedFilters = [...selectedFilters];
    newSelectedFilters[index] = { ...newSelectedFilters[index], filter };
    setSelectedFilters(newSelectedFilters);
  };

  const handleSelectVideo = (index, videoId) => {
    const newSelectedFilters = [...selectedFilters];

    if (!newSelectedFilters[index].videos.includes(videoId)) {
      const currentTotal = newSelectedFilters.reduce(
        (total, filter) => total + filter.videos.length,
        0
      );
      if (currentTotal < MAX_VIDEOS) {
        newSelectedFilters[index].videos = [videoId];
        setSelectedFilters(newSelectedFilters);
        setTotalSelectedVideos(currentTotal + 1);
      } else {
        alert(`You can only select up to ${MAX_VIDEOS} videos.`);
      }
    }
  };

  const handleSelectGroupVideos = (index, videoId, videoIndex) => {
    const newSelectedFilters = [...selectedFilters];
    const videos = [...newSelectedFilters[index].videos];

    if (!videos.includes(videoId)) {
      const currentTotal = newSelectedFilters.reduce(
        (total, filter) => total + filter.videos.length,
        0
      );

      if (currentTotal < MAX_VIDEOS) {
        videos[videoIndex] = videoId;
        newSelectedFilters[index].videos = videos;
        setSelectedFilters(newSelectedFilters);
        setTotalSelectedVideos(currentTotal + 1);
      } else {
        alert(`You can only select up to ${MAX_VIDEOS} videos.`);
      }
    }
  };

  const onClickExtract = () => {
    if (connection) {
      onPostProcessingVideo(selectedSession);
      onCheckPostProcessing();
    }
  };

  const onClickApplyFilter = () => {
    const filterRequests = [];

    selectedFilters.forEach(({ filter, videos }) => {
      if (filter.groupFilter && videos.length !== 2) {
        alert("Please select two videos for group filter.");
        return;
      }
      if (!filter.groupFilter && videos.length !== 1) {
        alert("Please select one video.");
        return;
      }

      filterRequests.push({
        filter: filter,
        videos: videos
      });
    });

    setIsProcessing(true);

    onApplyFiltersToVideos(selectedSession, filterRequests);
  };

  const addFilterSelection = () => {
    setSelectedFilters([...selectedFilters, { filter: null, videos: [] }]);
  };

  const removeFilterSelection = (index) => {
    const videosToRemove = selectedFilters[index].videos.length;
    const newSelectedFilters = selectedFilters.filter((_, i) => i !== index);
    setTotalSelectedVideos(totalSelectedVideos - videosToRemove);
    setSelectedFilters(newSelectedFilters);
  };
  return (
    <Box className="flex flex-col items-start h-full p-4">
      <Grid container spacing={2} sx={{ flexWrap: "nowrap" }}>
        <Grid item>
          <FormControl fullWidth>
            <InputLabel>Sessions</InputLabel>
            <Select
              value={selectedSession}
              label="Sessions"
              onChange={(e) => handleSelectSession(e.target.value)}
              sx={{ width: "200px" }}
            >
              {recordings.map((session) => (
                <MenuItem key={session.session_id} value={session.session_id}>
                  {session.session_title} ({session.session_id})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {isProcessing ? (
        // Show processing icon when isProcessing is true
        <Box className="mt-4" display="flex" flexDirection="column" alignItems="center">
          <Typography variant="h6">Processing...</Typography>
          <CircularProgress />
        </Box>
      ) : (
        // Render the existing UI when not processing
        <Box className="mt-4">
          {/* ... [Your existing UI components] ... */}

          {/* Selected Videos Count and Add Filter Button */}
          <Box display="flex" alignItems="center" justifyContent="space-between" mt={2} mb={2}>
            <Typography variant="body1">
              {`Selected Videos: ${totalSelectedVideos}/${MAX_VIDEOS}`}
            </Typography>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<AddIcon />}
              onClick={addFilterSelection}
              disabled={totalSelectedVideos >= MAX_VIDEOS}
            >
              Add Filter
            </Button>
          </Box>

          {/* Dynamic Filter Selection */}
          {selectedFilters.map((filterObj, index) => (
            <Box key={index} mb={3}>
              <Grid container spacing={2} alignItems="flex-start">
                <Grid item xs={5}>
                  <FormControl fullWidth>
                    <InputLabel>Filters</InputLabel>
                    <Select
                      value={filterObj.filter ? filterObj.filter.id : ""}
                      label="Filters"
                      onChange={(e) => handleSelectFilter(index, e)}
                      sx={{ width: "100%" }}
                    >
                      <ListSubheader>Standard Filters</ListSubheader>
                      {individualFilters.map((filter) => (
                        <MenuItem key={filter.id} value={filter.id}>
                          {filter.name}
                        </MenuItem>
                      ))}

                      <ListSubheader>Group Filters</ListSubheader>
                      {groupFilters.map((filter) => (
                        <MenuItem key={filter.id} value={filter.id}>
                          {filter.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                {/* Video Selection Based on Filter Type */}
                {filterObj.filter && (
                  <>
                    {filterObj.filter.groupFilter ? (
                      <>
                        <Grid item xs={3}>
                          <FormControl fullWidth sx={{ minWidth: 150 }}>
                            <InputLabel>Select First Video</InputLabel>
                            <Select
                              label="Select First Video"
                              value={filterObj.videos[0] || ""}
                              onChange={(e) => handleSelectGroupVideos(index, e.target.value, 0)}
                            >
                              {videos.map((video) => (
                                <MenuItem key={video} value={video}>
                                  {video}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={3}>
                          <FormControl fullWidth sx={{ minWidth: 150 }}>
                            <InputLabel>Select Second Video</InputLabel>
                            <Select
                              label="Select Second Video"
                              value={filterObj.videos[1] || ""}
                              onChange={(e) => handleSelectGroupVideos(index, e.target.value, 1)}
                            >
                              {videos.map((video) => (
                                <MenuItem key={video} value={video}>
                                  {video}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                      </>
                    ) : (
                      <Grid item xs={6}>
                        <FormControl fullWidth sx={{ minWidth: 200 }}>
                          <InputLabel>Select Video</InputLabel>
                          <Select
                            label="Select Video"
                            value={filterObj.videos[0] || ""}
                            onChange={(e) => handleSelectVideo(index, e.target.value)}
                          >
                            {videos.map((video) => (
                              <MenuItem key={video} value={video}>
                                <Tooltip title={video}>
                                  <Typography
                                    variant="body1"
                                    sx={{ whiteSpace: "normal", wordBreak: "break-word" }}
                                  >
                                    {video}
                                  </Typography>
                                </Tooltip>
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                    )}
                  </>
                )}

                <Grid item xs={1}>
                  <IconButton
                    color="secondary"
                    onClick={() => removeFilterSelection(index)}
                    disabled={selectedFilters.length === 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Grid>
              </Grid>
            </Box>
          ))}

          {/* Apply Filters Button */}
          <Grid item xs={12} sx={{ mt: 4 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={onClickApplyFilter}
              disabled={
                selectedFilters.length === 0 || selectedFilters.some((f) => f.filter === null)
              }
            >
              Apply Filters
            </Button>
          </Grid>

          {/* Error and Success Messages */}
          {errorMessage && (
            <Grid item xs={12} sx={{ mt: 2 }}>
              <Alert severity="error">{errorMessage}</Alert>
            </Grid>
          )}
          {successMessage && (
            <Grid item xs={12} sx={{ mt: 2 }}>
              <Alert severity="success">{successMessage}</Alert>
            </Grid>
          )}
        </Box>
      )}
    </Box>
  );
}

export default PostProcessing;
