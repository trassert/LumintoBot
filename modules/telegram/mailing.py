import asyncio

from .client import client

from .. import db, phrase

from loguru import logger
from telethon import events
from datetime import datetime
from telethon.tl.custom import Message

logger.info(f"Загружен модуль {__name__}!")


async def send_to_subscribers(message_text):
    """Отправка сообщения всем подписчикам"""
    data = db.mailing_get()
    subscribers = data.get("subscribers", [])

    if not subscribers:
        return 0

    successful_sends = 0
    for user_id in subscribers:
        try:
            await client.send_message(
                user_id,
                f"{phrase.mailing.new}\n\n{message_text}\n\n__{phrase.mailing.upd_hint}__",
            )
            successful_sends += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.info(f"Ошибка отправки пользователю {user_id}: {e}")

    return successful_sends


@client.on(events.NewMessage(pattern=r"(?i)^\+обновление ([\s\S]+)"))
async def admin_broadcast(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(level=roles.ADMIN, name=phrase.roles.admin)
        )
    await event.reply(
        phrase.mailing.done.format(
            await send_to_subscribers(event.pattern_match.group(1).strip())
        )
    )


@client.on(events.NewMessage(pattern=r"(?i)^\+обновления"))
async def subscribe_command(event: Message):
    """Обработчик команды подписки"""
    data = db.mailing_get()
    subscribers = data.get("subscribers", [])

    if event.sender_id in subscribers:
        return await event.reply(phrase.mailing.already_subscribe)
    subscribers.append(event.sender_id)
    data["subscribers"] = subscribers
    db.mailing_save(data)
    return await event.reply(phrase.mailing.subscribe)


@client.on(events.NewMessage(pattern=r"(?i)^\/отписаться$"))
async def unsubscribe_command(event: Message):
    """Обработчик команды отписки"""
    data = db.mailing_get()
    subscribers = data.get("subscribers", [])

    if event.sender_id not in subscribers:
        return await event.reply(phrase.mailing.already_unsub)
    subscribers.remove(event.sender_id)
    data["subscribers"] = subscribers
    db.mailing_save(data)
    return await event.reply(phrase.mailing.unsub)
