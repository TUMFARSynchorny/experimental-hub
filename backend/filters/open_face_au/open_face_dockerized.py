import logging
import subprocess
import shlex 
import platform 

from filters.open_face_au.open_face_subprocess import OpenFace

class OpenFaceDockerized(OpenFace):
    """Class for running OpenFace as an external process."""

    container_name: str

    def __init__(self, port: int):
        try:
            self._logger = logging.getLogger("OpenFaceDockerized")
            self.container_name = f'openface-container-{port}'
            self._logger.debug(f"Create openface container for port:{port} container-name:{self.container_name}")
            
            command = f"docker run -it -d --name {self.container_name} -p {port}:5555 hhuseyinkacmaz/test2 /bin/sh -c \"./build/bin/AUExtractor 5555\""
            
            if platform.system() == 'Windows':
                command = shlex.split(command)
            
            self._openface_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                shell=True
            )
        except Exception as e:
            self._logger.error(f"OpenFace Error: {e}")

    def __del__(self):
        try:
            self._logger.debug(f"Trying to stop and remove the container, name:{self.container_name}")
            subprocess.Popen(
                [
                    f"docker rm -f {self.container_name}"
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                shell=True
            )
        except Exception as e:
            self._logger.error(f"OpenFace Deletion Error: {e}")