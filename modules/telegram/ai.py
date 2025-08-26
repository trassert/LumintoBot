from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from telethon.tl.custom import Message
from telethon.errors import MessageTooLongError
from telethon import events

from .client import client
from .global_checks import *

from .. import phrase, ai, config, floodwait, formatter

WaitAI = floodwait.FloodWaitBase("WaitAI", config.flood.ai)


@client.on(events.NewMessage(pattern=r"(?i)^/ии\s([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ai\s([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^ии\s([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/бот\s([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/лаи\s([\s\S]+)", func=checks))
async def gemini(event: Message):
    text = event.pattern_match.group(1).strip()

    if event.chat_id == config.chats.chat:
        chat = ai.chat
        prompt = f"{event.sender_id} | {text}"
        request = WaitAI.request()
    elif event.chat_id == config.chats.staff:
        chat = ai.staff
        prompt = text
        request = True
    else:
        return await event.reply(phrase.ai.only_chat)

    if request is not True:
        return await event.reply(
            phrase.wait.until.format(formatter.value_to_str(request, "секунд"))
        )

    logger.info(f"Запрос {prompt}")
    try:
        response = (await chat.send_message(prompt)).text
    except Exception:
        return logger.error("Не удалось получить ответ ИИ")
    try:
        if len(response) > 4096:
            response = formatter.splitter(response)
            for chunk in response:
                await event.reply(chunk)
        else:
            await event.reply(response)
    except Exception:
        await event.reply(phrase.ai.error)


@client.on(events.NewMessage(pattern=r"(?i)^/ии$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ai$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^ии$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/бот$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/лаи$", func=checks))
async def gemini_empty(event: Message):
    return await event.reply(phrase.ai.no_resp)
