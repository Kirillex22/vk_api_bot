from abc import ABC, abstractmethod
import numpy as np

from src.bot.Mods import ActivityMode


class AbstractVkApiWrapper(ABC):
    @abstractmethod
    def dump_dialog(self, userid: str, count_of_messages: int = 200, basic_offset: int = 500) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_message(self, userid: str, text: str, ) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_reaction(self, targetid: str, msg_id: int, randomly: bool = True, reaction_range: np.ndarray[float] = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_activity(self, targetid: str, _random: bool = True, activity: ActivityMode = None) -> None:
        raise NotImplementedError