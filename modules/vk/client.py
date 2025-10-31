from loguru import logger
from vkbottle.bot import Bot

from .. import config

logger.info(f"Загружен модуль {__name__}!")

bot = Bot(token=config.tokens.bot.vk)


async def start():
    """Небольшой костыль для запуска uvloop и telethon с vkbottle"""
    logger.info("Запускаю Polling VKBottle...")
    async for event in bot.polling.listen():
        for update in event.get("updates", []):
            await bot.router.route(update, bot.polling.api)
