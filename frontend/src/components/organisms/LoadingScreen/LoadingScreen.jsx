import LoadingIndicator from "../../molecules/LoadingIndicator/LoadingIndicator";
import { Link } from "@mui/material";

function LoadingScreen({ refreshTimeOut, connectionTimeOut }) {
  return refreshTimeOut ? (
    connectionTimeOut ? (
      <LoadingIndicator
        loading={false}
        text={
          <>
            <h1 className="pt-5">
              Hmm... This is taking a while, consider relaunching SynthARium.
            </h1>
            <h1>
              For more help, please see our{" "}
              <Link href="https://github.com/TUMFARSynchrony/SynthARium/wiki/FAQ" underline="hover">
                FAQ
              </Link>
              .
            </h1>
          </>
        }
      />
    ) : (
      <LoadingIndicator
        loading={true}
        text={
          <>
            <h1>Loading...</h1>
            <h1>
              Please refresh the tab. If the delay continues after refreshing, hang tight—your
              connection may be slow.
            </h1>
          </>
        }
      />
    )
  ) : (
    <LoadingIndicator loading={true} text={<h1>Loading...</h1>} />
  );
}

export default LoadingScreen;
