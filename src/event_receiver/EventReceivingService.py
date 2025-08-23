import logging
from queue import Queue
from typing import Dict, Any

from src.common.Events import UserActionEvent, AbstractEvent
from src.event_receiver.Exceptions import EventFilteringException, EventMappingException
from src.event_receiver.Mappers import map_raw_event_to_abstract_event, map_abstract_event_to_concrete_event
from src.common.Utils import EventFilters
from src.event_receiver.pollers.core.AbstractPoller import AbstractPoller


class EventReceivingService:
    def __init__(self,
        filters: EventFilters,
        token: str,
        vk_id: str,
        poller: AbstractPoller,
    ):
        self._filters: EventFilters = filters
        self._token: str = token
        self._vk_id: str = vk_id
        self._containers: Dict[str, Queue[UserActionEvent]] = {}
        self._poller: AbstractPoller = poller

    def add_container(self, userid: str, queue: Queue[UserActionEvent]) -> None:
        self._containers[userid] = queue

    def __call__(self) -> None:
        for response in self._poller.listen():
            try:
                raw_event: Dict[str, Any] = vars(response)
                abstract_event: AbstractEvent = map_raw_event_to_abstract_event(raw_event)
                filtered: AbstractEvent= self._filters.apply(abstract_event)
                concrete_event: UserActionEvent = map_abstract_event_to_concrete_event(filtered)

                if concrete_event.userid in self._containers:
                    self._containers[concrete_event.userid].put(concrete_event)

            except EventFilteringException as e:
                logging.debug(str(e))

            except EventMappingException as e:
                logging.debug(str(e))