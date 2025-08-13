import vk_api
import time
import random
import threading
import numpy as np
import logging
from typing import List, Dict, Any
from pathlib import Path

from src.Utils import DialogCollector
from src.answer_generators.core import BaseAnswerGenerator


PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


class AccountManager:
    def __init__(
            self,
            targets: Dict[str, str],
            token: str,
            vk_id: str,
            answer_generator: BaseAnswerGenerator,
            reaction_probability: float = 0.4
    ):
        self._targets: Dict[str, str] = targets
        self._token: str = token
        self._vk_id: str = vk_id
        self._path_to_out = None
        self._api = None
        self._handlers: Dict[str, List[bool | Any]] = {}
        self._activities: List[str] = ["typing", "audiomessage", "photo", "videomessage"]
        self._reaction_probability = reaction_probability
        self._answer_generator: BaseAnswerGenerator = answer_generator
        self._dialog_collector: DialogCollector = DialogCollector(self._targets)
        self._generator_lock: bool = False

        if reaction_probability <= 0: 
            self.reaction_arange = np.array([1]) 
        else: 
            self.reaction_arange = np.arange(0, int(1/reaction_probability), 1)


    def __random_value_gen(self) -> bool:
        return random.choice(self.reaction_arange) == 0

    def auth(self) -> None:
        self._api = vk_api.VkApi(token = self._token).get_api()

    def _get_last_unhandled_messages(self, userid: str, delay_between_reactions: int = 1) -> List[str]:
        response: Dict = self._api.messages.getHistory(user_id = int(userid))
        messages: List[Dict] = response.get('items')

        corpus = []

        for message in messages:
            from_id: str = message.get('from_id')
            logging.info(f"Получено от {from_id}, сообщение: {message.get('text')}")
            if int(from_id) == int(self._vk_id): break

            if self.__random_value_gen():
                time.sleep(delay_between_reactions)
                self._send_reaction(userid, message.get('conversation_message_id'))

            corpus.append(message.get('text', ''))

        logging.info(f"Итоговое число необработанных сообщений: {len(corpus)}")
        corpus.reverse()
        return corpus

    def dump_dialog(self, userid: str, count_of_messages : int = 200) -> None:
        current_offset = 0
        count_of_iters = int(count_of_messages/200)
        if count_of_iters == 0:
            count_of_iters = 1

        general_payload: str = ""
        logging.info(f"Попытка дампа диалога для userid: {userid}, count: {count_of_messages}")
        for i in range(count_of_iters):
            messages: Dict[str, Any] = self._api.messages.getHistory(user_id = int(userid), count = 200, offset = current_offset)
            payload: str = self._dialog_collector(messages)
            general_payload += payload
            current_offset += count_of_messages

        total: int = len(general_payload.split('\n'))
        filename: str = f"./dialogs_dumps/{userid}.dump"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(general_payload)

        logging.info(f"Записан дамп диалога размером {total} для {userid}:{self._targets[userid]} в файл {filename}")

    def _send_message(self, userid: str, text:str,) -> None:
        self._api.messages.send(user_id = int(userid), random_id = '0', message = text)

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

    def _start_conversation(
            self,
            targetid: str,
            delay_between_answers_seconds: int,
            delay_limit_seconds: int,
            mode : tuple
    ) -> None:

        path_to_context = f"{PROJECT_ROOT}\\dialogs_dumps\\{targetid}.dump"

        with open(path_to_context, encoding="utf-8") as f:
            context: str = f.read()

        current_delay_capacity = 0
        is_attempted_to_start_conversation = False

        stop = False

        while not stop:
            if 'reaction' in mode:
                time.sleep(delay_between_answers_seconds)

            corpus: List[str] = self._get_last_unhandled_messages(targetid)
            text: str = "\n".join(corpus)

            if current_delay_capacity > delay_limit_seconds:
                break

            logging.info(f"Проверка пакета сообщений длины {len(corpus)} от {targetid}")
            if len(corpus) > 0:
                if 'default' in mode:
                    self._set_activity(targetid, mode = 'typing')
                    current_delay_capacity = 0

                    response: str = self._wait_and_get_answer_from_generator(targetid, text, context)
                    if response is None:
                        continue

                    logging.info(f"Отправляем сообщение...")
                    self._send_message(targetid, response)
                    logging.info(f'Отправлено сообщение {response} пользователю {targetid}:{self._targets[targetid]}')
                else:
                    is_attempted_to_start_conversation = False
                    continue
            else:
                if 'default' in mode and not is_attempted_to_start_conversation:
                    is_attempted_to_start_conversation = True
                    response: str = self._wait_and_get_answer_from_generator(targetid, None, context)
                    logging.info(f"Отправляем сообщение...")
                    self._send_message(targetid, response)
                    logging.info(f'Отправлено сообщение {response} пользователю {targetid}:{self._targets[targetid]}')

                time.sleep(delay_between_answers_seconds)
                current_delay_capacity += delay_between_answers_seconds

            stop = self._handlers[targetid][0]

        del self._handlers[targetid]
        logging.info(f"Обработчик для {targetid}:{self._targets[targetid]} успешно удален.")

    def _send_reaction(self, targetid: str, conv_msg_id: int):
        react_id = random.randint(1, 16)
        self._api.messages.sendReaction(
            peer_id = int(targetid),
            cmid = conv_msg_id,
            reaction_id = react_id
        )

    def _set_activity(self, targetid: str, mode = 'random'):
        if mode == 'random':
            self._api.messages.setActivity(
                user_id = int(targetid),
                type = random.choice(self._activities)
            )
        else:
            self._api.messages.setActivity(
                user_id = int(targetid),
                type = mode
            )

    def create_target_handler(self, targetid: str, delay_between_answers_seconds = 2, delay_limit_seconds = 60, mode = ('default', 'reaction')) -> None:
        thread = threading.Thread(target=self._start_conversation, args=(targetid, delay_between_answers_seconds, delay_limit_seconds, mode,))
        self._handlers[targetid] = [False, thread]
        thread.start()
        logging.info(f'Добавлен и запущен обработчик для {targetid}:{self._targets[targetid]}')

    def terminate_handler(self, targets: list):
        for targetid in targets:
            if targetid not in self._handlers:
                continue
            self._handlers[targetid][0] = True
            logging.info(f'Послан сигнал остановки для {targetid}:{self._targets[targetid]}')
        



