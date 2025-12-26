import aiofiles
import datetime

from loguru import logger
from os import path

from . import pathes

logger.info(f"Загружен модуль {__name__}!")


async def buy(nick: str, item: str, value: str):
    async with aiofiles.open(
        path.join(
            pathes.shop_log,
            "{}.log".format(datetime.date.today().strftime("%Y.%m.%d")),
        ),
        "a",
    ) as f:
        await f.write(f"{nick}|{item}-{value}\n")
