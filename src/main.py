import logging
import threading

from typing import Dict, List

from src import PROJECT_ROOT
from src.bot.BotManager import BotManager
from src.bot.vk_api_wrappers.impl.VkApiWrapper import VkApiWrapper
from src.common.Events import EventType
from src.common.Utils import EventFilters
from src.answer_generators.impl.GigaChatAnswerGenerator import GigaChatAnswerGenerator, GigaModels
from src.config.App import AppSettings
from src.config.Logging import setup_logging
from src.event_receiver.EventReceivingService import EventReceivingService
from src.event_receiver.pollers.impl.VkApiPoller import VkApiPoller
from src.tkinter_app.Backend import TkinterApp
from src.tkinter_app.Frontend import start

setup_logging()

config = AppSettings.from_yaml_file(f"{PROJECT_ROOT}/config.yaml")

USERS: Dict[str, str] = config.users
VK_API_TOKEN: str = config.VK_API_TOKEN
USER_VK_ID: str = config.USER_VK_ID
GIGACHAT_API_TOKEN: str = config.GIGACHAT_API_TOKEN
USERS_IDS: List[str] = list(USERS.keys())

ANSWER_GENERATOR = GigaChatAnswerGenerator(
        GIGACHAT_API_TOKEN,
        GigaModels.GIGACHAT_2_PRO
)

VK_API_WRAPPER = VkApiWrapper(VK_API_TOKEN, USERS)
ACCOUNT_MANAGER = BotManager(USERS, USER_VK_ID, ANSWER_GENERATOR, VK_API_WRAPPER, 0.5)
EVENT_RECEIVER = EventReceivingService(
    EventFilters(
        [EventType.MESSAGE_NEW],
    ),
    VK_API_TOKEN,
    USER_VK_ID,
    VkApiPoller(VK_API_TOKEN)
)

EVENT_RECEIVING_TASK = threading.Thread(target=EVENT_RECEIVER.__call__, args=(), daemon=True)
EVENT_RECEIVING_TASK .start()

APP = TkinterApp(ACCOUNT_MANAGER, USERS_IDS, EVENT_RECEIVER)

COUNTS = [i*50 for i in range(1, 10, 1)]

logging.info(f"Загружены цели: {USERS}")

if __name__ == '__main__':
    try:
        start(APP, USERS, COUNTS)
    except Exception as e:
        logging.error(e)
        input('...')
