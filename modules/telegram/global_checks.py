from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from telethon import events

from .. import db, phrase

from . import func

async def checks(event):
    roles = db.roles()
    if event.is_private:
        name = await func.get_name(event.sender_id, push=True)
        (
            logger.info(f"ЛС - {name} > {event.text}")
            if len(event.text) < 100
            else logger.info(f"ЛС - {name} > {event.text[:100]}...")
        )
    if roles.get(event.sender_id) == roles.BLACKLIST:
        if isinstance(event, events.CallbackQuery.Event):
            await event.answer(phrase.blacklisted, alert=True)
        await event.reply(phrase.blacklisted)
        return False
    return True
