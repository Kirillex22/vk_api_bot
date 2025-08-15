from tkinter import Tk, Frame, Label, Button, StringVar, IntVar, Checkbutton, Entry
from tkinter.ttk import Combobox
from typing import Dict

from src.tkinter_app.backend import TkinterApp
from src.bot.Mods import BotActionMode
from src.tkinter_app.backend import HandlerConfig


def start(app: TkinterApp, targets: Dict[str, str], counts: list[int]) -> None:
    window = Tk()
    window.title("VK ChatBot Control Panel")
    window.geometry("900x650")
    window.configure(bg="#f4f6f8")

    frame = Frame(window, bg="#f4f6f8", padx=30, pady=30)
    frame.pack(expand=True, fill="both")

    Label(frame, text="🎯 VK ChatBot Control Panel", font=("Segoe UI", 20, "bold"), bg="#f4f6f8", fg="#333").grid(row=0, column=0, columnspan=2, pady=(0, 20))

    # Целевая аудитория
    Label(frame, text="Select target:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=1, column=0, sticky="w", pady=5)
    target_var = StringVar(value="Available targets")
    combobox_target = Combobox(frame, values=list(targets.keys()), width=40, textvariable=target_var, state="readonly", font=("Segoe UI", 12))
    combobox_target.grid(row=1, column=1, pady=5)

    # Размер дампа
    Label(frame, text="Dump size:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=2, column=0, sticky="w", pady=5)
    size_var = StringVar(value="Available sizes")
    combobox_size = Combobox(frame, values=counts, width=40, textvariable=size_var, state="readonly", font=("Segoe UI", 12))
    combobox_size.grid(row=2, column=1, pady=5)

    # Настройки задержки и печати
    Label(frame, text="Delay between answers (sec):", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=3, column=0, sticky="w", pady=5)
    delay_var = IntVar(value=5)
    Entry(frame, textvariable=delay_var, width=10, font=("Segoe UI", 12)).grid(row=3, column=1, sticky="w")

    Label(frame, text="Min chars/sec typing:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=4, column=0, sticky="w", pady=5)
    min_chars_var = IntVar(value=3)
    Entry(frame, textvariable=min_chars_var, width=10, font=("Segoe UI", 12)).grid(row=4, column=1, sticky="w")

    Label(frame, text="Max chars/sec typing:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=5, column=0, sticky="w", pady=5)
    max_chars_var = IntVar(value=5)
    Entry(frame, textvariable=max_chars_var, width=10, font=("Segoe UI", 12)).grid(row=5, column=1, sticky="w")

    Label(frame, text="Penalty scale:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=6, column=0, sticky="w", pady=5)
    penalty_var = IntVar(value=5)
    Entry(frame, textvariable=penalty_var, width=10, font=("Segoe UI", 12)).grid(row=6, column=1, sticky="w")

    # Режимы действий
    Label(frame, text="Select modes:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=7, column=0, sticky="w", pady=5)
    mode_dialog_var = IntVar(value=1)
    mode_reaction_var = IntVar(value=1)
    Checkbutton(frame, text="DIALOG", variable=mode_dialog_var, font=("Segoe UI", 12), bg="#f4f6f8").grid(row=7, column=1, sticky="w")
    Checkbutton(frame, text="REACTION", variable=mode_reaction_var, font=("Segoe UI", 12), bg="#f4f6f8").grid(row=8, column=1, sticky="w")

    button_pad_y = 8
    Button(frame, text='▶ Execute', command=lambda: app.start(
        HandlerConfig(
            targetid=targets[target_var.get()],  # получаем значение из словаря по ключу
            delay_between_answers_seconds=delay_var.get(),
            mode=[mode for m, mode in [(mode_dialog_var.get(), BotActionMode.DIALOG),
                                       (mode_reaction_var.get(), BotActionMode.REACTION)] if m],
            min_chars_sec_typing=min_chars_var.get(),
            max_chars_sec_typing=max_chars_var.get(),
            penalty_scale=penalty_var.get()
        )
    ), bg="#4caf50", fg="white", font=("Segoe UI", 12, "bold")).grid(row=9, column=0, columnspan=2, sticky="ew", pady=button_pad_y)

    Button(frame, text='⛔ Terminate for this person', command=app.stop, bg="#ff9800", fg="white", font=("Segoe UI", 12, "bold")).grid(row=10, column=0, columnspan=2, sticky="ew", pady=button_pad_y)
    Button(frame, text='🛑 Terminate for all', command=app.stop_all, bg="#f44336", fg="white", font=("Segoe UI", 12, "bold")).grid(row=11, column=0, columnspan=2, sticky="ew", pady=button_pad_y)
    Button(frame, text='💾 Dialog dump', command=app.dump_dialog, bg="#2196f3", fg="white", font=("Segoe UI", 12, "bold")).grid(row=12, column=0, columnspan=2, sticky="ew", pady=button_pad_y)
    Button(frame, text='🚪 Exit', command=window.destroy, bg="#9e9e9e", fg="white", font=("Segoe UI", 12, "bold")).grid(row=13, column=0, columnspan=2, sticky="ew", pady=button_pad_y)

    # Привязка комбобоксов
    combobox_target.bind("<<ComboboxSelected>>", app.selected)
    combobox_size.bind("<<ComboboxSelected>>", app.set_count_of_messages)
    app.bind_comboboxes(combobox_target, combobox_size)

    window.mainloop()
