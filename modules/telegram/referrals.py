import re

from loguru import logger
from telethon import events
from telethon.tl.custom import Message

from .. import db, phrase
from . import func
from .client import client
from .global_checks import checks

logger.info(f"Загружен модуль {__name__}!")


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
    if await ref.check_ref(arg) is not None:
        return await event.reply(phrase.ref.already_exists)
    if await ref.get_own(event.sender_id) is not None:
        await ref.add_own(event.sender_id, arg)
        return await event.reply(phrase.ref.edited.format(arg))
    await ref.add_own(event.sender_id, arg)
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
    return await event.reply(phrase.ref.notext)


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
    if await db.RefCodes().delete(event.sender_id) is False:
        return await event.reply(phrase.ref.not_found)
    return await event.reply(phrase.ref.deleted)


@client.on(events.NewMessage(pattern=r"(?i)^/топреф$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топрефералов$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топрефералы$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ рефералы$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ реф$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ рефералов$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/рефералы топ$", func=checks))
async def top_ref(event: Message):
    text = [phrase.ref.top]
    info = await db.RefCodes().get_top_uses()
    n = 1
    for chunk in info:
        text.append(
            f"{n}. **{await func.get_name(int(chunk[0]))}** - {chunk[1]}"
        )
        n += 1
        if n > 10:
            break
    if n == 1:
        return await event.reply(phrase.ref.top_empty)
    return await event.reply("\n".join(text))


@client.on(events.NewMessage(pattern=r"(?i)^/рефка$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/рефкод$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/моярефка$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мойрефкод$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/реферальныйкод$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/реферальный код$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/refcode", func=checks))
async def my_ref(event: Message):
    ref = db.RefCodes()
    name = await ref.get_own(event.sender_id)
    if name is None:
        return await event.reply(phrase.ref.not_found)
    uses = await ref.check_uses(event.sender_id)
    if len(uses) == 0:
        uses = "0"
    else:
        players = []
        for player in uses:
            players.append(await func.get_name(player, minecraft=True))
        uses = f"{len(uses)}: {', '.join(players)}"
    return await event.reply(phrase.ref.my.format(name=name, uses=uses))
