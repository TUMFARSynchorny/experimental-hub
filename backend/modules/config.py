"""Provide the `Config` class."""


from typing import Literal

import json
from os.path import join, exists
from modules import BACKEND_DIR


class Config:
    """Config for experimental hub backend."""

    host: str
    port: int
    environment: Literal["dev", "prod"]
    https: bool
    ssl_cert: str | None
    ssl_key: str | None

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
            "host": str,
            "port": int,
            "environment": str,  # Literal not supported here, check afterwards.
            "https": bool,
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

        # Load config into this class.
        self.host = config["host"]
        self.port = config["port"]
        self.environment = config["environment"]
        self.https = config["https"]

        # parse ssl_cert and ssl_key
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
                print(f"[Config] Did not find ssl_cert file: {self.ssl_cert}.")
                raise FileNotFoundError(f"{self.ssl_cert} not found")
            if not exists(self.ssl_key):
                print(f"[Config] Did not find ssl_key file: {self.ssl_key}.")
                raise FileNotFoundError(f"{self.ssl_key} not found")

        print(f"[Config] successfully loaded config: {str(self)}")

    def __str__(self) -> str:
        """Get string representation of parameters in this Config.

        Format: "host: <host>, port: <port>, environment: <environment>."
        """
        return (
            f"host: {self.host}, port: {self.port}, environment: {self.environment}, "
            f"ssl_cert: {self.ssl_cert}, ssl_key: {self.ssl_key}."
        )

    def __repr__(self) -> str:
        """Get representation of this Config obj.

        Format: "Config(host: <host>, port: <port>, environment: <environment>.)"
        """
        return f"Config({self.__str__})"
