import time
import threading
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
import logging
from typing import List, Dict, Any, Tuple
from queue import Queue

from src.bot.Mods import BotActionMode, ActivityMode
from src.bot.vk_api_wrappers.core.AbstractVkApiWrapper import AbstractVkApiWrapper
from src.common.Events import UserActionEvent
from src.common.Utils import GeneratorLock, make_str_from_context, read_initial_context, typing_time
from src.answer_generators.core import AbstractAnswerGenerator


WAIT_CYCLES_WITHOUT_EVENTS = 10


class BotStates(StrEnum):
    WAITING_FOR_EVENTS = 'Waiting for events...'
    ANSWERING_USER_MESSAGE = 'Answering user message...'
    IMITATING_TYPING = 'Imitating typing...'
    SENDING_MESSAGE_TO_USER = 'Sending message to user...'
    SETTING_REACTION_ON_MESSAGES = 'Setting reactions on messages...'
    BANNED_FOR_SPAM = 'Banned for spam (waiting penalty time)...'
    CANCELLED = 'Cancelled...'
    ERROR = 'Error...'


@dataclass
class HandlerConfig:
    targetid: str
    delay_between_answers_seconds: int
    mode: Tuple[BotActionMode]
    min_chars_sec_typing: int = 3
    max_chars_sec_typing: int = 5
    penalty_scale: int = 5
    rules: str = ""


