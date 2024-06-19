import random 
import tkinter as tk
from tkinter import * 
from tkinter import messagebox
import asyncio
from tkinter.ttk import Combobox 
from src.account_manager import AccountManager
from src.instance import Instance
from src.data_getter import DataGetter
from src.answer_generator import AnswerGenerator
import pprint
import os
from dotenv import load_dotenv
load_dotenv()

#mainloop
def main():
    targets = DataGetter.targets_reader('data/targets.json')
    names = list(targets.keys())

    counts = [i*1000 for i in range(1, 21, 1)]

    pprint.pp(targets)

    token = os.getenv('VK_API_TOKEN')
    user_id = os.getenv('USER_VK_ID')
    print(token)

    am = AccountManager(targets, token, user_id)
    am.auth()

    gen = AnswerGenerator(random_word_probability = 0.1)
    am.answer_generator = gen.generate_response

    intce = Instance(am, names, gen)

    window = Tk()
    window.title("ChatBot for vk.com")
    window.geometry("800x600")

    frame = Frame(
        window,
        padx=10,
        pady=10
    )
    frame.pack(expand=True)

    cal_btn = Button(
        frame, 
        text='Execute',
        command=intce.start
    )
    cal_btn.grid(row=5, column=2)

    stop_btn = Button(
        frame, 
        text='Terminate for this person',
        command=intce.stop
    )
    stop_btn.grid(row=6, column=2)

    stop_all_btn = Button(
        frame, 
        text='Terminate for all',
        command=intce.stop_all
    )
    stop_all_btn.grid(row=7, column=2)

    dump_btn = Button(
        frame, 
        text='Dialog dump',
        command=intce.dump_dialog
    )
    dump_btn.grid(row=8, column=2)

    load_model_btn = Button(
        frame, 
        text='Fit model',
        command=intce.fit_model
    )
    load_model_btn.grid(row=9, column=2)

    pred_mode_btn = Button(
        frame, 
        text='Load model',
        command=intce.load_model
    )
    pred_mode_btn.grid(row=10, column=2)

    exit_btn = Button(
        frame, 
        text='Exit',
        command=window.destroy
    )
    exit_btn.grid(row=12, column=1)

    method_lbl = Label(
        frame,
        text="Set current target"
    )
    method_lbl.grid(row=1, column=1)

    method_lb2 = Label(
        frame,
        text="Choose dump size"
    )
    method_lb2.grid(row=3, column=1)

    combobox = Combobox(frame, values=names, width=30, state="readonly")
    combobox.grid(row=2, column=1)
    combobox.set('Available targets')
    combobox.bind("<<ComboboxSelected>>", intce.selected)
    intce.combobox = combobox


    combobox1 = Combobox(frame, values=counts, width=30, state="readonly")
    combobox1.grid(row=4, column=1)
    combobox1.set('Available sizes')
    combobox1.bind("<<ComboboxSelected>>", intce.set_count_of_messages)
    intce.combobox1 = combobox1

    window.mainloop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as inst:
        print(type(inst))
        print(inst)
        input('press enter to exit')
