from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from telethon.sync import TelegramClient

from os import path

from .. import (
    config,
)

client = TelegramClient(
    session=path.join("db", "bot"),
    api_id=config.tokens.bot.id,
    api_hash=config.tokens.bot.hash,
    device_model="Bot",
    system_version="4.16.30-vxCUSTOM",
    use_ipv6=True,
)

from . import (
    actions,
    admins,
    ai,
    base,
    callbacks,
    func,
    games,
    global_checks,
    shop,
    states,
    statistic,
    tickets,
)
