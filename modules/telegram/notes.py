from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from .client import client
from .global_checks import *

from telethon import events
from telethon.tl.custom import Message

from .. import db, phrase

@client.on(events.NewMessage(pattern=r"(?i)^\+нот (.+)\n([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+note (.+)\n([\s\S]+)", func=checks))
async def add_note(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.VIP:
        return await event.reply(
            phrase.roles.no_perms.format(level=roles.VIP, name=phrase.roles.vip)
        )
    if db.Notes().create(
        event.pattern_match.group(1).strip(),
        event.pattern_match.group(2).strip()
    ) is True:
        return await event.reply(phrase.notes.new.format(event.pattern_match.group(1).strip()))


@client.on(events.NewMessage(pattern=r"(?i)^\+нот (.+)$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+note (.+)$", func=checks))
async def add_note_notext(event: Message):
    return await event.reply(phrase.notes.notext)


@client.on(events.NewMessage(pattern=r"(?i)^\+нот\n([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+note\n([\s\S]+)", func=checks))
async def add_note_notext(event: Message):
    return await event.reply(phrase.notes.noname)