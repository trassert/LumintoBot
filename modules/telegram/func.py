import random
import re

from loguru import logger
from telethon.tl import types
from telethon.tl.functions.users import GetFullUserRequest

from .. import db
from .client import client

logger.info(f"Загружен модуль {__name__}!")


async def get_name(id, push=False, minecraft=False) -> str | None:
    """Выдает имя + фамилия, либо @пуш."""
    try:
        if minecraft is True:
            nick = db.nicks(id=int(id)).get()
            if nick is not None:
                return f"[{nick}](tg://user?id={id})"
        user_name = await client.get_entity(int(id))
        if user_name.username is not None and push:
            return f"@{user_name.username}"
        if user_name.username is None or not push:
            fn = user_name.first_name.replace("[", "(").replace("]", ")")
            if user_name.last_name is None:
                return f"[{fn}](tg://user?id={id})"
            ln = user_name.last_name.replace("[", "(").replace("]", ")")
            return f"[{fn} {ln}](tg://user?id={id})"
        return f"@{user_name.username}"
    except Exception:
        return "Неопознанный персонаж"


async def get_id(str: str) -> int:
    if str[-1] == ",":
        str = str[:-1]
    if str.isdigit():
        if bool(re.fullmatch(r"^@\d+$", str)):
            str = str[1:]
        check = await get_name(int(str))
        if check == "Неопознанный персонаж":
            return None
        return int(str)
    user = await client(GetFullUserRequest(str))
    return user.full_user.id


async def make_quiz_poll(answers: list, correct_answer_id: int, question: str) -> types.MessageMediaPoll:
    return (
        types.MessageMediaPoll(
            poll=types.Poll(
                id=random.randint(1, 100000),
                question=types.TextWithEntities(
                    text=question, entities=[],
                ),
                answers=[
                    types.PollAnswer(
                        text=types.TextWithEntities(text=option, entities=[]),
                        option=bytes([i]),
                    )
                    for i, option in enumerate(answers, start=1)
                ],
                quiz=True,
            ),
            results=types.PollResults(
                results=[
                    types.PollAnswerVoters(
                        option=bytes([correct_answer_id]),
                        voters=0,
                        correct=True,
                    ),
                ],
            ),
        ),
    )


def get_reply_message_id(event):
    if event.reply_to is None:
        return None
    if not event.reply_to.forum_topic:
        return event.reply_to.reply_to_msg_id
    if event.reply_to.reply_to_top_id is None:
        return None
    return event.reply_to.reply_to_msg_id


async def get_author_by_msgid(chat_id: int, msg_id: int) -> int | None:
    if not msg_id or msg_id <= 0:
        return None
    msg = await client.get_messages(chat_id, ids=msg_id)
    print(msg)
    return msg.sender_id if msg else None