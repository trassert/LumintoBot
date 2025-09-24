from vkbottle.bot import Bot, Message
from typing import Optional

from .. import config, phrase, ai, floodwait, formatter
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

bot = Bot(token=config.tokens.bot.vk)

WaitAI = floodwait.FloodWaitBase("WaitAI", config.flood.ai)


@bot.on.message(text="/ии <prompt>")
async def ai_message(message: Message, prompt: Optional[str] = None):
    if prompt is None:
        return await message.reply(phrase.ai.no_resp)
    request = WaitAI.request()
    if request is not True:
        return await message.reply(
            phrase.wait.until.format(formatter.value_to_str(request, "секунд"))
        )
    logger.info(f"Запрос {prompt}")
    chat = ai.chat
    try:
        response = (await chat.send_message(prompt)).text
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
