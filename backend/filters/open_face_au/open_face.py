from abc import ABC, abstractmethod

class OpenFace(ABC):
    """
    Abstract base class for OpenFace operations.
    """

    @abstractmethod
    def __init__(self, port: int):
        pass

    @abstractmethod
    def __del__(self):
        pass