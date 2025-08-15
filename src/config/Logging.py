import logging
import sys

def setup_logging() -> None:
    # Общий формат
    log_format = '[%(asctime)s] %(levelname)s: %(message)s'
    date_format = '%H:%M:%S'

    # Создаём обработчик для файла
    file_handler = logging.FileHandler(
        'vk_api_bot.log',
        mode='a',  # или 'w' если нужно перезаписывать
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Создаём обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Конфигурируем root-логгер
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )