import datetime
import logging
from sys import stderr

import aiofiles
from loguru import logger

from . import pathes

logger.info(f"Загружен модуль {__name__}!")


class InterceptHandler(logging.Handler):
    def emit(self, record):
        level = "TRACE" if record.levelno == 5 else record.levelname
        logger.opt(depth=6, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def setup():
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
    log_dir = pathes.log
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "{time:YYYY-MM-DD}.log",
        format="[{time:HH:mm:ss} <level>{level}</level>]:",
        rotation="00:00",
        retention="30 days",
        level="INFO",
        colorize=True,
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )
    logger.info("Настроено логирование!")

    return logging.basicConfig(handlers=[InterceptHandler()], level=0)


async def buy(nick: str, item: str, value: str):
    async with aiofiles.open(
        pathes.shop_log / "{}.log".format(datetime.date.today().strftime("%Y.%m.%d")),
        "a",
    ) as f:
        await f.write(f"{nick}|{item}-{value}\n")
