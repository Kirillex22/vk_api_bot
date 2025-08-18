from typing import Dict, Any

from vk_api.longpoll import VkEventType

from src.common.Events import AbstractEvent, EventType, UserActionEvent, NewMessageEvent
from src.event_receiver.Exceptions import EventMappingException


def map_raw_event_to_abstract_event(raw_event: Dict[str, Any]) -> AbstractEvent:
    userid: int | None = raw_event.pop('user_id', None)
    if userid is None:
        userid = raw_event.pop('peer_id', None)

    type_: VkEventType | None = raw_event.pop('type', None)

    if userid is None or type_ is None:
        raise EventMappingException(f'Неверный формат события {type_}')

    if type_ is VkEventType.MESSAGE_NEW:
        new_type_ = EventType.MESSAGE_NEW

    else:
        raise EventMappingException(f'Неверный формат события {type_}')

    return AbstractEvent(new_type_, str(userid), raw_event)


def map_abstract_event_to_concrete_event(event: AbstractEvent) -> UserActionEvent:
    if event.type_ == EventType.MESSAGE_NEW:
        return NewMessageEvent(event.attrs.get('from_me'), event.userid, event.attrs.get('text'), event.attrs.get("info"))
    else:
        raise EventMappingException('Неверный тип события.')