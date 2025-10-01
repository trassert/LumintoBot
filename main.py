import asyncio

from loguru import logger
from sys import stderr

logger.remove()
logger.add(
    stderr,
    format="<blue>{time:HH:mm:ss}</blue>"
    " <bold>|</bold> <level>{level}</level>"
    " <bold>|</bold> <green>{function}</green>"
    " <cyan><bold>></bold></cyan> {message}",
    level="INFO",
    colorize=True,
)

from modules.telegram.client import client as tg  # noqa: E402
from modules.vk import client as vk  # noqa: E402
from modules import db, config, webhooks, time_to, ai, phrase  # noqa: E402


async def init():
    await tg.start(bot_token=config.tokens.bot.token)
    await db.Users.initialize()
    logger.info(
        f"Ответ ИИ - {(await ai.chat.send_message(phrase.ai.main_prompt)).text.replace('\n', '')}"
    )
    logger.info(
        f"Крокодил - {(await ai.crocodile.send_message(phrase.ai.crocodile_prompt)).text.replace('\n', '')}"
    )
    logger.info(
        f"Стафф - {(await ai.staff.send_message(phrase.ai.staff_prompt)).text.replace('\n', '')}"
    )


async def main():
    await init()
    await webhooks.server()
    await asyncio.gather(
        tg.run_until_disconnected(),
        vk.start(),
        time_to.update_shop(),
        time_to.rewards(),
        time_to.remove_states(),
        time_to.port_checks(),
    )


if __name__ == "__main__":
    if sum(db.database("shop_weight").values()) != 100:
        logger.error("Сумма процентов в магазине не равна 100!")
    try:
        try:
            import uvloop

            uvloop.run(main())
        except ModuleNotFoundError:
            logger.warning("Uvloop не установлен!")
            asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.warning("Закрываю бота!")
