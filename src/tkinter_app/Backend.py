import logging
from tkinter.ttk import Combobox

from src.bot.BotManager import BotManager, HandlerConfig
from src.event_receiver.EventReceivingService import EventReceivingService


class TkinterApp:
    def __init__(self, am: BotManager, targetids: list[str], event_receiver: EventReceivingService):
        self._am: BotManager = am
        self._targetids = targetids
        self._event_receiver: EventReceivingService = event_receiver

        self._current_target: str | None = None
        self._count_of_messages: int = 50
        self._combobox: Combobox | None = None
        self._combobox1: Combobox | None = None

    @property
    def handlers_states(self):
        return self._am.handlers_states

    def bind_comboboxes(self, combobox: Combobox, combobox1: Combobox) -> None:
        self._combobox = combobox
        self._combobox1 = combobox1

    def selected(self, event=None) -> None:
        if not self._combobox:
            logging.warning("Combobox ещё не инициализирован")
            return
        self._current_target = self._combobox.get().split()[0]
        logging.info(f'Выбран {self._current_target}')

    def set_count_of_messages(self, event=None) -> None:
        if not self._combobox1:
            logging.warning("Combobox1 ещё не инициализирован")
            return
        self._count_of_messages = int(self._combobox1.get())
        logging.info(f'Установлено {self._count_of_messages} как количество сообщений для дампа.')

    def start(self, config: HandlerConfig) -> None:
        queue = self._am.create_target_handler(config)
        self._event_receiver.add_container(config.targetid, queue)

    def stop(self) -> None:
        if not self._current_target:
            logging.warning("Не выбран целевой пользователь!")
            return
        self._am.terminate_handler([self._current_target])

    def stop_all(self) -> None:
        self._am.terminate_handler(self._targetids)

    def dump_dialog(self) -> None:
        if not self._current_target:
            logging.warning("Не выбран целевой пользователь!")
            return
        self._am.api.dump_dialog(self._current_target, self._count_of_messages)