from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

import asyncio

from telethon import events, types

from random import choice

from .client import client
from .global_checks import *
from .func import get_name
from .games import crocodile_handler, crocodile_hint

from .. import config, pathes, phrase, db, dice, formatter, floodwait
from ..mcrcon import MinecraftClient


WaitCasino = floodwait.FloodWaitBase("WaitCasino", config.flood.casino)


@client.on(events.CallbackQuery(func=checks))
async def callback_action(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"{event.sender_id} отправил КБ - {data}")
    if data[0] == "crocodile":
        if data[1] == "start":
            if db.database("crocodile_super_game") == 1:
                return await event.answer(phrase.crocodile.super_game_here, alert=True)
            if db.database("current_game") != 0:
                return await event.answer(phrase.crocodile.no, alert=True)
            with open(pathes.crocodile_path, "r", encoding="utf8") as f:
                word = choice(f.read().split("\n"))
            unsec = ""
            for x in list(word):
                if x.isalpha():
                    unsec += "_"
                elif x == " ":
                    unsec += x
            db.database("current_game", {"hints": [], "word": word, "unsec": unsec})
            client.add_event_handler(
                crocodile_hint, events.NewMessage(pattern=r"(?i)^/подсказка")
            )
            client.add_event_handler(
                crocodile_handler, events.NewMessage(chats=event.chat_id)
            )
            return await event.reply(phrase.crocodile.up)
        elif data[1] == "stop":
            entity = await client.get_entity(event.sender_id)
            user = (
                f"@{entity.username}"
                if entity.username
                else entity.first_name + " " + entity.last_name
            )
            if db.database("current_game") == 0:
                return await event.answer(phrase.crocodile.already_down, alert=True)
            if db.database("crocodile_super_game") == 1:
                return await event.answer(phrase.crocodile.super_game_here, alert=True)
            bets_json = db.database("crocodile_bets")
            if bets_json != {}:
                bets = round(sum(list(bets_json.values())) / 2)
                bets = 1 if bets < 1 else bets
                sender_balance = db.get_money(event.sender_id)
                if sender_balance < bets:
                    return await event.answer(
                        phrase.crocodile.not_enough.format(
                            formatter.value_to_str(sender_balance, "изумруд")
                        ),
                        alert=True,
                    )
                db.add_money(event.sender_id, -bets)
            word = db.database("current_game")["word"]
            db.database("current_game", 0)
            db.database("crocodile_last_hint", 0)
            client.remove_event_handler(crocodile_hint)
            client.remove_event_handler(crocodile_handler)
            if bets_json != {}:
                return await event.reply(
                    phrase.crocodile.down_payed.format(
                        user=user, money=formatter.value_to_str(bets, "изумруд"), word=word
                    )
                )
            return await event.reply(phrase.crocodile.down.format(word))
    elif data[0] == "shop":
        if int(data[-1]) != db.database("shop_version"):
            return await event.answer(phrase.shop.old, alert=True)
        nick = db.nicks(id=event.sender_id).get()
        if nick is None:
            return await event.answer(phrase.nick.not_append, alert=True)
        shop = db.get_shop()
        del shop["theme"]
        balance = db.get_money(event.sender_id)
        items = list(shop.keys())
        item = shop[items[int(data[1])]]
        if balance < item["price"]:
            return await event.answer(
                phrase.money.not_enough.format(formatter.value_to_str(balance, "изумруд")),
                alert=True,
            )
        try:
            async with MinecraftClient(
                host=db.database("ipv4"),
                port=config.tokens.rcon.port,
                password=config.tokens.rcon.password,
            ) as rcon:
                command = f'invgive {nick} {item["name"]} {item["value"]}'
                logger.info(f"Выполняется команда: {command}")
                await rcon.send(command)
        except TimeoutError:
            return await event.answer(phrase.shop.timeout, alert=True)
        db.add_money(event.sender_id, -item["price"])
        return await event.answer(
            phrase.shop.buy.format(items[int(data[1])]), alert=True
        )
    elif data[0] == "word":
        user_name = await get_name(data[3])
        if data[1] == "yes":
            with open(pathes.crocodile_path, "a", encoding="utf-8") as f:
                f.write(f"\n{data[2]}")
            db.add_money(data[3], config.coofs.WordRequest)
            await client.send_message(
                config.chats.chat,
                phrase.word.success.format(
                    word=data[2],
                    user=user_name,
                    money=formatter.value_to_str(config.coofs.WordRequest, "изумруд"),
                ),
            )
            return await client.edit_message(
                event.sender_id, event.message_id, phrase.word.add
            )
        if data[1] == "no":
            with open(pathes.crocodile_blacklist_path, "a", encoding="utf-8") as f:
                f.write(f"\n{data[2]}")
            await client.send_message(
                config.chats.chat, phrase.word.no.format(word=data[2], user=user_name)
            )
            return await client.edit_message(
                event.sender_id, event.message_id, phrase.word.noadd
            )
    elif data[0] == "nick":
        if event.sender_id != int(data[2]):
            return await event.answer(phrase.not_for_you)
        if db.nicks(id=event.sender_id).get() == data[1]:
            return await event.answer(phrase.nick.already_you, alert=True)
        balance = db.get_money(event.sender_id)
        if balance - config.coofs.PriceForChangeNick < 0:
            return await event.answer(
                phrase.money.not_enough.format(formatter.value_to_str(balance, "изумруд"))
            )
        db.add_money(event.sender_id, -config.coofs.PriceForChangeNick)
        db.nicks(data[1], event.sender_id).link()
        user_name = await get_name(data[2])
        return await event.reply(
            phrase.nick.buy_nick.format(
                user=user_name,
                price=formatter.value_to_str(config.coofs.PriceForChangeNick, "изумруд"),
            )
        )
    elif data[0] == "casino":
        request = WaitCasino.request()
        if request is not True:
            return await event.answer(
                phrase.casino.floodwait.format(request),
                alert=True
            )
        if data[1] == "auto":
            balance = db.get_money(event.sender_id)
            if balance < config.coofs.PriceForCasino:
                return await event.answer(
                    phrase.money.not_enough.format(formatter.value_to_str(balance, "изумруд")),
                    alert=True,
                )
            db.add_money(event.sender_id, -config.coofs.PriceForCasino)
            media_dice = await client.send_file(
                event.chat_id,
                types.InputMediaDice("🎰"),
                reply_to=config.chats.topics.games,
            )
            fm = await event.reply(phrase.casino.wait)
            pos = dice.get(media_dice.media.value)
            if (pos[0] == pos[1]) and (pos[1] == pos[2]):
                await db.Users.add_win(event.sender_id)
                logger.info(f"{event.sender_id} - победил в казино")
                db.add_money(
                    event.sender_id,
                    config.coofs.PriceForCasino * config.coofs.CasinoWinRatio,
                )
                await asyncio.sleep(2)
                return await fm.edit(
                    phrase.casino.win_auto.format(
                        value=config.coofs.PriceForCasino * config.coofs.CasinoWinRatio,
                        name=await get_name(event.sender_id),
                    )
                )
            elif (pos[0] == pos[1]) or (pos[1] == pos[2]):
                db.add_money(event.sender_id, config.coofs.PriceForCasino)
                await asyncio.sleep(2)
                return await fm.edit(
                    phrase.casino.partially_auto.format(await get_name(event.sender_id))
                )
            else:
                await db.Users.add_lose_money(event.sender_id, config.coofs.PriceForCasino)
                logger.info(f"{event.sender_id} проиграл в казино")
                await asyncio.sleep(2)
                return await fm.edit(
                    phrase.casino.lose_auto.format(
                        name=await get_name(event.sender_id),
                        value=config.coofs.PriceForCasino,
                    )
                )
    elif data[0] == "state":
        if data[1] == "pay":
            nick = db.nicks(id=event.sender_id).get()
            if nick is None:
                return await event.answer(phrase.state.not_connected, alert=True)
            if db.states.if_player(event.sender_id) is not False:
                return await event.answer(phrase.state.already_player, alert=True)
            if db.states.if_author(event.sender_id) is not False:
                return await event.answer(phrase.state.already_author, alert=True)
            balance = db.get_money(event.sender_id)
            state = db.state(data[2])
            if state.price > balance:
                return await event.answer(
                    phrase.money.not_enough.format(formatter.value_to_str(balance, "изумруд")),
                    alert=True,
                )
            db.add_money(event.sender_id, -state.price)
            state.change("money", state.money + state.price)
            players = state.players
            players.append(event.sender_id)
            state.change("players", players)
            await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.new_player.format(state=state.name, player=nick),
                reply_to=config.chats.topics.rp,
            )
            if (state.type == 0) and (len(players) >= config.coofs.Type1Players):
                await client.send_message(
                    entity=config.chats.chat,
                    message=phrase.state.up.format(name=state.name, type="Государство"),
                    reply_to=config.chats.topics.rp,
                )
                state.change("type", 1)
            if (state.type == 1) and (len(players) >= config.coofs.Type2Players):
                await client.send_message(
                    entity=config.chats.chat,
                    message=phrase.state.up.format(name=state.name, type="Империя"),
                    reply_to=config.chats.topics.rp,
                )
                state.change("type", 2)
            return await event.answer(phrase.state.admit.format(state.name), alert=True)
        elif data[1] == "remove":
            try:
                state = db.state(data[2])
            except FileNotFoundError:
                return await event.answer(phrase.state.already_deleted, alert=True)
            if event.sender_id != state.author:
                return await event.answer(phrase.not_for_you, alert=True)
            db.add_money(state.author, state.money)
            if db.states.remove(data[2]) != True:
                return await event.answer(phrase.error, alert=True)
            await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.rem_public.format(name=data[2]),
                reply_to=config.chats.topics.rp,
            )
            return await event.reply(
                phrase.state.removed.format(
                    author=await get_name(state.author, push=False)
                )
            )
        elif data[1] == "m":
            if event.sender_id != int(data[2]):
                return await event.answer(phrase.not_for_you, alert=True)
            state_name: str = data[3].capitalize()
            balance = db.get_money(event.sender_id)
            if balance < config.coofs.PriceForNewState:
                return await event.answer(
                    phrase.money.not_enough.format(
                        formatter.value_to_str(balance, "изумруд")
                    ),
                    alert=True
                )
            if db.states.check(state_name) is True:
                return await event.answer(phrase.state.already_here, alert=True)
            db.add_money(event.sender_id, -config.coofs.PriceForNewState)
            db.states.add(state_name, event.sender_id)
            await event.reply(
                phrase.state.make_by_callback.format(
                    author=await get_name(event.sender_id),
                    state_name=state_name
                )
            )
            return await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.make.format(state_name),
                reply_to=config.chats.topics.rp,
            )
