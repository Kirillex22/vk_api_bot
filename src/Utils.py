from typing import Dict, Any


class DialogCollector:
    def __init__(self, users: Dict[str, Any]):
        """
        :param users: Cловарь ID пользователя : Псевдоним
        """
        self._users = users

    def _get_first_post_text(self, data: dict) -> str:
        attachments = data.get('attachments', [])
        if not attachments:
            return ""
        first = attachments[0]
        if first.get('type') == 'wall':
            wall = first.get('wall', {})
            return wall.get('text', "")
        return ""

    def __call__(self, dialog_slice: Dict[str, Any], message_len_limit: int = 100) -> str:
        """
        Собирает API-Ответ в строку в формате Псевдоним: Cообщение_1\n ... Псевдоним: Cообщение_N
        :param dialog_slice: Срез диалога
        :param message_len_limit: Максимальная длина одного сообщения (большие по длине отфильтруются)
        :return:
        """
        collected: str = ""
        for item in dialog_slice.get('items', []):
            text: str | None = item.get('text')
            if text is None or len(text) <= 0:
                text: str = self._get_first_post_text(item)
            if text is not None and 0 < len(text) <= message_len_limit:
                userid: str = str(item.get('from_id'))
                username: str = self._users.get(userid)
                if username is None:
                    username: str = 'Цель имитации.'
                collected += f"ИМЯ:{username}, ТЕКСТ СООБЩЕНИЯ: {text}\n"

        return collected