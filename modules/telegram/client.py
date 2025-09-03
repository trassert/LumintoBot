from telethon.sync import TelegramClient

from .. import config, pathes
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")
client = TelegramClient(
    session=pathes.bot_path,
    api_id=config.tokens.bot.id,
    api_hash=config.tokens.bot.hash,
    device_model="Bot",
    system_version="4.16.30-vxCUSTOM",
    lang_code="ru",
    system_lang_code="ru",
)

from . import actions, admins, ai, base, callbacks, func, games, global_checks, shop, states, statistic, tickets, notes, referrals  # noqa: E402, F401
