"""Provide the `Config` class."""


from typing import Literal

import json
from os.path import join, exists
from hub import BACKEND_DIR


class Config:
    """Config for experimental hub backend."""

    experimenter_password: str
    host: str
    port: int
    environment: Literal["dev", "prod"]
    serve_frontend: bool
    https: bool
    ssl_cert: str | None
    ssl_key: str | None

    log: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
    log_file: str | None
    log_dependencies: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]

    ping_subprocesses: int
    experimenter_multiprocessing: bool
    participant_multiprocessing: bool
    post_processing: dict

    open_face_type: str

    def __init__(self):
        """Load config from `backend/config.json`.

        Raises
        ------
        ValueError
            If a key in `backend/config.json` is missing or has the wrong type.
        FileNotFoundError
            If one of the files refereed to by ssl_cert or ssl_key is not found.
        """
        config_path = join(BACKEND_DIR, "config.json")
        config = json.load(open(config_path))

        # Check if keys exist and types are correct.
        data_types = {
            "experimenter_password": str,
            "host": str,
            "port": int,
            "environment": str,  # Literal not supported here, check afterwards.
            "serve_frontend": bool,
            "https": bool,
            "log": str,
            "log_dependencies": str,
            "ping_subprocesses": int,
            "experimenter_multiprocessing": bool,
            "participant_multiprocessing": bool,
            "post_processing": dict,
            "open_face_type": str
        }
        for key in data_types:
            if key not in config:
                raise ValueError(
                    f"{key} with type {data_types[key]} is missing in config.json."
                )
            if not isinstance(config[key], data_types[key]):
                raise ValueError(
                    f"{key} must be of type {data_types[key]} in config.json."
                )

        # Special data checks.
        if config["environment"] not in ["dev", "prod"]:
            raise ValueError("'environment' must be 'dev' or 'prod' in config.json.")

        valid_log_levels = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
        if config["log"] not in valid_log_levels:
            raise ValueError(f'"log" must be one of: {valid_log_levels}')

        if config["log_dependencies"] not in valid_log_levels:
            raise ValueError(f'"log_dependencies" must be one of: {valid_log_levels}')

        # Load config into this class.
        self.experimenter_password = config["experimenter_password"]
        self.host = config["host"]
        self.port = config["port"]
        self.environment = config["environment"]
        self.serve_frontend = config["serve_frontend"]
        self.https = config["https"]
        self.log = config["log"]
        self.log_dependencies = config["log_dependencies"]
        self.ping_subprocesses = config["ping_subprocesses"]
        self.experimenter_multiprocessing = config["experimenter_multiprocessing"]
        self.participant_multiprocessing = config["participant_multiprocessing"]
        self.post_processing = config["post_processing"]

        # Parse open_face_type
        self.open_face_type = config["open_face_type"]
        if self.open_face_type is not None:
            self.open_face_type = "subprocess"
        # Parse log_file
        self.log_file = config.get("log_file")
        if self.log_file is not None:
            self.log_file = join(BACKEND_DIR, self.log_file)

        # Parse ssl_cert and ssl_key
        self.ssl_cert = config.get("ssl_cert")
        if self.ssl_cert is not None:
            self.ssl_cert = join(BACKEND_DIR, self.ssl_cert)

        self.ssl_key = config.get("ssl_key")
        if self.ssl_key is not None:
            self.ssl_key = join(BACKEND_DIR, config["ssl_key"])

        # Check ssl_cert and ssl_key if https is true
        if self.https:
            if self.ssl_cert is None or self.ssl_key is None:
                raise ValueError("ssl_cert and ssl_key are required for https.")
            if not exists(self.ssl_cert):
                raise FileNotFoundError(f"Did not find ssl_cert file: {self.ssl_cert}")
            if not exists(self.ssl_key):
                raise FileNotFoundError(f"Did not find ssl_key file: {self.ssl_key}")

    def __str__(self) -> str:
        """Get string representation of parameters in this Config."""
        return (
            f"host={self.host}, port={self.port}, environment={self.environment}, "
            f"https={self.https}, serve_frontend={self.serve_frontend}, ssl_cert="
            f"{self.ssl_cert}, ssl_key={self.ssl_key}, log={self.log}, log_dependencies"
            f"={self.log_dependencies}, log_file={self.log_file}, ping_subprocesses="
            f"{self.ping_subprocesses}, experimenter_multiprocessing="
            f"{self.experimenter_multiprocessing}, participant_multiprocessing="
            f"{self.participant_multiprocessing}, post_processing="
            f"{self.post_processing}, open_face_type="
            f"{self.open_face_type}."
        )

    def __repr__(self) -> str:
        """Get representation of this Config obj."""
        return f"Config({str(self)})"

