from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from .. import db
from .client import client


async def get_name(id, push=False, minecraft=False):
    "Выдает @пуш, если нет - имя + фамилия"
    try:
        if minecraft is True:
            nick = db.nicks(id=int(id)).get()
            if nick is not None:
                return f"[{nick}]" f"(tg://user?id={id})"
        user_name = await client.get_entity(int(id))
        if user_name.username is not None and push:
            return f"@{user_name.username}"
        elif user_name.username is None or not push:
            if user_name.last_name is None:
                return f"[{user_name.first_name}]" f"(tg://user?id={id})"
            else:
                return (
                    f"[{user_name.first_name} {user_name.last_name}]"
                    f"(tg://user?id={id})"
                )
        else:
            return f"@{user_name.username}"
    except Exception:
        return "Неопознанный персонаж"
