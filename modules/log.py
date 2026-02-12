import datetime
import logging

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
    return logging.basicConfig(handlers=[InterceptHandler()], level=0)


async def buy(nick: str, item: str, value: str):
    async with aiofiles.open(
        pathes.shop_log / "{}.log".format(datetime.date.today().strftime("%Y.%m.%d")),
        "a",
    ) as f:
        await f.write(f"{nick}|{item}-{value}\n")
