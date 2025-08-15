from typing import Generator

from vk_api import VkApi
from vk_api.longpoll import VkLongPoll

from src.event_receiver.pollers.core.AbstractPoller import AbstractPoller


class VkApiPoller(AbstractPoller):
    def __init__(self, token: str):
        self._poller = VkLongPoll(VkApi(token=token))

    def listen(self) -> Generator:
        return self._poller.listen()