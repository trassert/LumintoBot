from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from telethon import events
from telethon.tl.custom import Message

from .client import client
from .global_checks import *
from .func import get_name

from .. import (
    phrase,
    formatter
)

@client.on(events.NewMessage(pattern=r"(?i)^\+чек(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+ticket(.*)", func=checks))
async def do_ticket(event: Message):
    if not event.is_private:
        return await event.reply(phrase.ticket.in_chat)
    arg = event.pattern_match.group(1).strip()
    if arg == "":
        return await event.reply(phrase.ticket.no_value)
    try:
        arg = int(arg)
    except ValueError:
        return await event.reply(phrase.ticket.not_int)
    if arg < 1:
        return await event.reply(phrase.ticket.bigger_than_zero)
    balance = db.get_money(event.sender_id)
    if balance < arg:
        return await event.reply(
            phrase.money.not_enough.format(formatter.value_to_str(balance, "изумруд"))
        )
    db.add_money(event.sender_id, -arg)
    ticket_id = db.ticket.add(event.sender_id, arg)
    return await event.reply(
        phrase.ticket.added.format(
            value=arg, author=await get_name(event.sender_id), id=ticket_id
        )
    )


@client.on(events.NewMessage(pattern=r"(?i)^/чек(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ticket(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/активировать(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^активировать(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/activate(.*)", func=checks))
async def get_ticket(event: Message):
    arg = event.pattern_match.group(1).strip()
    if arg == "":
        return await event.reply(phrase.ticket.no_value)
    ticket_info = db.ticket.get(arg)
    if ticket_info is None:
        return await event.reply(phrase.ticket.no_such)
    db.add_money(event.sender_id, ticket_info["value"])
    db.ticket.delete(arg)
    return await event.reply(
        phrase.ticket.got.format(
            author=await get_name(ticket_info["author"]),
            value=formatter.value_to_str(ticket_info["value"], "изумруд"),
        )
    )