class BotManager:
    def __init__(
            self,
            targets: Dict[str, str],
            vk_id: str,
            answer_generator: AbstractAnswerGenerator,
            api: AbstractVkApiWrapper,
            reaction_probability: float = 0.8
    ):
        self._targets: Dict[str, str] = targets
        self.api = api
        self._vk_id: str = vk_id
        self._path_to_out = None
        self._handlers: Dict[str, List[bool | Any]] = {}
        self._reaction_probability = reaction_probability
        self._answer_generator: AbstractAnswerGenerator = answer_generator
        self._generator_lock: bool = False

        if reaction_probability <= 0: 
            self.reaction_range = np.array([1])
        else: 
            self.reaction_range = np.arange(0, int(1/reaction_probability), 1)

    def update_state(self, targetid: str, state: str) -> None:
        self._handlers[targetid][2] = state

    @property
    def handlers_states(self) -> List[Dict[str, str | bool]]:
        result: List[Dict[str, str | bool]] = []

        for targetid in self._targets:
            if targetid not in self._handlers:
                result.append(
                    {
                        'id': targetid,
                        'name':self._targets[targetid],
                        'running': False,
                        'current_state': 'No state'
                    }
                )

            else:
                result.append(
                    {
                        'id': targetid,
                        'name':self._targets[targetid],
                        'running': not self._handlers[targetid][0],
                        'current_state': self._handlers[targetid][2]
                    }
                )

        return result

    def _wait_and_get_answer_from_generator(
        self,
        targetid: str,
        text: str | None,
        context: str,
        rules: str
    ) -> str | None:
        logging.info(f"Заблокирован ли генератор: {self._generator_lock}")

        self.update_state(targetid, BotStates.ANSWERING_USER_MESSAGE)

        while self._generator_lock:
            logging.info("Поток ожидает освобождения генератора ответов...")
            time.sleep(0.5)

        logging.info(f"Генератор ответов свободен, занимает обработчик для {targetid}...")
        try:
            with GeneratorLock(self):
                response_for_user: str = self._answer_generator(text, context, rules)
                return response_for_user

        except RuntimeError as e:
            logging.error(e)
            return None

    def _send_message(
        self,
        targetid: str,
        response: str,
        min_char_sec_typing: int,
        max_chars_sec_typing: int
    ) -> None:
        self.update_state(targetid, BotStates.IMITATING_TYPING)

        self.api.set_activity(targetid, False, ActivityMode.TYPING)
        time.sleep(typing_time(response, min_char_sec_typing, max_chars_sec_typing))

        self.update_state(targetid, BotStates.SENDING_MESSAGE_TO_USER)

        logging.info(f"Отправляем сообщение...")
        self.api.send_message(targetid, response)
        logging.info(f'Отправлено сообщение {response} пользователю {targetid}:{self._targets[targetid]}')

    def _start_conversation(self, cfg: HandlerConfig, queue: Queue[UserActionEvent]) -> None:
        targetid: str = cfg.targetid
        penalty_scale: float = cfg.penalty_scale
        modes: Tuple[BotActionMode] = cfg.mode
        min_chars_sec_typing: int = cfg.min_chars_sec_typing
        max_chars_sec_typing: int = cfg.max_chars_sec_typing
        delay_between_answers_seconds: int = cfg.delay_between_answers_seconds
        rules: str = cfg.rules

        context: List[UserActionEvent] = []
        starting_block = True
        cycles_without_events: int = 0

        try:
            initial_context: str = read_initial_context(targetid).replace("{", "{{").replace("}", "}}")
        except FileNotFoundError:
            self._handlers[targetid][0] = True


        def calculate_penalty(_context: List[UserActionEvent], scale: float) -> float:
            _penalty: float = 0.0

            for _event in reversed(_context):
                if _event.from_me:
                    _penalty += 1
                else:
                    break

            return _penalty*scale

        try:
            while True:
                self.update_state(targetid, BotStates.WAITING_FOR_EVENTS)

                stop: bool = self._handlers[targetid][0]
                if stop:
                    self.update_state(targetid, BotStates.CANCELLED)
                    logging.info(f"Остановка обработчика для {targetid}:{self._targets[targetid]}")
                    break

                batch: List[UserActionEvent] = []

                time.sleep(delay_between_answers_seconds)

                while not queue.empty():
                    event: UserActionEvent = queue.get_nowait()
                    batch.append(event)

                if len(batch) <= 0:
                    cycles_without_events += 1

                    if cycles_without_events >= WAIT_CYCLES_WITHOUT_EVENTS:
                        starting_block = False

                    if BotActionMode.DIALOG in modes and not starting_block:
                        penalty: float = calculate_penalty(context, penalty_scale)
                        logging.info(f"Штраф {penalty} секунд для {targetid}:{self._targets[targetid]} за спам.")
                        self.update_state(targetid, BotStates.BANNED_FOR_SPAM)
                        time.sleep(penalty)
                        starting_block = True

                        response: str = self._wait_and_get_answer_from_generator(
                            targetid,
                            None,
                            initial_context + make_str_from_context(context, self._targets[targetid]),
                            rules
                        )

                        self._send_message(
                            targetid,
                            response,
                            min_chars_sec_typing,
                            max_chars_sec_typing
                        )

                    continue

                if cycles_without_events > 0:
                    cycles_without_events -= 1

                if all(event.from_me for event in batch):
                    context += batch
                    continue

                if BotActionMode.REACTION in modes:
                    for event in batch:
                        self.update_state(targetid, BotStates.SETTING_REACTION_ON_MESSAGES)
                        if not event.from_me:
                            self.api.send_reaction(
                                targetid,
                                event.messageid,
                                True,
                                self.reaction_range
                            )

                text: str = "\n".join([event.message for event in batch if not event.from_me])

                logging.info(f"Проверка пакета сообщений длины {len(text)} от {targetid}")

                if BotActionMode.DIALOG in modes:
                    response: str = self._wait_and_get_answer_from_generator(
                        targetid,
                        text,
                        initial_context + make_str_from_context(
                            context,
                            self._targets[targetid]
                        ),
                        rules
                    )

                    self._send_message(
                        targetid,
                        response,
                        min_chars_sec_typing,
                        max_chars_sec_typing
                    )

                context += batch

        except Exception as e:
            logging.error(e)
            self.update_state(targetid, BotStates.ERROR)

        del self._handlers[targetid]
        logging.info(f"Обработчик для {targetid}:{self._targets[targetid]} успешно удален.")

    def create_target_handler(self, cfg: HandlerConfig) -> Queue[UserActionEvent]:
        queue = Queue()
        thread = threading.Thread(target=self._start_conversation, args=(cfg,queue,),  daemon=True)
        self._handlers[cfg.targetid] = [False, thread, 'Waiting for events...']
        thread.start()
        logging.info(f'Добавлен и запущен обработчик для {cfg.targetid}:{self._targets[cfg.targetid]}')
        return queue

    def terminate_handler(self, targets: List[str]):
        for targetid in targets:
            if targetid not in self._handlers:
                continue
            self._handlers[targetid][0] = True
            self.update_state(targetid, BotStates.CANCELLED)
            logging.info(f'Послан сигнал остановки для {targetid}:{self._targets[targetid]}')
        



