"""TODO document"""

from __future__ import annotations

from modules.connection import Connection


class User():
    """TODO document"""
    id: str
    connection: Connection

    def __init__(self):
        """TODO document"""
        pass

    def send(self, data):
        """TODO document"""
        pass

    def disconnect(self):
        """TODO document"""
        pass

    def subscribe_to(self, user: User):
        """TODO document"""
        pass

    def set_muted(self, muted: bool):
        """TODO document"""
        pass

    def handle_message(self, message):
        """TODO document"""
        pass
