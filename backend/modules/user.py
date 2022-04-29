"""TODO document"""

from __future__ import annotations
from abc import ABC
from typing import Callable, Any

from custom_types.message import MessageDict
from custom_types.error import ErrorDict
from modules.exceptions import ErrorDictException
import modules.connection as _connection


class User(ABC):
    """TODO document"""

    id: str
    _connection: _connection.Connection
    _handlers: dict[str, list[Callable[[Any], MessageDict | None]]]

    def __init__(self, id: str):
        """TODO document"""
        self.id = id
        self._handlers = {}

    def set_connection(self, connection: _connection.Connection):
        """TODO document"""
        self._connection = connection

    def send(self, message: MessageDict):
        """TODO document"""
        self._connection.send(message)

    def disconnect(self):
        """TODO document"""
        pass

    def subscribe_to(self, user: User):
        """TODO document"""
        pass

    def set_muted(self, muted: bool):
        """TODO document"""
        pass

    def on(self, endpoint: str, handler: Callable[[Any], MessageDict | None]):
        """TODO document"""
        if endpoint in self._handlers.keys():
            self._handlers[endpoint].append(handler)
        else:
            self._handlers[endpoint] = [handler]

    def handle_message(self, message: MessageDict | Any):
        """TODO document"""

        endpoint = message["type"]
        handler_functions = self._handlers.get(endpoint, None)

        if handler_functions is None:
            print(f"[USER]: No handler for {endpoint} found.")
            return

        print(
            f"[USER]: Received {endpoint}. Calling {len(handler_functions)} handler(s)."
        )
        for handler in handler_functions:
            try:
                response = handler(message["data"])
            except ErrorDictException as err:
                response = err.error_message
            except Exception as err:
                print("[USER] INTERNAL SERVER ERROR:", err)
                err = ErrorDict(
                    type="INTERNAL_SERVER_ERROR",
                    code=500,
                    description="Internal server error.",
                )
                response = MessageDict(type="ERROR", data=err)

            if response is not None:
                self.send(response)
