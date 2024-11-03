import Box from "@mui/material/Box";
import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import Select from "@mui/material/Select";
import ListSubheader from "@mui/material/ListSubheader";
import { ChatFilter, Filter } from "../../../types";
import MenuItem from "@mui/material/MenuItem";
import React from "react";
import { useAppSelector } from "../../../redux/hooks";
import { selectFiltersDataSession } from "../../../redux/slices/openSessionSlice";
import chatFiltersData from "../../../chat_filters.json";
import Alert from "@mui/material/Alert";

interface FilterGroupDropdownProps {
  asymmetricFiltersId?: string;
  selectedFilter: Filter;
  selectedChatFilter?: ChatFilter;
  handleFilterSelect: (
    filter: Filter,
    isGroupFilter: boolean,
    asymmetricFiltersId?: string
  ) => void;
  handleSelectChatFilter?: (chatFilter: ChatFilter) => void;
}

export const FilterGroupDropdown: React.FC<FilterGroupDropdownProps> = ({
  asymmetricFiltersId,
  selectedFilter,
  selectedChatFilter,
  handleFilterSelect,
  handleSelectChatFilter
}) => {
  const filtersData = useAppSelector(selectFiltersDataSession);
  const individualFilters = filtersData.filter((filter) => filter.groupFilter !== true);
  const groupFilters = filtersData.filter((filter) => filter.groupFilter === true);
  const chatFilters: ChatFilter[] = chatFiltersData.chat_filters.map((filter: ChatFilter) => {
    return filter;
  });

  return (
    <Box sx={{ display: "flex", justifyContent: "flex-start", gap: 2 }}>
      <Box sx={{ display: "flex", flexDirection: "column", justifyContent: "flex-start" }}>
        <FormControl sx={{ m: 1, minWidth: 180 }} size="small">
          <InputLabel id="filters-select">Filters</InputLabel>
          {
            <Select
              value={selectedFilter.name}
              id="filters-select"
              label="Filters"
              displayEmpty={true}
              renderValue={(selected) => {
                if (selected === "Placeholder") {
                  return <em>Select a Filter</em>;
                }
                return selected;
              }}
            >
              <ListSubheader sx={{ fontWeight: "bold", color: "black" }}>
                Individual Filters
              </ListSubheader>
              {/* Uncomment the below block to use new filters. */}
              {individualFilters.map((individualFilter: Filter) => {
                return (
                  <MenuItem
                    key={individualFilter.id}
                    value={individualFilter.name}
                    onClick={() =>
                      handleFilterSelect(
                        individualFilter,
                        individualFilter.groupFilter,
                        asymmetricFiltersId
                      )
                    }
                  >
                    {individualFilter.name}
                  </MenuItem>
                );
              })}
              <ListSubheader sx={{ fontWeight: "bold", color: "black" }}>
                Group Filters
              </ListSubheader>
              {groupFilters.map((groupFilter: Filter) => {
                return (
                  <MenuItem
                    key={groupFilter.id}
                    value={groupFilter.name}
                    onClick={() =>
                      handleFilterSelect(groupFilter, groupFilter.groupFilter, asymmetricFiltersId)
                    }
                  >
                    {groupFilter.name}
                  </MenuItem>
                );
              })}
            </Select>
          }
        </FormControl>
        <Alert severity="info" sx={{ padding: "2px 8px" }}>
          You can select each filter multiple times
        </Alert>
      </Box>

      {!asymmetricFiltersId && chatFilters && (
        <Box sx={{ display: "flex", justifyContent: "flex-start" }}>
          <FormControl sx={{ m: 1, minWidth: 180 }} size="small">
            <InputLabel id="filters-select">Chat Filters (BETA)</InputLabel>

            <Select
              value={selectedChatFilter.name}
              id="filters-select"
              label="Chat Filters (BETA)"
              displayEmpty={true}
              renderValue={(selected) => {
                if (selected === "Placeholder") {
                  return <em>Select a Chat Filter</em>;
                }
                return selected;
              }}
            >
              <ListSubheader sx={{ fontWeight: "bold", color: "black" }}>
                Individual Filters
              </ListSubheader>
              {chatFilters.map((chatFilter: ChatFilter) => {
                return (
                  <MenuItem
                    key={chatFilter.id}
                    value={chatFilter.name}
                    onClick={() => handleSelectChatFilter(chatFilter)}
                  >
                    {chatFilter.name}
                  </MenuItem>
                );
              })}
            </Select>
          </FormControl>
        </Box>
      )}
    </Box>
  );
};
