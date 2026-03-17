from aiogram import Router, types
from loguru import logger
from telethon import events

from .. import config, db, formatter, phrase
from . import func
from .client import client, dp

logger.info(f"Загружен модуль {__name__}!")

router = Router(name="actions")


@client.on(events.ChatAction(chats=config.chats.chat))
async def chat_action(event: events.ChatAction.Event):
    try:
        user_name = await func.get_name(event.user_id)
    except TypeError:
        return None

    if event.user_left:
        return await client.send_message(
            config.chats.chat,
            phrase.chataction.leave.format(user_name),
        )

    if event.user_joined or event.user_added:
        if formatter.check_zalgo(user_name) > 50:
            await client.edit_permissions(
                config.chats.chat,
                event.user_id,
                send_messages=False,
            )
            return await client.send_message(
                config.chats.chat,
                phrase.chataction.zalgo.format(user_name),
                silent=False,
            )
        if not db.hellomsg_check(event.user_id):
            return logger.info(f"{event.user_id} вступил, но приветствие уже было.")
        return await client.send_message(
            config.chats.chat,
            phrase.chataction.hello.format(await func.get_name(event.user_id)),
            link_preview=False,
        )
        logger.info(f"Новый участник в чате - {event.user_id}")
    return None


@router.chat_join_request()
async def handle_join_request(request: types.ChatJoinRequest):
    """Обработка запроса на вступление в чат."""
    user_id = request.from_user.id

    if await db.Nicks(id=user_id).get() is not None:
        logger.info(f"Пользователь {user_id} одобрен (ник привязан)")
        return await request.approve()

    await request.bot.send_message(
        chat_id=user_id,
        text=phrase.chataction.need_link,
        parse_mode="HTML",
        link_preview_options=types.LinkPreviewOptions(is_disabled=True),
    )
    logger.info(f"Пользователю {user_id} отправлена инструкция")
    return None


dp.include_router(router)
