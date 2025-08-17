from abc import ABC, abstractmethod

class AbstractAnswerGenerator(ABC):
    """
    Базовый класс генератора ответов
    """
    @abstractmethod
    def __call__(self, message: str, context: str) -> str:
        """
        :param message: Сообщения собеседника
        :param context: Размеченный контекст (диалог)
        :return: Ответ модели с учетом контекста
        """
        raise NotImplementedError