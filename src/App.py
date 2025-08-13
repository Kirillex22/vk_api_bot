import logging
from tkinter.ttk import Combobox
from src.AccountManager import AccountManager

class App:
    def __init__(self, am: AccountManager, targetids: list[str]):
        self._am: AccountManager = am
        self._targetids = targetids

        # Инициализируем атрибуты
        self._current_target: str | None = None
        self._count_of_messages: int = 50
        self._combobox: Combobox | None = None
        self._combobox1: Combobox | None = None

    # Присваиваем комбобоксы
    def bind_comboboxes(self, combobox: Combobox, combobox1: Combobox) -> None:
        self._combobox = combobox
        self._combobox1 = combobox1

    # Колбэки
    def selected(self, event=None) -> None:
        if self._combobox is None:
            logging.warning("Combobox ещё не инициализирован")
            return
        self._current_target = self._combobox.get()
        logging.info(f'Выбран {self._current_target}')

    def set_count_of_messages(self, event=None) -> None:
        if self._combobox1 is None:
            logging.warning("Combobox1 ещё не инициализирован")
            return
        self._count_of_messages = int(self._combobox1.get())
        logging.info(f'Установлено {self._count_of_messages} как количество сообщений для дампа.')

    # Основные методы
    def start(self) -> None:
        if self._current_target is None:
            logging.warning("Не выбран целевой пользователь!")
            return
        self._am.create_target_handler(
            self._current_target,
            delay_between_answers_seconds=15,
            delay_limit_seconds=500,
            mode=['default', 'reaction']
        )

    def stop(self) -> None:
        if self._current_target is None:
            logging.warning("Не выбран целевой пользователь!")
            return
        self._am.terminate_handler([self._current_target])

    def stop_all(self) -> None:
        self._am.terminate_handler(self._targetids)

    def dump_dialog(self) -> None:
        if self._current_target is None:
            logging.warning("Не выбран целевой пользователь!")
            return
        self._am.dump_dialog(self._current_target, self._count_of_messages)