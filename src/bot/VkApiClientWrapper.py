import logging
import random
from typing import Dict, Any

import numpy as np
from vk_api import VkApi

from src.bot.Mods import ActivityMode, ACTIVITIES
from src.common.Utils import DialogCollector, random_value_gen


class VkApiClientWrapper:
    def __init__(self, token: str, targets: Dict[str, str]):
        self._api = VkApi(token=token).get_api()
        self._targets: Dict[str, str] = targets
        self._dialog_collector: DialogCollector = DialogCollector(self._targets)

    def dump_dialog(self, userid: str, count_of_messages: int = 200) -> None:
        current_offset = 0
        count_of_iters = int(count_of_messages / 200)
        if count_of_iters == 0:
            count_of_iters = 1

        general_payload: str = ""
        logging.info(f"Попытка дампа диалога для userid: {userid}, count: {count_of_messages}")
        for i in range(count_of_iters):
            messages: Dict[str, Any] = self._api.messages.getHistory(user_id=int(userid), count=200,
                                                                     offset=current_offset)
            payload: str = self._dialog_collector(messages)
            general_payload += payload
            current_offset += count_of_messages

        total: int = len(general_payload.split('\n'))
        filename: str = f"./dialogs_dumps/{userid}.dump"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(general_payload)

        logging.info(f"Записан дамп диалога размером {total} для {userid}:{self._targets[userid]} в файл {filename}")

    def send_message(self, userid: str, text: str, ) -> None:
        self._api.messages.send(user_id=int(userid), random_id='0', message=text)

    def send_reaction(self, targetid: str, conv_msg_id: int, randomly: bool = True, reaction_range: np.ndarray[float] = None) -> None:
        if randomly:
            if not random_value_gen(reaction_range):
                return

        react_id = random.randint(1, 16)
        self._api.messages.sendReaction(
            peer_id=int(targetid),
            cmid=conv_msg_id,
            reaction_id=react_id
        )

    def set_activity(self, targetid: str, _random: bool = True, activity: ActivityMode = None) -> None:
        if _random:
            self._api.messages.setActivity(
                user_id=int(targetid),
                type=random.choice(ACTIVITIES)
            )
        else:
            self._api.messages.setActivity(
                user_id=int(targetid),
                type=activity
            )