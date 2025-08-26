from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from telethon import events

from .client import client
from .func import get_name

from .. import config, phrase, formatter, db


@client.on(events.ChatAction(chats=config.chats.chat))
async def chat_action(event: events.ChatAction.Event):
    user_name = await get_name(event.user_id, push=False)
    if event.user_left:
        return await client.send_message(
            config.chats.chat, phrase.chataction.leave.format(user_name)
        )
    elif event.user_joined or event.user_added:
        if formatter.check_zalgo(user_name) > 50:
            await client.edit_permissions(
                config.chats.chat, event.user_id, send_messages=False
            )
            return await client.send_message(
                config.chats.chat,
                phrase.chataction.zalgo.format(user_name),
                silent=False,
            )
        if db.hellomsg_check(event.user_id) is False:
            logger.info(f"{event.user_id} вступил, но приветствие уже было.")
            return
        logger.info(f"Новый участник в чате - {event.user_id}")
        return await client.send_message(
            config.chats.chat, phrase.chataction.hello.format(user_name)
        )
