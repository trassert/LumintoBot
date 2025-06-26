import nest_asyncio
import asyncio

from loguru import logger
from sys import stderr

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

from modules.telegram.client import client
from modules import db
from modules import ip
from modules import config
from modules import webhooks
from modules import time_to
from modules import ai
from modules import phrase


async def main():
    while True:
        try:
            logger.info(
                f"Ответ ИИ - {(await ai.chat.send_message(phrase.main_prompt)).text.replace('\n', '')}"
            )
            await db.Users.initialize()
            await webhooks.server()
            await asyncio.gather(
                client.start(bot_token=config.tokens.bot.token),
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
