from typing import Dict, List

from tkinter import (
    Tk, Toplevel, Frame, Label, Button, StringVar, IntVar,
    Entry, Canvas, Scrollbar, RIGHT, Y, LEFT, BOTH, filedialog, Listbox, SINGLE, END, Checkbutton, Text
)
from tkinter.ttk import Combobox

from src.tkinter_app.Backend import TkinterApp, HandlerConfig
from src.bot.Mods import BotActionMode
from src.common.Utils import dump_dialog_from_telegram, get_names_from_tg_dump as _get_names_from_tg_dump

def _open_tg_import_window(app: TkinterApp):
    """
    Окно для выбора Telegram dump и задания маппинга имён.
    """
    path = filedialog.askopenfilename(
        title="Выберите дамп Telegram",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not path:
        return

    mapping_win = Toplevel()
    mapping_win.title("Telegram → VK Name Mapping")
    mapping_win.geometry("860x520")
    mapping_win.configure(bg="#f4f6f8")

    Label(mapping_win, text="Укажите соответствия имён (Telegram → VK):",
          font=("Segoe UI Semibold", 14), bg="#f4f6f8", fg="#333").pack(pady=(12, 4))
    Label(mapping_win, text=f"Файл: {path}",
          font=("Segoe UI", 10), bg="#f4f6f8", fg="#666").pack(pady=(0, 8))

    content = Frame(mapping_win, bg="#f4f6f8")
    content.pack(fill="both", expand=True, padx=14, pady=8)

    # Левая колонка: найденные имена
    left = Frame(content, bg="#f4f6f8")
    left.pack(side=LEFT, fill="both", expand=True, padx=(0, 8))
    Label(left, text="Найденные имена (TG):", font=("Segoe UI", 12, "bold"), bg="#f4f6f8").pack(anchor="w", pady=(0, 6))

    listbox_frame = Frame(left, bg="#f4f6f8")
    listbox_frame.pack(fill="both", expand=True)
    lb_scroll = Scrollbar(listbox_frame)
    lb_scroll.pack(side=RIGHT, fill=Y)
    tg_names_listbox = Listbox(listbox_frame, selectmode=SINGLE, yscrollcommand=lb_scroll.set,
                               font=("Segoe UI", 11), height=14)
    tg_names_listbox.pack(fill="both", expand=True)
    lb_scroll.config(command=tg_names_listbox.yview)

    left_btns = Frame(left, bg="#f4f6f8")
    left_btns.pack(fill="x", pady=(6, 0))

    # Правая колонка: маппинг
    right = Frame(content, bg="#f4f6f8")
    right.pack(side=LEFT, fill="both", expand=True, padx=(8, 0))
    Label(right, text="Маппинг (TG → VK):", font=("Segoe UI", 12, "bold"), bg="#f4f6f8").pack(anchor="w", pady=(0, 6))
    mapping_area = Frame(right, bg="#f4f6f8", bd=0)
    mapping_area.pack(fill="both", expand=True)

    head = Frame(mapping_area, bg="#f4f6f8")
    head.pack(fill="x", pady=(0, 6))
    Label(head, text="TG Name", font=("Segoe UI", 11, "bold"), bg="#f4f6f8", width=32, anchor="w").grid(row=0, column=0, padx=(0, 8))
    Label(head, text="VK Name / ID", font=("Segoe UI", 11, "bold"), bg="#f4f6f8", width=32, anchor="w").grid(row=0, column=1, padx=(8, 0))

    rows_container = Frame(mapping_area, bg="#f4f6f8")
    rows_container.pack(fill="both", expand=True)
    rows_canvas = Canvas(rows_container, bg="#f4f6f8", highlightthickness=0)
    rows_canvas.pack(side=LEFT, fill=BOTH, expand=True)
    rows_scroll = Scrollbar(rows_container, command=rows_canvas.yview)
    rows_scroll.pack(side=RIGHT, fill=Y)
    rows_canvas.configure(yscrollcommand=rows_scroll.set)
    rows_inner = Frame(rows_canvas, bg="#f4f6f8")
    rows_canvas.create_window((0, 0), window=rows_inner, anchor="nw")

    mapping_entries: List[tuple[Entry, Entry]] = []

    def _recalc_scroll(_evt=None):
        rows_inner.update_idletasks()
        rows_canvas.configure(scrollregion=rows_canvas.bbox("all"))

    rows_inner.bind("<Configure>", _recalc_scroll)

    def add_mapping_row(tg_val: str = "", vk_val: str = ""):
        row = Frame(rows_inner, bg="#f4f6f8")
        row.pack(fill="x", pady=3)
        e_tg = Entry(row, width=36, font=("Segoe UI", 11))
        e_tg.insert(0, tg_val)
        e_tg.grid(row=0, column=0, padx=(0, 8), sticky="w")
        e_vk = Entry(row, width=36, font=("Segoe UI", 11))
        e_vk.insert(0, vk_val)
        e_vk.grid(row=0, column=1, padx=(8, 0), sticky="w")

        def remove_row():
            try:
                mapping_entries.remove((e_tg, e_vk))
            except ValueError:
                pass
            row.destroy()
            _recalc_scroll()

        Button(row, text="✖", command=remove_row, bg="#f44336", fg="white",
               width=3, font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=(8, 0))
        mapping_entries.append((e_tg, e_vk))
        _recalc_scroll()

    right_btns = Frame(right, bg="#f4f6f8")
    right_btns.pack(fill="x", pady=(6, 0))

    Button(right_btns, text="+ Add row", command=lambda: add_mapping_row("", ""),
           bg="#2196f3", fg="white", font=("Segoe UI", 11)).pack(side=LEFT)

    discovered_names = sorted(list(_get_names_from_tg_dump(path)))
    for n in discovered_names:
        tg_names_listbox.insert(END, n)

    def add_selected_name():
        sel = tg_names_listbox.curselection()
        if not sel:
            return
        name = tg_names_listbox.get(sel[0])
        add_mapping_row(name, "")

    def add_all_names(max_count: int = 200):
        existing_tg = {et.get().strip() for et, _ in mapping_entries if et.get().strip()}
        count = 0
        for name in discovered_names:
            if name not in existing_tg:
                add_mapping_row(name, "")
                count += 1
                if count >= max_count:
                    break

    Button(left_btns, text="➕ Добавить выбранное имя →", command=add_selected_name,
           bg="#673ab7", fg="white", font=("Segoe UI", 11)).pack(side=LEFT, padx=(0, 6))
    Button(left_btns, text="⏩ Автодобавить все", command=add_all_names,
           bg="#009688", fg="white", font=("Segoe UI", 11)).pack(side=LEFT)

    bottom = Frame(mapping_win, bg="#f4f6f8")
    bottom.pack(fill="x", pady=10)

    def submit_mapping():
        mapping: Dict[str, str] = {}
        for e_tg, e_vk in mapping_entries:
            tg_name = e_tg.get().strip()
            vk_name = e_vk.get().strip()
            if tg_name and vk_name:
                mapping[tg_name] = vk_name

        mapping_win.destroy()
        dump_dialog_from_telegram(app._current_target, path, mapping)

    Button(bottom, text="✅ Импортировать", command=submit_mapping,
           bg="#4caf50", fg="white", font=("Segoe UI Semibold", 12)).pack(side=LEFT, padx=(0, 8))
    Button(bottom, text="❌ Отмена", command=mapping_win.destroy,
           bg="#f44336", fg="white", font=("Segoe UI Semibold", 12)).pack(side=LEFT)


# ------------------------- ОСНОВНОЙ UI -------------------------

def start(app: TkinterApp, targets: Dict[str, str], counts: List[int]) -> None:
    window = Tk()
    window.title("🎯 VK ChatBot Control Panel")
    window.geometry("1300x1000")
    window.configure(bg="#f4f6f8")

    left_frame = Frame(window, bg="#f4f6f8", padx=25, pady=25)
    left_frame.pack(side="left", fill="both", expand=True)

    Label(left_frame, text="VK ChatBot Control Panel",
          font=("Segoe UI Semibold", 20), bg="#f4f6f8", fg="#333").grid(row=0, column=0, columnspan=2, pady=(0, 20))

    # ------------------ Таргет и размер дампа ------------------
    Label(left_frame, text="Выберите цель:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=1, column=0, sticky="w", pady=5)
    targets_list: List[str] = [f'{t_name} {t_id}' for t_name, t_id in targets.items()]
    target_var = StringVar(value="Choose target")
    combobox_target = Combobox(left_frame, values=targets_list, width=35, textvariable=target_var,
                               state="readonly", font=("Segoe UI", 12))
    combobox_target.grid(row=1, column=1, pady=5)

    Label(left_frame, text="Размер дампа:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=2, column=0, sticky="w", pady=5)
    size_var = StringVar(value="Select size")
    combobox_size = Combobox(left_frame, values=counts, width=35, textvariable=size_var,
                             state="readonly", font=("Segoe UI", 12))
    combobox_size.grid(row=2, column=1, pady=5)

    # ------------------ Настройки ------------------
    delay_var = IntVar(value=5)
    Label(left_frame, text="Период накопления сообщений (sec):", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=3, column=0, sticky="w", pady=5)
    Entry(left_frame, textvariable=delay_var, width=8, font=("Segoe UI", 12)).grid(row=3, column=1, sticky="w")

    min_chars_var = IntVar(value=3)
    Label(left_frame, text="Мин. скорость печати/sec:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=4, column=0, sticky="w", pady=5)
    Entry(left_frame, textvariable=min_chars_var, width=8, font=("Segoe UI", 12)).grid(row=4, column=1, sticky="w")

    max_chars_var = IntVar(value=5)
    Label(left_frame, text="Макс. скорость печати/sec:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=5, column=0, sticky="w", pady=5)
    Entry(left_frame, textvariable=max_chars_var, width=8, font=("Segoe UI", 12)).grid(row=5, column=1, sticky="w")

    penalty_var = IntVar(value=5)
    Label(left_frame, text="Множитель штрафа за спам:", font=("Segoe UI", 12), bg="#f4f6f8").grid(row=6, column=0, sticky="w", pady=5)
    Entry(left_frame, textvariable=penalty_var, width=8, font=("Segoe UI", 12)).grid(row=6, column=1, sticky="w")

    # ------------------ Режимы ------------------
    mode_dialog_var = IntVar(value=1)
    mode_reaction_var = IntVar(value=1)
    Checkbutton(left_frame, text="DIALOG", variable=mode_dialog_var, font=("Segoe UI", 12), bg="#f4f6f8").grid(row=7, column=1, sticky="w")
    Checkbutton(left_frame, text="REACTION", variable=mode_reaction_var, font=("Segoe UI", 12), bg="#f4f6f8").grid(row=8, column=1, sticky="w")

    # ------------------ Поле для правил ------------------
    Label(left_frame, text="Правила ведения диалога (построчно):", font=("Segoe UI", 12), bg="#f4f6f8").grid(
        row=9, column=0, sticky="nw", pady=(10, 5)
    )

    rules_frame = Frame(left_frame, bg="#f4f6f8")
    rules_frame.grid(row=9, column=1, pady=(10, 5), sticky="nsew")

    # Текст + скроллбар
    rules_scroll = Scrollbar(rules_frame)
    rules_scroll.pack(side=RIGHT, fill=Y)

    rules_text = Text(
        rules_frame,
        width=50,
        height=12,
        font=("Segoe UI", 11),
        wrap="word",
        yscrollcommand=rules_scroll.set,
        relief="solid",
        bd=1,
    )
    rules_text.pack(fill="both", expand=True)

    rules_scroll.config(command=rules_text.yview)

    # Кнопка загрузки правил из файла
    def load_rules_from_file():
        file_path = filedialog.askopenfilename(
            title="Выберите файл с правилами",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            rules_text.delete("1.0", "end")
            rules_text.insert("1.0", content)
        except Exception as e:
            print(f"Ошибка загрузки файла правил: {e}")

    Button(rules_frame, text="📂 Загрузить из файла",
           command=load_rules_from_file,
           bg="#009688", fg="white", font=("Segoe UI", 10)).pack(fill="x", pady=(4, 0))

    # ------------------ Кнопки ------------------
    button_pad_y = 6
    Button(left_frame, text='▶ Запустить обработчик.',
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
                   penalty_scale=penalty_var.get(),
                   rules="\n".join(
                       line.strip() for line in rules_text.get("1.0", "end").splitlines() if line.strip()
                   )
               )
           ),
           bg="#4caf50", fg="white", font=("Segoe UI Semibold", 12, "bold")).grid(row=10, column=0, columnspan=2, sticky="ew", pady=button_pad_y)

    Button(left_frame, text='⛔ Выключить обработчик для текущего пользователя', command=app.stop, bg="#ff9800", fg="white",
           font=("Segoe UI Semibold", 12, "bold")).grid(row=11, column=0, columnspan=2, sticky="ew", pady=button_pad_y)
    Button(left_frame, text='🛑 Выключить все обработчики', command=app.stop_all, bg="#f44336", fg="white",
           font=("Segoe UI Semibold", 12, "bold")).grid(row=12, column=0, columnspan=2, sticky="ew", pady=button_pad_y)

    Button(left_frame, text='💾 Импорт диалога из VK', command=app.dump_dialog, bg="#2196f3", fg="white",
           font=("Segoe UI Semibold", 12, "bold")).grid(row=13, column=0, columnspan=2, sticky="ew", pady=button_pad_y)

    Button(left_frame, text='📂 Импорт диалога из Telegram',
           command=lambda: _open_tg_import_window(app),
           bg="#673ab7", fg="white", font=("Segoe UI Semibold", 12)).grid(row=14, column=0, columnspan=2, sticky="ew", pady=button_pad_y)

    Button(left_frame, text='🚪 Выход', command=window.destroy, bg="#9e9e9e", fg="white",
           font=("Segoe UI Semibold", 12)).grid(row=15, column=0, columnspan=2, sticky="ew", pady=button_pad_y)

    # ------------------ Привязки ------------------
    combobox_target.bind("<<ComboboxSelected>>", app.selected)
    combobox_size.bind("<<ComboboxSelected>>", app.set_count_of_messages)
    app.bind_comboboxes(combobox_target, combobox_size)

    # ------------------ Правый фрейм: мониторинг ------------------
    right_frame = Frame(window, bg="#e9ecef", padx=15, pady=15)
    right_frame.pack(side="right", fill="both", expand=False)

    Label(right_frame, text="Статус обработчика", font=("Segoe UI Semibold", 14), bg="#e9ecef").pack(pady=(0, 10))
    canvas = Canvas(right_frame, width=430, bg="#e9ecef", highlightthickness=0)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar = Scrollbar(right_frame, command=canvas.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    canvas.configure(yscrollcommand=scrollbar.set)
    blocks_frame = Frame(canvas, bg="#e9ecef")
    canvas.create_window((0, 0), window=blocks_frame, anchor="nw")
    BLOCK_HEIGHT = 56
    BLOCK_PAD = 6

    def update_handlers_status():
        for widget in blocks_frame.winfo_children():
            widget.destroy()
        for handler in app.handlers_states:
            handler_id = handler.get("id", "unknown")
            handler_name = handler.get("name", "unknown")
            running = handler.get("running", False)
            current_state = handler.get("current_state", "")
            color = "#4caf50" if running else "#f44336"
            block = Frame(blocks_frame, bg=color, height=BLOCK_HEIGHT, width=400)
            block.pack(pady=(0, BLOCK_PAD), fill="x")
            label_text = f"{handler_id} ({handler_name}): {current_state}"
            Label(block, text=label_text, bg=color, fg="white", font=("Segoe UI Semibold", 12)).pack(padx=10, pady=10, anchor="w")
        blocks_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        window.after(1000, update_handlers_status)

    update_handlers_status()
    window.mainloop()
