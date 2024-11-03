import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import styled from "@emotion/styled";
import CardActionArea from "@mui/material/CardActionArea";
import Stack from "@mui/material/Stack";
import { integerToDateTime } from "../../../utils/utils";
import {
  ongoingSessionCardBackgroundColor,
  ongoingSessionCardBorderColor,
  ongoingSessionCardHeaderColor,
  sessionCardBorderColor
} from "../../../styles/styles";

const GreySessionTitle = styled(Typography)(() => ({
  component: "div",
  variant: "subtitle1",
  color: "grey",
  fontWeight: "bold"
}));

const OngoingSessionTitle = styled(Typography)(() => ({
  component: "div",
  variant: "subtitle1",
  color: ongoingSessionCardHeaderColor,
  fontWeight: "bold"
}));

function SessionCard({ title, date, description, onClick, ongoing }) {
  return (
    <Card
      sx={{
        mt: 2,
        mb: 2,
        borderTop: ongoing ? ongoingSessionCardBorderColor : sessionCardBorderColor,
        backgroundColor: ongoing ? ongoingSessionCardBackgroundColor : "white"
      }}
    >
      <CardActionArea onClick={onClick}>
        <CardContent>
          <Stack spacing={1} sx={{ display: "block", textAlign: "left" }}>
            {ongoing ? (
              <OngoingSessionTitle>Ongoing:{title}</OngoingSessionTitle>
            ) : (
              <GreySessionTitle>{title}</GreySessionTitle>
            )}
            <Typography>{integerToDateTime(date)}</Typography>
            {/* Nowrap displays only one line of experiment description, rest is ... */}
            <Typography noWrap={true}>{description}</Typography>
          </Stack>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}

export default SessionCard;
