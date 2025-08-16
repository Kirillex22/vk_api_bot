import sys
from tkinter import Tk, Frame, Label, Button, StringVar, IntVar, Checkbutton, Entry, Canvas, Scrollbar, RIGHT, Y, LEFT, BOTH
from tkinter.ttk import Combobox
from typing import Dict, List

from src.tkinter_app.Backend import TkinterApp, HandlerConfig
from src.bot.Mods import BotActionMode


def start(app: TkinterApp, targets: Dict[str, str], counts: list[int]) -> None:
    window = Tk()
    window.title("🎯 VK ChatBot Control Panel")
    window.geometry("1100x700")
    window.configure(bg="#f4f6f8")

    # --- Левый фрейм: настройки ---
    left_frame = Frame(window, bg="#f4f6f8", padx=25, pady=25)
    left_frame.pack(side="left", fill="both", expand=True)

    Label(
        left_frame,
        text="VK ChatBot Control Panel",
        font=("Segoe UI Semibold", 20),
        bg="#f4f6f8",
        fg="#333"
    ).grid(row=0, column=0, columnspan=2, pady=(0, 20))

    # --- Целевая аудитория ---
    Label(left_frame, text="Select target:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=1, column=0, sticky="w", pady=5)
    targets_list: List[str] = [f'{t_name} {t_id}' for t_name, t_id in targets.items()]
    target_var = StringVar(value="Choose target")
    combobox_target = Combobox(left_frame, values=targets_list, width=35, textvariable=target_var,
                               state="readonly", font=("Segoe UI", 12))
    combobox_target.grid(row=1, column=1, pady=5)

    # --- Размер дампа ---
    Label(left_frame, text="Dump size:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=2, column=0, sticky="w", pady=5)
    size_var = StringVar(value="Select size")
    combobox_size = Combobox(left_frame, values=counts, width=35, textvariable=size_var,
                             state="readonly", font=("Segoe UI", 12))
    combobox_size.grid(row=2, column=1, pady=5)

    # --- Настройки ---
    Label(left_frame, text="Delay (sec):", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=3, column=0, sticky="w", pady=5)
    delay_var = IntVar(value=5)
    Entry(left_frame, textvariable=delay_var, width=8, font=("Segoe UI", 12)).grid(row=3, column=1, sticky="w")

    Label(left_frame, text="Min chars/sec:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=4, column=0, sticky="w", pady=5)
    min_chars_var = IntVar(value=3)
    Entry(left_frame, textvariable=min_chars_var, width=8, font=("Segoe UI", 12)).grid(row=4, column=1, sticky="w")

    Label(left_frame, text="Max chars/sec:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=5, column=0, sticky="w", pady=5)
    max_chars_var = IntVar(value=5)
    Entry(left_frame, textvariable=max_chars_var, width=8, font=("Segoe UI", 12)).grid(row=5, column=1, sticky="w")

    Label(left_frame, text="Penalty scale:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=6, column=0, sticky="w", pady=5)
    penalty_var = IntVar(value=5)
    Entry(left_frame, textvariable=penalty_var, width=8, font=("Segoe UI", 12)).grid(row=6, column=1, sticky="w")

    # --- Режимы действий ---
    Label(left_frame, text="Select modes:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=7, column=0, sticky="w", pady=5)
    mode_dialog_var = IntVar(value=1)
    mode_reaction_var = IntVar(value=1)
    Checkbutton(left_frame, text="DIALOG", variable=mode_dialog_var, font=("Segoe UI", 12), bg="#f4f6f8").grid(row=7, column=1, sticky="w")
    Checkbutton(left_frame, text="REACTION", variable=mode_reaction_var, font=("Segoe UI", 12), bg="#f4f6f8").grid(row=8, column=1, sticky="w")

    # --- Кнопки управления ---
    button_pad_y = 6
    Button(left_frame,
           text='▶ Execute',
           command=lambda: app.start(
               HandlerConfig(
                   targetid=target_var.get().split()[0],
                   delay_between_answers_seconds=delay_var.get(),
                   mode=[mode for m, mode in [
                       (mode_dialog_var.get(), BotActionMode.DIALOG),
                       (mode_reaction_var.get(), BotActionMode.REACTION)
                   ] if m],
                   min_chars_sec_typing=min_chars_var.get(),
                   max_chars_sec_typing=max_chars_var.get(),
                   penalty_scale=penalty_var.get()
               )
           ),
           bg="#4caf50", fg="white", font=("Segoe UI Semibold", 12, "bold")
           ).grid(row=9, column=0, columnspan=2, sticky="ew", pady=button_pad_y)

    Button(left_frame, text='⛔ Terminate for this person', command=app.stop, bg="#ff9800", fg="white",
           font=("Segoe UI Semibold", 12, "bold")).grid(row=10, column=0, columnspan=2, sticky="ew", pady=button_pad_y)
    Button(left_frame, text='🛑 Terminate for all', command=app.stop_all, bg="#f44336", fg="white",
           font=("Segoe UI Semibold", 12, "bold")).grid(row=11, column=0, columnspan=2, sticky="ew", pady=button_pad_y)
    Button(left_frame, text='💾 Dialog dump', command=app.dump_dialog, bg="#2196f3", fg="white",
           font=("Segoe UI Semibold", 12, "bold")).grid(row=12, column=0, columnspan=2, sticky="ew", pady=button_pad_y)
    Button(left_frame, text='🚪 Exit', command=window.destroy, bg="#9e9e9e", fg="white",
           font=("Segoe UI Semibold", 12, "bold")).grid(row=13, column=0, columnspan=2, sticky="ew", pady=button_pad_y)

    combobox_target.bind("<<ComboboxSelected>>", app.selected)
    combobox_size.bind("<<ComboboxSelected>>", app.set_count_of_messages)
    app.bind_comboboxes(combobox_target, combobox_size)

    # --- Правый фрейм: красочный мониторинг обработчиков ---
    right_frame = Frame(window, bg="#e9ecef", padx=15, pady=15)
    right_frame.pack(side="right", fill="both", expand=False)

    Label(right_frame, text="Handlers Status", font=("Segoe UI Semibold", 14), bg="#e9ecef").pack(pady=(0, 10))

    canvas = Canvas(right_frame, width=400, bg="#e9ecef")
    canvas.pack(side=LEFT, fill=BOTH, expand=True)

    scrollbar = Scrollbar(right_frame, command=canvas.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    canvas.configure(yscrollcommand=scrollbar.set)

    blocks_frame = Frame(canvas, bg="#e9ecef")
    canvas.create_window((0, 0), window=blocks_frame, anchor="nw")

    BLOCK_HEIGHT = 50
    BLOCK_PAD = 5

    def update_handlers_status():
        for widget in blocks_frame.winfo_children():
            widget.destroy()

        for i, handler in enumerate(app.handlers_states):
            handler_id = handler.get("id", "unknown")
            handler_name = handler.get("name", "unknown")
            running = handler.get("running", False)
            current_state = handler.get("current_state", "")

            color = "#4caf50" if running else "#f44336"

            block = Frame(blocks_frame, bg=color, height=BLOCK_HEIGHT, width=380)
            block.pack(pady=(0, BLOCK_PAD), fill="x")

            label_text = f"{handler_id} ({handler_name}): {current_state}"
            Label(block, text=label_text, bg=color, fg="white", font=("Segoe UI Semibold", 12)).pack(padx=10, pady=10, anchor="w")

        # обновляем scrollregion
        blocks_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        window.after(1000, update_handlers_status)

    update_handlers_status()
    window.mainloop()
