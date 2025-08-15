from abc import ABC, abstractmethod
from typing import Generator


class AbstractPoller(ABC):
    @abstractmethod
    def listen(self) -> Generator:
        raise NotImplementedError