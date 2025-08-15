from pydantic_settings import BaseSettings
from typing import Dict
from pathlib import Path
import yaml


class AppSettings(BaseSettings):
    # Словарь пользователей: id -> имя
    users: Dict[str, str]

    # Токен VK и ID пользователя
    VK_API_TOKEN: str
    USER_VK_ID: str

    GIGACHAT_API_TOKEN: str

    class Config:
        # Можно оставить пустым, т.к. мы будем читать YAML через метод
        env_file = None

    @classmethod
    def from_yaml_file(cls, path: str) -> "AppSettings":
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"{path} не найден")
        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

