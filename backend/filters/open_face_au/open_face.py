import subprocess
import os
import logging


class OpenFace:
    """Class for running OpenFace as an external process."""

    _logger: logging.Logger
    _own_extractor: None
    _feature_extraction: None

    def __init__(self):
        self._logger = logging.getLogger(f"OpenFace")

    def run_feature_extraction(self, video_path: str, out_dir: str):
        try:
            self._feature_extraction = subprocess.Popen(
                [
                    os.path.join(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(
                                    os.path.dirname(
                                        os.path.dirname(os.path.abspath(__file__))
                                    )
                                )
                            )
                        ),
                        "build",
                        "bin",
                        "FeatureExtraction",
                    ),
                    "-f",
                    f"'{video_path}'",
                    "-out_dir",
                    f"'{out_dir}'",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except Exception as error:
            self._logger.error("Error running OpenFace. Video path: " + video_path + ", Out dir: " + out_dir
                               + ". Exception: " + error)

    #customize the OwnExtractor and port
    # differentiate between windows/unix/macOS
    def run_own_extractor(self, port: int):
        try:
            self._own_extractor = subprocess.Popen(
                [
                    os.path.join(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(
                                    os.path.dirname(
                                        os.path.dirname(os.path.abspath(__file__))
                                    )
                                )
                            )
                        ),
                        "build",
                        "bin",
                        "OwnExtractor",
                    ),
                    f"{port}",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except Exception as error:
            self._logger.error("Error running OwnExtractor. Port: " + port + ". Exception: " + error)

    def stop(self):
        try:
            self._own_extractor.terminate()
            self._feature_extraction.terminate()
        except Exception:
            self._own_extractor.kill()
            self._feature_extraction.kill()
            
    def __del__(self):
        try:
            self._own_extractor.terminate()
            self._feature_extraction.terminate()
        except Exception:
            self._own_extractor.kill()
            self._feature_extraction.kill()
