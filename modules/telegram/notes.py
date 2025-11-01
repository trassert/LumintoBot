from loguru import logger
from telethon import events
from telethon.tl.custom import Message

from .. import db, phrase
from .client import client
from .global_checks import checks

logger.info(f"Загружен модуль {__name__}!")


@client.on(
    events.NewMessage(pattern=r"(?i)^\+нот (.+)\n([\s\S]+)", func=checks),
)
@client.on(
    events.NewMessage(pattern=r"(?i)^\+note (.+)\n([\s\S]+)", func=checks),
)
async def add_note(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.VIP:
        return await event.reply(
            phrase.roles.no_perms.format(level=roles.VIP, name=phrase.roles.vip),
        )
    if (
        db.Notes().create(
            event.pattern_match.group(1).strip(),
            event.text.split("\n", maxsplit=1)[1],
        )
        is True
    ):
        return await event.reply(
            phrase.notes.new.format(event.pattern_match.group(1).strip()),
        )
    return await event.reply(phrase.notes.already_added)


@client.on(events.NewMessage(pattern=r"(?i)^\+нот (.+)$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+note (.+)$", func=checks))
async def add_note_notext(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.VIP:
        return await event.reply(
            phrase.roles.no_perms.format(level=roles.VIP, name=phrase.roles.vip),
        )
    return await event.reply(phrase.notes.notext)


@client.on(events.NewMessage(pattern=r"(?i)^\+нот\n([\s\S]+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+note\n([\s\S]+)", func=checks))
async def add_note_noname(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.VIP:
        return await event.reply(
            phrase.roles.no_perms.format(level=roles.VIP, name=phrase.roles.vip),
        )
    return await event.reply(phrase.notes.noname)


@client.on(events.NewMessage(pattern=r"(?i)^\.(.+)", func=checks))
async def get_note(event: Message):
    note_text = db.Notes().get(event.pattern_match.group(1).strip().lower())
    if note_text is not None:
        if event.reply_to_msg_id:
            reply_message: Message = await event.get_reply_message()
            return await client.send_message(
                event.chat_id,
                note_text,
                reply_to=reply_message.id,
                link_preview=False,
            )
        return await client.send_message(
            event.chat_id, note_text, reply_to=event.id, link_preview=False,
        )
    return None


@client.on(events.NewMessage(pattern=r"(?i)^/notes$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ноты$", func=checks))
async def get_all_notes(event: Message):
    text = ""
    n = 1
    for name in db.Notes().get_all():
        text += f"{n}. {name}\n"
        n += 1
    return await event.reply(phrase.notes.alltext.format(text))


@client.on(events.NewMessage(pattern=r"(?i)^\-нот (.+)$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-note (.+)$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-text (.+)$", func=checks))
async def del_note(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.VIP:
        return await event.reply(
            phrase.roles.no_perms.format(level=roles.VIP, name=phrase.roles.vip),
        )
    if not db.Notes().remove(event.pattern_match.group(1).strip()):
        return await event.reply(phrase.notes.not_found)
    return await event.reply(phrase.notes.deleted)


@client.on(events.NewMessage(pattern=r"(?i)^\-нот$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-note$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-text$", func=checks))
async def del_note_notext(event: Message):
    return await event.reply(phrase.note.noname)
