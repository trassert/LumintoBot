from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from telethon.tl.custom import Message
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
    if not event.chat_id == config.chats.chat:
        return await event.reply(phrase.ai.chat)
    request = WaitAI.request()
    if request is not True:
        return await event.reply(
            phrase.wait.until.format(formatter.value_to_str(request, "секунд"))
        )
    text = event.pattern_match.group(1).strip()
    logger.info(f"Запрос {text}")
    try:
        response = (await ai.chat.send_message(f"{event.sender_id} | {text}")).text
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
