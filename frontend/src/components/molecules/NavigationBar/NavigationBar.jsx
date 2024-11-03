import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Stack from "@mui/material/Stack";
import { styled } from "@mui/material/styles";
import { ActionButton } from "../../atoms/Button";

const GreyToolbar = styled(Toolbar)(() => ({
  backgroundColor: "#899499"
}));

// This is the toolbar view for the experimenter, with navigation links to session overview,
// and the post processing room. It is intentionally not displayed in the session form screen
// and experiment overview to prevent multiple navigation possibilities.
function NavigationBar() {
  return (
    <>
      <AppBar position="static">
        <GreyToolbar>
          <Stack direction="row">
            <ActionButton text={"Session Overview"} path={"/"} variant="string" size="large" />
            <ActionButton
              text={"Post-Processing Room"}
              path={"/postProcessingRoom"}
              variant="string"
              size="large"
            />
          </Stack>
        </GreyToolbar>
      </AppBar>
    </>
  );
}

export default NavigationBar;
