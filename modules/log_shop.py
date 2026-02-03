import datetime

import aiofiles
from loguru import logger

from . import pathes

logger.info(f"Загружен модуль {__name__}!")


async def buy(nick: str, item: str, value: str):
    async with aiofiles.open(
        pathes.shop_log
        / "{}.log".format(datetime.date.today().strftime("%Y.%m.%d")),
        "a",
    ) as f:
        await f.write(f"{nick}|{item}-{value}\n")
