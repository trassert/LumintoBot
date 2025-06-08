from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from telethon import events

from .. import db, phrase


async def checks(event):
    roles = db.roles()
    if roles.get(event.sender_id) == roles.BLACKLIST:
        if isinstance(event, events.CallbackQuery.Event):
            await event.answer(phrase.blacklisted, alert=True)
        await event.reply(phrase.blacklisted)
        return False
    return True
