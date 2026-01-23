import urllib.parse

from telethon.tl.custom import Message
from telethon.tl.types import (
    KeyboardButtonRow,
    ReplyInlineMarkup,
    KeyboardButtonUrl,
)

from loguru import logger
from . import func
from .. import phrase, config, db, formatter
from .client import client

logger.info(f"Загружен модуль {__name__}!")


@func.new_command(r"\+товар (.+)")
async def add_trade(event: Message):
    if not event.is_private:
        return await event.reply(phrase.trade.private)

    username = await func.get_simple_push(event.sender_id)
    if username is None:
        return await event.reply(phrase.trade.username)

    arg = event.pattern_match.group(1).strip().lower()

    async with client.conversation(event.sender_id, timeout=300) as conv:

        async def ask_int(
            prompt: str, error_not_int: str, error_not_positive: str
        ) -> int | None:
            while True:
                await conv.send_message(prompt)
                try:
                    resp = await conv.get_response()
                except TimeoutError:
                    await event.reply(phrase.trade.timeout)
                    return None

                text = resp.raw_text.strip().lower()
                if text == "/стоп":
                    await conv.send_message(phrase.trade.cancel)
                    return None

                if not text.isdigit():
                    await conv.send_message(error_not_int)
                    continue

                value = int(text)
                if value < 1:
                    await conv.send_message(error_not_positive)
                    continue

                return value

        count = await ask_int(
            phrase.trade.count,
            phrase.trade.count_is_int,
            phrase.trade.more_than_0,
        )
        if count is None:
            return

        price = await ask_int(
            phrase.trade.price,
            phrase.trade.price_is_int,
            phrase.trade.more_than_0,
        )
        if price is None:
            return

    parsed_text = urllib.parse.quote(
        f"Хочу купить у тебя {arg}. Предложение актуально?"
    )
    url = f"https://t.me/{username}?text={parsed_text}"

    message: Message = await client.send_message(
        config.chats.chat,
        phrase.trade.done.format(
            item=arg,
            count=count,
            price=formatter.value_to_str(price, phrase.currency),
        ),
        reply_to=config.chats.topics.trade,
        buttons=ReplyInlineMarkup(
            [
                KeyboardButtonRow(
                    [
                        KeyboardButtonUrl(text="🛒 Купить", url=url),
                    ]
                ),
            ]
        ),
    )

    await db.add_item(message.id, event.sender_id, arg, count, price)
    await event.reply(
        phrase.trade.ok.format(
            item=arg.capitalize(),
            price=formatter.value_to_str(price, phrase.currency),
            count=count,
            id=message.id,
        )
    )
