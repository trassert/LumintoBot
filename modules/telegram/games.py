from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

import asyncio

from random import randint, random

from telethon import events
from telethon.tl.custom import Message
from telethon.tl.types import KeyboardButtonCallback
from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback,
)

from .client import client
from .global_checks import *

from .. import config, phrase, ai, formatter


@client.on(events.NewMessage(config.chats.chat, pattern=r"(?i)^/казино$", func=checks))
async def casino(event: Message):
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None) != config.chats.topics.games
    ):
        return await event.reply(phrase.game_topic_warning)
    keyboard = [
        [
            KeyboardButtonCallback(
                text="🎰 Автоматическая прокрутка", data=b"casino.auto"
            )
        ]
    ]
    return await event.reply(
        phrase.casino.start.format(config.coofs.PriceForCasino), buttons=keyboard
    )


@client.on(events.NewMessage(pattern=r"(?i)^/крокодил$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/crocodile$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^старт крокодил$", func=checks))
async def crocodile(event: Message):
    if not event.chat_id == config.chats.chat:
        return await event.reply(phrase.crocodile.chat)
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None) != config.chats.topics.games
    ):
        return await event.reply(phrase.game_topic_warning)
    else:
        pass
    if db.database("current_game") == 0:
        keyboard = ReplyInlineMarkup(
            [
                KeyboardButtonRow(
                    [
                        KeyboardButtonCallback(
                            text="✅ Играть", data=b"crocodile.start"
                        ),
                        KeyboardButtonCallback(
                            text="❌ Остановить игру", data=b"crocodile.stop"
                        ),
                    ]
                )
            ]
        )
        return await event.reply(phrase.crocodile.game, buttons=keyboard)
    else:
        keyboard = ReplyInlineMarkup(
            [
                KeyboardButtonRow(
                    [
                        KeyboardButtonCallback(
                            text="❌ Остановить игру", data=b"crocodile.stop"
                        )
                    ]
                )
            ]
        )
        return await event.reply(phrase.crocodile.no, buttons=keyboard)


