from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

import re

from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon import errors as TGErrors
from telethon import events
from telethon.tl.custom import Message

from .client import client
from .global_checks import *
from .func import get_name

from .. import db


@client.on(events.NewMessage(pattern=r"(?i)^/addrefcode (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/новыйреф (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/новаярефка (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/новый реф (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+реф (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+рефка (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+рефкод (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/добавить рефку (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^добавить рефку (.+)", func=checks))
async def add_refcode(event: Message):
    arg = event.pattern_match.group(1).strip().lower()
    if not re.match("^[A-Za-z0-9_]*$", arg):
        return await event.reply(phrase.ref.not_regex)
    ref = db.RefCodes()
    if ref.check_ref(arg) is not None:
        return await event.reply(phrase.ref.already_exists)
    if ref.get_own(event.sender_id) is not None:
        ref.add_own(event.sender_id, arg)
        return await event.reply(phrase.ref.edited.format(arg))
    ref.add_own(event.sender_id, arg)
    return await event.reply(phrase.ref.added.format(arg))


@client.on(events.NewMessage(pattern=r"(?i)^/addrefcode$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/новыйреф$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/новаярефка$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/новый реф$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+реф$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+рефка$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+рефкод$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/добавить рефку$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^добавить рефку$", func=checks))
async def add_refcode_empty(event: Message):
    pass


@client.on(events.NewMessage(pattern=r"(?i)^/delrefcode$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/удалитьреф$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/удалитьрефку$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/удалить реф$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-реф$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-рефка$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-рефкод$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/удалить рефку$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^удалить рефку$", func=checks))
async def del_refcode(event: Message):
    pass