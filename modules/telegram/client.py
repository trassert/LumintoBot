from loguru import logger
from telethon import TelegramClient

from .. import config, pathes

logger.info(f"Загружен модуль {__name__}!")
client = TelegramClient(
    session=pathes.bot,
    api_id=config.tokens.bot.id,
    api_hash=config.tokens.bot.hash,
    device_model="Bot",
    system_version="4.16.30-vxCUSTOM",
    lang_code="ru",
    system_lang_code="ru",
    use_ipv6=config.vars.UseIPv6,
    connection_retries=-1,
    retry_delay=2,
)

from . import (  # noqa: E402, F401
    actions,
    admins,
    base,
    callbacks,
    func,
    games,
    global_checks,
    mailing,
    notes,
    referrals,
    shop,
    states,
    statistic,
    tickets,
    forum,
)
