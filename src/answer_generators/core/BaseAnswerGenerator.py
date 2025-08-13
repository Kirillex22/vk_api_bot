from abc import ABC, abstractmethod
from typing import List

class BaseAnswerGenerator(ABC):
    """
    Базовый класс генератора ответов
    """
    @abstractmethod
    def __call__(self, messages: List[str], context: str) -> str:
        """
        :param messages: Сообщения собеседника
        :param context: Размеченный контекст (диалог)
        :return: Ответ модели с учетом контекста
        """
        raise NotImplementedError