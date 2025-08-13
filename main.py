import logging
from tkinter import *
from tkinter.ttk import Combobox
from typing import Dict, List

from src.AccountManager import AccountManager
from src.App import App
from src.Config import AppSettings
from src.answer_generators.impl.GigaChatAnswerGenerator import GigaChatAnswerGenerator, GigaModels

logging.basicConfig(
    level=logging.INFO,               # показывать INFO и выше
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)

config = AppSettings.from_yaml_file("config.yaml")

USERS: Dict[str, str] = config.users
VK_API_TOKEN: str = config.VK_API_TOKEN
USER_VK_ID: str = config.USER_VK_ID
GIGACHAT_API_TOKEN: str = config.GIGACHAT_API_TOKEN
USERS_IDS: List[str] = list(USERS.keys())

ANSWER_GENERATOR = GigaChatAnswerGenerator(
        GIGACHAT_API_TOKEN,
        GigaModels.GIGACHAT_2_PRO
)

ACCOUNT_MANAGER = AccountManager(USERS, VK_API_TOKEN, USER_VK_ID, ANSWER_GENERATOR)
ACCOUNT_MANAGER.auth()

APP = App(ACCOUNT_MANAGER, USERS_IDS)

COUNTS = [i*50 for i in range(1, 4, 1)]

def main():
    logging.info(f"Загружены цели: {USERS}")

    window = Tk()
    window.title("ChatBot for vk.com")
    window.geometry("800x600")

    frame = Frame(window, padx=20, pady=20)
    frame.pack(expand=True, fill="both")

    # Метки
    method_lbl = Label(frame, text="Set current target", font=("Arial", 14))
    method_lbl.grid(row=0, column=0, sticky="w", pady=5)

    method_lb2 = Label(frame, text="Choose dump size", font=("Arial", 14))
    method_lb2.grid(row=2, column=0, sticky="w", pady=5)

    # Комбобоксы
    combobox = Combobox(frame, values=USERS_IDS, width=40, state="readonly", font=("Arial", 12))
    combobox.grid(row=1, column=0, sticky="w", pady=5)
    combobox.set('Available targets')

    combobox1 = Combobox(frame, values=COUNTS, width=40, state="readonly", font=("Arial", 12))
    combobox1.grid(row=3, column=0, sticky="w", pady=5)
    combobox1.set('Available sizes')

    # Кнопки
    btn_font = ("Arial", 14)
    btn_padx = 10
    btn_pady = 10

    cal_btn = Button(frame, text='Execute', command=APP.start, font=btn_font, padx=btn_padx, pady=btn_pady)
    cal_btn.grid(row=5, column=0, sticky="ew", pady=5)

    stop_btn = Button(frame, text='Terminate for this person', command=APP.stop, font=btn_font, padx=btn_padx, pady=btn_pady)
    stop_btn.grid(row=6, column=0, sticky="ew", pady=5)

    stop_all_btn = Button(frame, text='Terminate for all', command=APP.stop_all, font=btn_font, padx=btn_padx, pady=btn_pady)
    stop_all_btn.grid(row=7, column=0, sticky="ew", pady=5)

    dump_btn = Button(frame, text='Dialog dump', command=APP.dump_dialog, font=btn_font, padx=btn_padx, pady=btn_pady)
    dump_btn.grid(row=8, column=0, sticky="ew", pady=5)

    exit_btn = Button(frame, text='Exit', command=window.destroy, font=btn_font, padx=btn_padx, pady=btn_pady)
    exit_btn.grid(row=9, column=0, sticky="ew", pady=5)

    # Привязка колбеков
    combobox.bind("<<ComboboxSelected>>", APP.selected)
    combobox1.bind("<<ComboboxSelected>>", APP.set_count_of_messages)
    APP.bind_comboboxes(combobox, combobox1)

    window.mainloop()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(e)
        input('press enter to exit')
