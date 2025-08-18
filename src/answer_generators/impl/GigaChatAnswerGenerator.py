import logging
from typing import Callable

from langchain_community.chat_models.gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
from enum import Enum

from src.answer_generators.core.AbstractAnswerGenerator import AbstractAnswerGenerator


class GigaModels(Enum):
    GIGACHAT_2 = "GigaChat-2"
    GIGACHAT_2_PRO = "GigaChat-2-Pro"
    GIGACHAT_2_MAX = 'GigaChat-2-Max'


def init_dialog_prompt_fabric(context: str, rules: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system",
         f"""Ты - участник диалога. Тебе нужно изучить отрывок старого диалога, представленный ниже, и придумать какой
          фразой начать новый диалог с данным человеком, либо, если есть возможность, как продолжить данный. 
          Правила:
          Основное правило - имитировать письменную речь и ход мыслей собеседника, которым ты являешься, если это не противоречит правилам ниже: 
          {rules}
          Вот диалог: {context}"""),
        ("user", "{message}")
    ])


def continue_dialog_prompt_fabric(context: str, rules: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
            ("system",
             f"""Ты - участник диалога, который идет прямо сейчас. Тебе нужно изучить ход диалога, представленный ниже, и придумать какой
                 фразой продолжить диалог с данным человеком.
                 Основное правило - имитировать письменную речь и ход мыслей собеседника, которым ты являешься, если это не противоречит правилам ниже:
                 {rules}
                Вот диалог: {context}"""),
                ("user", "{message}")
        ])

class GigaChatAnswerGenerator(AbstractAnswerGenerator):
    def __init__(
            self,
            secret: str,
            model: GigaModels
    ):
        self._giga: GigaChat = GigaChat(
            credentials=secret,
            model=model.value,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        )


    def __call__(self, message: str | None, context: str, rules: str) -> str:
        prompt = continue_dialog_prompt_fabric(context, rules) if message is not None else init_dialog_prompt_fabric(context, rules)
        user_message = f"Собеседник отправил новые сообщения. Ответь ему. Не забывай, что тебе нужно быть похожим на TARGET: {message}" if message is not None else "Начни диалог. Не забывай, что тебе нужно быть похожим на TARGET."
        chain = prompt | self._giga
        logging.info(f"промпт: {prompt}")
        response: BaseMessage = chain.invoke({"message": user_message})
        return response.content