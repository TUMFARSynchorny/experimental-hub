import subprocess
import os


class OpenFace:
    def __init__(self, port: int):
        try:
            self._openface_process = subprocess.Popen(
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception:
            pass

    def __del__(self):
        try:
            self._openface_process.terminate()
        except Exception:
            self._openface_process.kill()