@client.on(events.NewMessage(pattern=r"(?i)^/ставка(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/крокоставка(.*)", func=checks))
async def crocodile_bet(event: Message):
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None) != config.chats.topics.games
    ):
        return await event.reply(phrase.game_topic_warning)
    try:
        bet = int(event.pattern_match.group(1).strip())
        if bet < db.database("min_bet"):
            return await event.reply(
                phrase.money.min_count.format(
                    formatter.value_to_str(db.database("min_bet"), "изумруд")
                )
            )
        elif bet > db.database("max_bet"):
            return await event.reply(
                phrase.money.max_count.format(
                    formatter.value_to_str(db.database("max_bet"), "изумруд")
                )
            )
    except IndexError:
        bet = db.database("min_bet")
    except ValueError:
        return await event.reply(phrase.money.nan_count)
    sender_balance = db.get_money(event.sender_id)
    if sender_balance < bet:
        return await event.reply(
            phrase.money.not_enough.format(
                formatter.value_to_str(sender_balance, "изумруд")
            )
        )
    if db.database("current_game") != 0:
        return await event.reply(phrase.crocodile.no)
    all_bets = db.database("crocodile_bets")
    if str(event.sender_id) in all_bets:
        return await event.reply(phrase.crocodile.bet_already)
    db.add_money(event.sender_id, -bet)
    all_bets[str(event.sender_id)] = bet
    db.database("crocodile_bets", all_bets)
    return await event.reply(
        phrase.crocodile.bet.format(formatter.value_to_str(bet, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/суперигра(.*)", func=checks))
async def super_game(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(level=roles.ADMIN, name=phrase.roles.admin)
        )
    arg = event.pattern_match.group(1).strip()
    bets = db.database("crocodile_bets")
    bets[str(config.tokens.bot.creator)] = 50
    db.database("crocodile_bets", bets)
    db.database("crocodile_super_game", 1)
    db.database("max_bet", 100)
    db.database("min_bet", 50)
    await client.send_message(config.chats.chat, phrase.crocodile.super_game_wait)
    await asyncio.sleep(60)
    db.database("current_game", {"hints": [], "unsec": "_" * len(arg), "word": arg})
    client.add_event_handler(
        crocodile_hint, events.NewMessage(pattern=r"(?i)^/подсказка")
    )
    client.add_event_handler(
        crocodile_handler, events.NewMessage(chats=config.chats.chat)
    )
    return await client.send_message(config.chats.chat, phrase.crocodile.super_game)


async def crocodile_handler(event: Message):
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None) != config.chats.topics.games
    ):
        return
    text = event.text.strip().lower()
    if not len(text) > 0:
        return
    current_word = db.database("current_game")["word"]
    current_mask = list(db.database("current_game")["unsec"])
    if text == current_word:
        bets = db.database("crocodile_bets")
        all = 0
        bets_str = ""
        topers = []
        n = 1
        for toper in db.crocodile_stat.get_all().keys():
            if n > config.coofs.TopLowerBets:
                break
            topers.append(toper)
            n += 1
        if bets != {}:
            for key in list(bets.keys()):
                if str(event.sender_id) == key:
                    if str(event.sender_id) in topers:
                        all += round(bets[key] * config.coofs.TopBets)
                    else:
                        all += round(bets[key] * config.coofs.CrocodileBetCoo)
                else:
                    all += bets[key]
            db.add_money(event.sender_id, all)
            bets_str = phrase.crocodile.bet_win.format(
                formatter.value_to_str(all, "изумруд"),
            )
        db.database("current_game", 0)
        db.database("crocodile_bets", {})
        db.database("crocodile_last_hint", 0)
        if db.database("crocodile_super_game") == 1:
            db.database("crocodile_super_game", 0)
            db.database("max_bet", config.coofs.CrocodileDefaultMaxBet)
            db.database("min_bet", config.coofs.CrocodileDefaultMinBet)
        client.remove_event_handler(crocodile_hint)
        client.remove_event_handler(crocodile_handler)
        db.crocodile_stat(event.sender_id).add()
        return await event.reply(phrase.crocodile.win.format(current_word) + bets_str)
    else:
        pass
    if text[0] != "/":
        if len(text) > len(current_word):
            n = 0
            for x in current_word:
                if x == text[n] and current_mask[n] == "_":
                    current_mask[n] = x
                n = n + 1
        else:
            n = 0
            for x in text:
                if x == current_word[n] and current_mask[n] == "_":
                    current_mask[n] = x
                n = n + 1
        if "".join(current_mask) == current_word:
            current_mask[randint(0, len(current_mask) - 1)] = "_"
            cgame = db.database("current_game")
            cgame["unsec"] = "".join(current_mask)
            db.database("current_game", cgame)
            return await event.reply(
                phrase.crocodile.new.format("".join(current_mask).replace("_", ".."))
            )
        if list(db.database("current_game")["unsec"]) != current_mask:
            cgame = db.database("current_game")
            cgame["unsec"] = "".join(current_mask)
            db.database("current_game", cgame)
            return await event.reply(
                phrase.crocodile.new.format("".join(current_mask).replace("_", ".."))
            )


async def crocodile_hint(event: Message):
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None) != config.chats.topics.games
    ):
        return await event.reply(phrase.game_topic_warning)
    game = db.database("current_game")
    hint = game["hints"]
    if event.sender_id in hint:
        return await event.reply(phrase.crocodile.hints_all)
    hint.append(event.sender_id)
    game["hints"] = hint
    db.database("current_game", game)
    word = game["word"]
    if (random() < config.coofs.PercentForRandomLetter) and (len(hint) > 0):
        n = 1
        for letter in list(game["unsec"]):
            if letter == "_":
                return await event.reply(f'{n} буква в слове - **{game["word"][n-1]}**')
            n += 1
    return await event.reply((await ai.crocodile.send_message(word)).text)


if db.database("current_game") != 0:
    client.add_event_handler(
        crocodile_handler, events.NewMessage(chats=config.chats.chat)
    )
    client.add_event_handler(
        crocodile_hint, events.NewMessage(pattern=r"(?i)^/подсказка$", func=checks)
    )
