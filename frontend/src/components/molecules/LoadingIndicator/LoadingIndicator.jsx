import { CircularProgress } from "@mui/material";

function LoadingIndicator({ loading, text }) {
  return (
    <div className="flex flex-col items-center pt-5">
      {loading ? <CircularProgress /> : null}
      {text}
    </div>
  );
}

export default LoadingIndicator;
