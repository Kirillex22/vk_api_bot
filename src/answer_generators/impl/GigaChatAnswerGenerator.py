from typing import Callable

from langchain_community.chat_models.gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
from enum import Enum

from src.answer_generators.core.BaseAnswerGenerator import BaseAnswerGenerator


class GigaModels(Enum):
    GIGACHAT_2 = "GigaChat-2"
    GIGACHAT_2_PRO = "GigaChat-2-Pro"
    GIGACHAT_2_MAX = 'GigaChat-2-Max'


class GigaChatAnswerGenerator(BaseAnswerGenerator):
    def __init__(
            self,
            secret: str,
            model: GigaModels,
            init_dialog_prompt_fabric: Callable[[str], ChatPromptTemplate] = None,
            continue_dialog_prompt_fabric: Callable[[str], ChatPromptTemplate] = None
    ):
        self._giga: GigaChat = GigaChat(
            credentials=secret,
            model=model.value,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        )

        self._init_dialog_prompt_fabric = init_dialog_prompt_fabric

        if init_dialog_prompt_fabric is None:
            def default_init_dialog_prompt_fabric(context: str) -> ChatPromptTemplate:
                return ChatPromptTemplate.from_messages([
                    ("system",
                     f"""Ты - участник диалога. Тебе нужно изучить отрывок старого диалога, представленный ниже, и придумать какой
                     фразой начать новый диалог с данным человеком, чтобы это звучало естественно, с учетом стиля общения, 
                     а также присущей сторонам пунктуации и соблюдения норм русского языка. Вот фрагмент диалога.
                                {context}"""),
                    ("user", "{message}")
                ])

            self._init_dialog_prompt_fabric = default_init_dialog_prompt_fabric

        self._continue_dialog_prompt_fabric = continue_dialog_prompt_fabric

        if continue_dialog_prompt_fabric is None:
            def default_continue_dialog_prompt_fabric(context: str) -> ChatPromptTemplate:
                return ChatPromptTemplate.from_messages([
                ("system",
                 f"""Ты - участник диалога, который идет прямо сейчас. Тебе нужно изучить ход диалога, представленный ниже, и придумать какой
                     фразой продолжить диалог с данным человеком, чтобы это звучало естественно, с учетом стиля общения, а также присущей 
                     сторонам пунктуации и соблюдения норм русского языка. Вот диалог.
                    {context}"""),
                ("user", "{message}")
            ])

            self._continue_dialog_prompt_fabric = default_continue_dialog_prompt_fabric



    def __call__(self, message: str | None, context: str) -> str:
        prompt = self._continue_dialog_prompt_fabric(context) if message is not None else self._init_dialog_prompt_fabric(message)
        user_message = f"Собеседник отправил новые сообщения. Верни фразу, которой ответишь. Не забывай, что тебе нужно быть похожим на TARGET: {message}" if message is not None else "Верни фразу, которой начнешь новый диалог. Не забывай, что тебе нужно быть похожим на TARGET."
        chain = prompt | self._giga
        response: BaseMessage = chain.invoke({"message": user_message})
        return response.content