from loguru import logger
from telethon import events, Button

from .. import config, formatter, phrase
from .client import client
from .func import get_name

logger.info(f"Загружен модуль {__name__}!")


@client.on(events.ChatAction(chats=config.chats.chat))
async def chat_action(event: events.ChatAction.Event):
    user_name = await get_name(event.user_id, push=False)

    if event.user_left:
        return await client.send_message(
            config.chats.chat,
            phrase.chataction.leave.format(user_name),
        )

    if event.user_joined or event.user_added:
        await client.edit_permissions(
            config.chats.chat,
            event.user_id,
            send_messages=False,
        )
        if formatter.check_zalgo(user_name) > 50:
            return await client.send_message(
                config.chats.chat,
                phrase.chataction.zalgo.format(user_name),
                silent=False,
            )

        logger.info(f"Новый участник в чате - {event.user_id}")
        return await client.send_message(
            config.chats.chat,
            phrase.chataction.test.format(user_name),
            buttons=[
                [
                    Button.inline(
                        phrase.chataction.test_btn, f"test.{event.user_id}"
                    )
                ],
            ],
        )
