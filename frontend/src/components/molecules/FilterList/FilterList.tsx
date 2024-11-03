import React from "react";
import {
  Box,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Typography
} from "@mui/material";
import { ChatFilter, Filter, FilterConfigArray, FilterConfigNumber } from "../../../types";

interface FilterListProps {
  asymmetricFilterId?: string;
  title: string;
  filters: Filter[] | ChatFilter[];
  filterType: string;
  handleFilterChange: (
    index: number,
    configType: string,
    value: string | number,
    filterType: string,
    asymmetricFilterId?: string
  ) => void;
  handleDelete: (
    filter: Filter | ChatFilter,
    index: number,
    isGroupFilter: boolean,
    asymmetricFilterId?: string
  ) => void;
}

export const FilterList: React.FC<FilterListProps> = ({
  asymmetricFilterId,
  title,
  filterType,
  filters,
  handleFilterChange,
  handleDelete
}) => {
  return (
    <>
      {filters && filters.length !== 0 && (
        <Typography variant="overline" display="block">
          {title}
        </Typography>
      )}
      {filters?.map((filter, filterIndex) => (
        <Box key={filterIndex} sx={{ display: "flex", justifyContent: "flex-start" }}>
          <Box sx={{ minWidth: 140 }}>
            <Chip
              key={filterIndex}
              label={filter.name}
              variant="outlined"
              size="medium"
              color="secondary"
              onDelete={() =>
                handleDelete(
                  filter,
                  filterIndex,
                  "groupFilter" in filter && filter.groupFilter,
                  asymmetricFilterId
                )
              }
            />
          </Box>
          <Box sx={{ display: "flex", justifyContent: "flex-start", flexWrap: "wrap" }}>
            {Object.keys(filter.config).map((configType, configIndex) => {
              const config = filter.config[configType];
              if (Array.isArray(config.defaultValue)) {
                return (
                  <FormControl
                    key={configIndex}
                    sx={{ m: 1, width: "10vw", minWidth: 130 }}
                    size="small"
                  >
                    <InputLabel htmlFor="grouped-select">
                      {configType.charAt(0).toUpperCase() + configType.slice(1)}
                    </InputLabel>
                    <Select
                      value={
                        (config as FilterConfigArray).requiresOtherFilter
                          ? config.defaultValue[0]
                          : config.value
                      }
                      id="grouped-select"
                      onChange={(e) => {
                        handleFilterChange(
                          filterIndex,
                          configType,
                          e.target.value,
                          filterType,
                          asymmetricFilterId
                        );
                      }}
                    >
                      {config.defaultValue.map((value: string) => (
                        <MenuItem key={value} value={value}>
                          {value}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                );
              } else if (typeof config.defaultValue === "number") {
                return (
                  <TextField
                    key={configIndex}
                    label={configType.charAt(0).toUpperCase() + configType.slice(1)}
                    defaultValue={config.value}
                    InputProps={{
                      inputProps: {
                        min: (config as FilterConfigNumber).min,
                        max: (config as FilterConfigNumber).max,
                        step: (config as FilterConfigNumber).step
                      }
                    }}
                    type="number"
                    size="small"
                    sx={{ m: 1, width: "10vw", minWidth: 130 }}
                    onChange={(e) => {
                      handleFilterChange(
                        filterIndex,
                        configType,
                        parseInt(e.target.value),
                        filterType,
                        asymmetricFilterId
                      );
                    }}
                  />
                );
              }
            })}
          </Box>
        </Box>
      ))}
    </>
  );
};
