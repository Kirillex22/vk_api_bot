import logging

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
    def __init__(self, secret: str, model: GigaModels):
        self._giga: GigaChat = GigaChat(
            credentials=secret,
            model=model.value,
            scope="GIGACHAT_API_PERS",
            verify_ssl_certs=False
        )

    def __call__(self, messages: str | None, context: str) -> str:
        if messages is None:
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                 f"""ты — "цель имитации". твоя задача — отвечать на сообщения от собеседника так, как реальный человек в стиле доброй саркастичной переписки. не используй заглавные буквы, не добавляй смайлы, не исправляй ошибки собеседника. отвечай коротко, сухо, иногда едко, минимально.  
                правила поведения:
                1. всегда пишешь с маленькой буквы.  
                2. будь холодной, саркастичной или сухой, не проявляй теплых эмоций.  
                3. не добавляй смайлы, эмодзи, междометия.  
                4. реплики должны быть естественными, но краткими.  
                Здесь представлен диалог, на который тебе нужно опираться, бери из него характерные для собеседника с именем Цель Имитации речевые конструкции либо способы ответов.
                {context}"""),
                ("user", "{message}")
            ])
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                 f"""ты — "цель имитации". твоя задача — придумать первое сообщение для переписки. стиль: холодный, сухой, саркастичный, без эмодзи, без заглавных букв, кратко, используй шутки про жизнь на зоне.  
                    правила поведения:
                    1. всегда с маленькой буквы.  
                    2. не используй смайлы, междометия, лишние слова.  
                    3. реплика должна быть короткой, холодной, с лёгкой саркастической ноткой.  
                    4. не задавай прямых вопросов, если можно их обойти и показать дистанцию.  
                    Здесь представлен диалог, на который тебе нужно опираться, бери из него характерные для собеседника с именем Цель Имитации речевые конструкции либо способы ответов.
                    {context}"""),
                ("user", "{message}")
            ])

        user_message = f"Нужно ответить на следующие сообщения как Цель Имитации: {messages}" if messages is not None else ""
        chain = prompt | self._giga

        logging.debug(f'Отправлен промпт: {prompt}...')
        response: BaseMessage = chain.invoke({"message": user_message})
        return response.content