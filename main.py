import asyncio
import logging
from sys import stderr

from loguru import logger

logger.remove()
logger.add(
    stderr,
    format="[{time:HH:mm:ss} <level>{level}</level>]:"
    " <green>{file}:{function}</green>"
    " <cyan>></cyan> {message}",
    level="INFO",
    colorize=True,
    backtrace=False,
    diagnose=False,
)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = "TRACE" if record.levelno == 5 else record.levelname
        logger.opt(depth=6, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


logging.basicConfig(handlers=[InterceptHandler()], level=0)


async def main():
    from modules import (
        ai,
        config,
        db,
        phrase,
        task_gen,
        tasks,
        webhooks,
    )
    from modules.telegram.client import client as tg
    from modules.vk import client as vk

    if sum(db.database("shop_weight").values()) != 100:
        logger.error("Сумма процентов в магазине не равна 100!")
    await db.Users.initialize()
    logger.info(
        f"Ответ ИИ - {(await ai.chat.send_message(phrase.ai.main_prompt)).text.replace('\n', '')}",
    )
    logger.info(
        f"Крокодил - {(await ai.crocodile.send_message(phrase.ai.crocodile_prompt)).text.replace('\n', '')}",
    )
    logger.info(
        f"Стафф - {(await ai.staff.send_message(phrase.ai.staff_prompt)).text.replace('\n', '')}",
    )
    await tg.start(bot_token=config.tokens.bot.token)
    await webhooks.server()
    await task_gen.UpdateShopTask.create(tasks.update_shop, 2)
    await task_gen.RewardsTask.create(tasks.rewards, "19:00")
    await task_gen.RemoveStatesTask.create(tasks.remove_states, "17:00")
    await asyncio.gather(
        tg.run_until_disconnected(),
        vk.start()
    )


if __name__ == "__main__":
    try:
        try:
            import uvloop

            uvloop.run(main())
        except ModuleNotFoundError:
            logger.warning(
                "Uvloop не найден! Установите его для большей производительности",
            )
            asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.warning("Закрываю бота!")
