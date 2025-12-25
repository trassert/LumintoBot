import asyncio

from loguru import logger
from telethon import events
from telethon.tl.custom import Message

from .. import ai, config, floodwait, formatter, phrase
from .client import client
from .global_checks import checks

logger.info(f"Загружен модуль {__name__}!")

WaitAI = floodwait.FloodWaitBase("WaitAI", config.flood.ai)


@client.on(events.NewMessage(pattern=r"(?i)^/ии\s([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ai\s([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^ии\s([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/бот\s([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/лаи\s([\s\S]+)", func=checks))
async def gemini(event: Message):
    text = event.pattern_match.group(1).strip()

    if event.chat_id == config.chats.chat:
        chat = ai.MainChat
        request = WaitAI.request()
    elif event.chat_id == config.chats.staff:
        chat = ai.StaffChat
        request = 0
    else:
        return await event.reply(phrase.ai.only_chat)

    if request is False:
        return await event.reply(phrase.wait.ai)

    default: Message = await event.reply(
        phrase.wait.ai_full.format(
            "" if request == 0 else f" (~{request} сек.)",
        ),
    )
    await asyncio.sleep(request)

    try:
        response = await ai.embedding_request(text, event.sender_id, await chat.get_chat())
    except Exception as e:
        await default.edit(phrase.ai.error)
        return logger.error(f"Не удалось получить ответ ИИ: {e}")
    try:
        if len(response) > 4096:
            response = formatter.splitter(response)
            await default.edit(response.pop(0))
            for chunk in response:
                await event.reply(chunk)
        else:
            return await default.edit(response)
    except Exception:
        return await default.edit(phrase.ai.error)


@client.on(events.NewMessage(pattern=r"(?i)^/ии$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ai$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^ии$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/бот$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/лаи$", func=checks))
async def gemini_empty(event: Message):
    return await event.reply(phrase.ai.no_resp)
