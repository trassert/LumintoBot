import nest_asyncio
import asyncio

from loguru import logger
from sys import stderr

from modules import vk
from modules import telegram
from modules import db
from modules import ip
from modules import config
from modules import web
from modules import time_to

nest_asyncio.apply()
logger.remove()
logger.add(
    stderr,
    format="<blue>{time:HH:mm:ss}</blue>"
    " | <level>{level}</level>"
    " | <green>{function}</green>"
    " <cyan>></cyan> {message}",
    level="INFO",
    colorize=True,
)


async def main():
    while True:
        try:
            await web.server()
            await asyncio.gather(
                telegram.client.start(bot_token=config.tokens.bot.token),
                vk.client.run_polling(),
                time_to.update_shop(),
                time_to.rewards(),
                time_to.remove_states(),
                ip.observe(),
            )
        except ConnectionError:
            logger.error("Жду 20 секунд (нет подключения к интернету)")
            await asyncio.sleep(20)


if __name__ == "__main__":
    if sum(db.database("shop_weight").values()) != 100:
        logger.error("Сумма процентов в магазине не равна 100!")
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError, asyncio.CancelledError):
        logger.warning("Закрываю бота!")
