import asyncio

from loguru import logger
from vkbottle.bot import Message

from .. import ai, config, floodwait, formatter, phrase
from .client import bot

logger.info(f"Загружен модуль {__name__}!")

WaitAI = floodwait.FloodWaitBase("WaitAI", config.flood.ai)


@bot.on.message(text="/ии <prompt>")
async def ai_message(message: Message, prompt: str | None = None):
    if prompt is None:
        return await message.reply(phrase.ai.no_resp)
    request = WaitAI.request()
    if request is False:
        return await message.reply(phrase.wait.ai)
    await asyncio.sleep(request)
    logger.info(f"Запрос {prompt}")
    chat = ai.MainChat
    try:
        response = await chat.send_message(prompt)
    except Exception:
        return logger.error("Не удалось получить ответ ИИ")
    try:
        if len(response) > 4096:
            response = formatter.splitter(response)
            for chunk in response:
                await message.reply(chunk)
        else:
            return await message.reply(response)
    except Exception:
        return await message.reply(phrase.ai.error)
