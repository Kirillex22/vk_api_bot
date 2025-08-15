import time
import threading
from dataclasses import dataclass

import numpy as np
import logging
from typing import List, Dict, Any, Tuple
from queue import Queue, Empty

from src.bot.Mods import BotActionMode, ActivityMode
from src.bot.VkApiClientWrapper import VkApiClientWrapper
from src.common.Events import UserActionEvent
from src.common.Utils import GeneratorLock, make_str_from_context, read_initial_context, typing_time
from src.answer_generators.core import BaseAnswerGenerator


@dataclass
class HandlerConfig:
    targetid: str
    delay_between_answers_seconds: int
    mode: Tuple[BotActionMode]
    min_chars_sec_typing: int = 3
    max_chars_sec_typing: int = 5
    penalty_scale: int = 5


class BotManager:
    def __init__(
            self,
            targets: Dict[str, str],
            token: str,
            vk_id: str,
            answer_generator: BaseAnswerGenerator,
            reaction_probability: float = 0.4
    ):
        self._targets: Dict[str, str] = targets
        self.api = VkApiClientWrapper(token, self._targets)
        self._vk_id: str = vk_id
        self._path_to_out = None
        self._handlers: Dict[str, List[bool | Any]] = {}
        self._reaction_probability = reaction_probability
        self._answer_generator: BaseAnswerGenerator = answer_generator
        self._generator_lock: bool = False

        if reaction_probability <= 0: 
            self.reaction_range = np.array([1])
        else: 
            self.reaction_range = np.arange(0, int(1/reaction_probability), 1)


    def _wait_and_get_answer_from_generator(self, targetid: str, text: str | None, context: str) -> str | None:
        logging.info(f"Заблокирован ли генератор: {self._generator_lock}")
        while self._generator_lock:
            logging.info("Поток ожидает освобождения генератора ответов...")
            time.sleep(0.5)

        logging.info(f"Генератор ответов свободен, занимает обработчик для {targetid}...")
        try:
            with GeneratorLock(self):
                response_for_user: str = self._answer_generator(text, context)
                return response_for_user

        except RuntimeError as e:
            logging.error(e)
            return None

    def _send_message(
            self,
            targetid: str,
            response: str,
            min_char_sec_typing: int,
            max_chars_sec_typing: int,
            delay_between_answers_seconds: int
    ) -> None:

        time.sleep(typing_time(response, min_char_sec_typing, max_chars_sec_typing))

        logging.info(f"Отправляем сообщение...")
        self.api.send_message(targetid, response)
        logging.info(f'Отправлено сообщение {response} пользователю {targetid}:{self._targets[targetid]}')

        time.sleep(delay_between_answers_seconds)

    def _start_conversation(self, cfg: HandlerConfig, queue: Queue[UserActionEvent]) -> None:
        targetid: str = cfg.targetid
        penalty_scale: float = cfg.penalty_scale
        modes: Tuple[BotActionMode] = cfg.mode
        min_chars_sec_typing: int = cfg.min_chars_sec_typing
        max_chars_sec_typing: int = cfg.max_chars_sec_typing
        delay_between_answers_seconds: int = cfg.delay_between_answers_seconds

        context: List[UserActionEvent] = []
        initial_context: str = read_initial_context(targetid)

        def calculate_penalty(_context: List[UserActionEvent], scale: float) -> float:
            _penalty: float = 0.0

            for _event in reversed(_context):
                if _event.from_me:
                    _penalty += 1
                else:
                    break

            return _penalty*scale

        while True:
            stop: bool = self._handlers[targetid][0]
            if stop:
                logging.info(f"Остановка обработчика для {targetid}:{self._targets[targetid]}")
                break

            try:
                event: UserActionEvent = queue.get(timeout=3)
            except Empty:
                if BotActionMode.DIALOG in modes:
                    penalty: float = calculate_penalty(context, penalty_scale)
                    logging.info(f"Штраф {penalty} секунд для {targetid}:{self._targets[targetid]} за спам.")
                    time.sleep(penalty)

                    response: str = self._wait_and_get_answer_from_generator(
                        targetid,
                        None,
                        make_str_from_context(context, self._targets[targetid]) if len(context) > 0 else initial_context,
                    )

                    self._send_message(targetid, response, min_chars_sec_typing, max_chars_sec_typing, delay_between_answers_seconds)
                continue

            if event.from_me:
                context.append(event)
                continue
            else:
                self.api.send_reaction(targetid, event.messageid)

            text: str = event.message
            logging.info(f"Проверка пакета сообщений длины {len(text)} от {targetid}")

            if BotActionMode.DIALOG in modes:
                self.api.set_activity(targetid, _random=False, activity=ActivityMode.TYPING)

                response: str = self._wait_and_get_answer_from_generator(
                    targetid,
                    text,
                    make_str_from_context(
                        context,
                        self._targets[targetid]
                    )
                )

                self._send_message(targetid, response, min_chars_sec_typing, max_chars_sec_typing, delay_between_answers_seconds)

            context.append(event)

        del self._handlers[targetid]
        logging.info(f"Обработчик для {targetid}:{self._targets[targetid]} успешно удален.")

    def create_target_handler(self, cfg: HandlerConfig) -> Queue[UserActionEvent]:
        queue = Queue()
        thread = threading.Thread(target=self._start_conversation, args=(cfg,queue,))
        self._handlers[cfg.targetid] = [False, thread]
        thread.start()
        logging.info(f'Добавлен и запущен обработчик для {cfg.targetid}:{self._targets[cfg.targetid]}')
        return queue

    def terminate_handler(self, targets: List[str]):
        for targetid in targets:
            if targetid not in self._handlers:
                continue
            self._handlers[targetid][0] = True
            logging.info(f'Послан сигнал остановки для {targetid}:{self._targets[targetid]}')
        



