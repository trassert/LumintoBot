from loguru import logger
from telethon import events

from .. import db, phrase
from . import func

logger.info(f"Загружен модуль {__name__}!")


async def checks(event) -> bool:
    roles = db.roles()
    if event.is_private:
        if not isinstance(event, events.CallbackQuery.Event):
            name = await func.get_name(event.sender_id, push=True)
            (
                logger.info(f"ЛС - {name} > {event.text}")
                if len(event.text) < 100
                else logger.info(f"ЛС - {name} > {event.text[:100]}...")
            )
    if roles.get(event.sender_id) != roles.BLACKLIST:
        return True
    if isinstance(event, events.CallbackQuery.Event):
        await event.answer(phrase.blacklisted, alert=True)
        return False
    await event.reply(phrase.blacklisted)
    return False
