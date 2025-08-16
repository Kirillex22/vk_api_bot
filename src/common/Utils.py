import logging
import random
import numpy as np
from typing import List, Dict, Any
from dataclasses import dataclass

from src.common import PROJECT_ROOT
from src.common.Events import EventType, AbstractEvent, UserActionEvent
from src.event_receiver.Exceptions import EventFilteringException


class DialogCollector:
    def __init__(self, users: Dict[str, Any]):
        """
        :param users: Cловарь ID пользователя : Псевдоним
        """
        self._users = users

    def _get_first_post_text(self, data: dict) -> str:
        attachments = data.get('attachments', [])
        if not attachments:
            return ""
        first = attachments[0]
        if first.get('type') == 'wall':
            wall = first.get('wall', {})
            return wall.get('text', "")
        return ""

    def __call__(self, dialog_slice: Dict[str, Any], message_len_limit: int = 1000) -> str:
        """
        Собирает API-Ответ в строку в формате Псевдоним: Cообщение_1\n ... Псевдоним: Cообщение_N
        :param dialog_slice: Срез диалога
        :param message_len_limit: Максимальная длина одного сообщения (большие по длине отфильтруются)
        :return:
        """
        collected: str = ""
        for item in reversed(dialog_slice.get('items', [])):
            text: str | None = item.get('text')
            if text is None or len(text) <= 0:
                text: str = self._get_first_post_text(item)
            if text is not None and 0 < len(text) <= message_len_limit:
                userid: str = str(item.get('from_id'))
                username: str = self._users.get(userid)
                if username is None:
                    username: str = 'Ты'
                collected += f"{username}: {text}\n"

        return collected


@dataclass
class EventFilters:
    types: List[EventType] = None

    def apply(self, event: AbstractEvent) -> AbstractEvent:
        if event.type_ not in self.types:
            raise EventFilteringException(f'Событие не прошло фильтр.')

        return event


class GeneratorLock:
    def __init__(self, instance):
        self.instance = instance

    def __enter__(self):
        logging.info("Начата работа с LLM.")
        if getattr(self.instance, "_generator_lock", True):
            raise RuntimeError("Генератор уже запущен")
        self.instance._generator_lock = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.instance._generator_lock = False
        logging.info("Работа с LLM закончена.")


def read_initial_context(targetid: str) -> str:
    path_to_context = f"{PROJECT_ROOT}\\dialogs_dumps\\{targetid}.dump"
    with open(path_to_context, encoding="utf-8") as f:
        context: str = f.read()
        logging.info(f"Загружен контекст длиной {len(context.split('\n'))}")
        return context


def make_str_from_context(_context: List[UserActionEvent], username: str) -> str:
    result = ""
    for new_mes_event in _context:
        if new_mes_event.from_me:
            result += f"Ты: {new_mes_event.message}\n"
        else:
            result += f"{username}: {new_mes_event.message}\n"

    logging.info(f'Context: {result}')

    return result


def random_value_gen(reaction_range: np.ndarray) -> bool:
    return random.choice(reaction_range) == 0


def typing_time(message: str, min_speed: int, max_speed: int) -> float:
    """
    Расчет времени печатания сообщения.

    :param message: текст сообщения
    :param min_speed: минимальная скорость печати (знаков в секунду)
    :param max_speed: максимальная скорость печати (знаков в секунду)
    :return: время печати в секундах
    """
    if not message:
        return 0.0

    # Длина сообщения
    length = len(message)

    # Случайная скорость печати в диапазоне
    speed = random.uniform(min_speed, max_speed)

    # Время в секундах
    time_seconds = length / speed

    return round(time_seconds, 2)
