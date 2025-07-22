from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from telethon import events

from .client import client
from .func import get_name

from .. import config, phrase


@client.on(events.ChatAction(chats=config.chats.chat))
async def chat_action(event: events.ChatAction.Event):
    user_name = await get_name(event.user_id, push=False)
    if event.user_left:
        return await client.send_message(
            config.chats.chat, phrase.chataction.leave.format(user_name)
        )
    elif event.user_joined:
        return await client.send_message(
            config.chats.chat, phrase.chataction.hello.format(user_name)
        )
