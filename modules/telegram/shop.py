from random import choice

from loguru import logger
from telethon import events
from telethon.tl.custom import Message
from telethon.tl.types import (
    KeyboardButtonCallback,
    KeyboardButtonRow,
    ReplyInlineMarkup,
)

from .. import db, formatter, phrase, task_gen
from .client import client
from .global_checks import checks

logger.info(f"Загружен модуль {__name__}!")


@client.on(events.NewMessage(pattern=r"(?i)^/shop", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/шоп$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/магазин$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^магазин$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^shop$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^шоп$", func=checks))
async def shop(event: Message):
    shop_data = db.get_shop()
    version = await db.database("shop_version")
    theme = shop_data.pop("theme")
    theme_data = phrase.shop_quotes[theme]

    items_lines = []
    button_callbacks = []

    for idx, (item_name, item_info) in enumerate(list(shop_data.items())[:5]):
        value = item_info["value"]
        price = formatter.value_to_str(item_info["price"], "изумруд")
        value_str = f" ({value})" if value != 1 else ""
        items_lines.append(f"{idx + 1}. {item_name}{value_str} - {price}")

        button_callbacks.append(
            KeyboardButtonCallback(
                text=f"{idx + 1}\u20e3",
                data=f"shop.{idx}.{version}".encode(),
            )
        )

    keyboard = ReplyInlineMarkup([KeyboardButtonRow(button_callbacks)])

    formatted_items = "\n".join(items_lines)
    quote = choice(theme_data["quotes"])
    emo = theme_data["emo"]
    clock = formatter.fmtime(await task_gen.UpdateShopTask.info())

    return await event.reply(
        phrase.shop.shop.format(
            quote=quote,
            emo=emo,
            items=formatted_items,
            clock=clock,
        ),
        buttons=keyboard,
        parse_mode="html",
    )
