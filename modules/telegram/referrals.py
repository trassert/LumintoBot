from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon import errors as TGErrors
from telethon import events
from telethon.tl.custom import Message


