from dataclasses import dataclass
from enum import StrEnum
from typing import Dict, Any, Union


class EventType(StrEnum):
    MESSAGE_NEW = 'MESSAGE_NEW'


@dataclass
class AbstractEvent:
    type_: str
    userid: str
    attrs: Dict[str, Any]


@dataclass
class NewMessageEvent:
    from_me: bool
    userid: str
    message: str
    messageid: int


UserActionEvent = Union[NewMessageEvent]
