import asyncio

from loguru import logger
from sys import stderr

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

from modules.telegram.client import client  # noqa: E402
from modules import db, config, webhooks, time_to, ai, phrase  # noqa: E402


async def main():
    while True:
        try:
            logger.info(
                "Ответ ИИ - {}".format(
                    (await ai.chat.send_message(phrase.ai.main_prompt)).text.replace(
                        "\n", ""
                    )
                )
            )
            logger.info(
                "Крокодил - {}".format(
                    (
                        await ai.crocodile.send_message(phrase.ai.crocodile_prompt)
                    ).text.replace("\n", "")
                )
            )
            logger.info(
                "Стафф-чат - {}".format(
                    (await ai.staff.send_message(phrase.ai.staff_prompt)).text.replace(
                        "\n", ""
                    )
                )
            )
            await db.Users.initialize()
            await webhooks.server()
            await asyncio.gather(
                client.start(bot_token=config.tokens.bot.token),
                time_to.update_shop(),
                time_to.rewards(),
                time_to.remove_states(),
            )
        except ConnectionError:
            logger.error("Жду 20 секунд (нет подключения к интернету)")
            await asyncio.sleep(20)


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
