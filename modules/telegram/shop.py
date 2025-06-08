from telethon import events
from telethon.tl.custom import Message
from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback,
)

from random import choice

from .client import client
from .global_checks import *

from ..formatter import decline_number
from .. import (
    phrase,
)

@client.on(events.NewMessage(pattern=r"(?i)^/shop", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/шоп$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/магазин$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^магазин$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^shop$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^шоп$", func=checks))
async def shop(event: Message):
    version = db.database("shop_version")
    keyboard = ReplyInlineMarkup(
        [
            KeyboardButtonRow(
                [
                    KeyboardButtonCallback(text="1️⃣", data=f"shop.0.{version}".encode()),
                    KeyboardButtonCallback(text="2️⃣", data=f"shop.1.{version}".encode()),
                    KeyboardButtonCallback(text="3️⃣", data=f"shop.2.{version}".encode()),
                    KeyboardButtonCallback(text="4️⃣", data=f"shop.3.{version}".encode()),
                    KeyboardButtonCallback(text="5️⃣", data=f"shop.4.{version}".encode()),
                ]
            )
        ]
    )
    shop = db.get_shop()
    theme = shop["theme"]
    del shop["theme"]
    items = list(shop.keys())
    return await event.reply(
        phrase.shop.shop.format(
            trade_1=items[0],
            value_1=(
                f" ({shop[items[0]]['value']})" if shop[items[0]]["value"] != 1 else ""
            ),
            price_1=decline_number(shop[items[0]]["price"], "изумруд"),
            trade_2=items[1],
            value_2=(
                f" ({shop[items[1]]['value']})" if shop[items[1]]["value"] != 1 else ""
            ),
            price_2=decline_number(shop[items[1]]["price"], "изумруд"),
            trade_3=items[2],
            value_3=(
                f" ({shop[items[2]]['value']})" if shop[items[2]]["value"] != 1 else ""
            ),
            price_3=decline_number(shop[items[2]]["price"], "изумруд"),
            trade_4=items[3],
            value_4=(
                f" ({shop[items[3]]['value']})" if shop[items[3]]["value"] != 1 else ""
            ),
            price_4=decline_number(shop[items[3]]["price"], "изумруд"),
            trade_5=items[4],
            value_5=(
                f" ({shop[items[4]]['value']})" if shop[items[4]]["value"] != 1 else ""
            ),
            price_5=decline_number(shop[items[4]]["price"], "изумруд"),
            quote=choice(phrase.shop_quotes[theme]["quotes"]),
            emo=phrase.shop_quotes[theme]["emo"],
        ),
        buttons=keyboard,
        parse_mode="html",
    )
