import asyncio
from random import choice, random, randint

from loguru import logger
from telethon import events, types
from telethon import Button

from .. import (
    config,
    db,
    dice,
    floodwait,
    formatter,
    mcrcon,
    pathes,
    phrase,
    mining,
)
from .client import client
from .func import get_name
from .games import crocodile_handler, crocodile_hint
from .global_checks import checks

logger.info(f"Загружен модуль {__name__}!")


@client.on(events.CallbackQuery(func=checks, pattern=r"^state"))
async def state_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (States), дата: {data}")
    if data[1] == "pay":
        nick = db.nicks(id=event.sender_id).get()
        if nick is None:
            return await event.answer(phrase.state.not_connected, alert=True)
        if db.states.if_player(event.sender_id) is not False:
            return await event.answer(phrase.state.already_player, alert=True)
        if db.states.if_author(event.sender_id) is not False:
            return await event.answer(phrase.state.already_author, alert=True)
        balance = await db.get_money(event.sender_id)
        state = db.state(data[2])
        if state.price > balance:
            return await event.answer(
                phrase.money.not_enough.format(
                    formatter.value_to_str(balance, "изумруд"),
                ),
                alert=True,
            )
        db.add_money(event.sender_id, -state.price)
        state.change("money", state.money + state.price)
        players = state.players
        players.append(event.sender_id)
        state.change("players", players)
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.new_player.format(
                state=state.name,
                player=nick,
            ),
            reply_to=config.chats.topics.rp,
        )
        if (state.type == 0) and (len(players) >= config.coofs.Type1Players):
            await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.up.format(
                    name=state.name,
                    type="Государство",
                ),
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
        return await event.answer(
            phrase.state.admit.format(state.name),
            alert=True,
        )
    if data[1] == "remove":
        try:
            state = db.state(data[2])
        except FileNotFoundError:
            return await event.answer(phrase.state.already_deleted, alert=True)
        if event.sender_id != state.author:
            return await event.answer(phrase.not_for_you, alert=True)
        db.add_money(state.author, state.money)
        if not db.states.remove(data[2]):
            return await event.answer(phrase.error, alert=True)
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.rem_public.format(name=data[2]),
            reply_to=config.chats.topics.rp,
        )
        return await event.reply(
            phrase.state.removed.format(
                author=await get_name(state.author, push=False),
            ),
        )
    if data[1] == "m":
        if event.sender_id != int(data[2]):
            return await event.answer(phrase.not_for_you, alert=True)
        state_name: str = data[3].capitalize()
        balance = await db.get_money(event.sender_id)
        if balance < config.coofs.PriceForNewState:
            return await event.answer(
                phrase.money.not_enough.format(
                    formatter.value_to_str(balance, "изумруд"),
                ),
                alert=True,
            )
        if db.states.check(state_name) is True:
            return await event.answer(phrase.state.already_here, alert=True)
        db.add_money(event.sender_id, -config.coofs.PriceForNewState)
        db.states.add(state_name, event.sender_id)
        await event.reply(
            phrase.state.make_by_callback.format(
                author=await get_name(event.sender_id),
                state_name=state_name,
            ),
        )
        return await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.make.format(state_name),
            reply_to=config.chats.topics.rp,
        )
    if data[1] == "rn":
        if event.sender_id != int(data[3]):
            return await event.answer(phrase.not_for_you)
        if db.states.check(data[2].capitalize()):
            return await event.answer(phrase.state.already_here, alert=True)
        state_name = db.states.if_author(event.sender_id)
        if state_name is False:
            return await event.answer(phrase.state.not_a_author, alert=True)
        balance = await db.get_money(event.sender_id)
        if balance - config.coofs.PriceForChangeStateNick < 0:
            return await event.answer(
                phrase.money.not_enough.format(
                    formatter.value_to_str(balance, "изумруд"),
                ),
                alert=True,
            )
        if db.state(state_name).rename(data[2].capitalize()) is False:
            return await event.answer(phrase.state.already_here, alert=True)
        db.add_money(event.sender_id, -config.coofs.PriceForChangeStateNick)
        await event.reply(
            phrase.state.renamed.format(
                old=state_name.capitalize(),
                new=data[2].capitalize(),
            ),
        )
        return await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.renamed.format(
                old=state_name.capitalize(),
                new=data[2].capitalize(),
            ),
            reply_to=config.chats.topics.rp,
        )
    return None


@client.on(events.CallbackQuery(func=checks, pattern=r"^casino"))
async def casino_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    request = floodwait.WaitCasino.request()
    if request is False:
        return await event.answer(phrase.casino.full_floodwait.format(request))
    logger.info(f"КБ кнопка (Casino), дата: {data}")
    if data[1] == "auto":
        balance = await db.get_money(event.sender_id)
        if balance < config.coofs.PriceForCasino:
            return await event.answer(
                phrase.money.not_enough.format(
                    formatter.value_to_str(balance, "изумруд"),
                ),
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
                    value=config.coofs.PriceForCasino
                    * config.coofs.CasinoWinRatio,
                    name=await get_name(event.sender_id),
                ),
            )
        if (pos[0] == pos[1]) or (pos[1] == pos[2]):
            db.add_money(event.sender_id, config.coofs.PriceForCasino)
            await asyncio.sleep(2)
            return await fm.edit(
                phrase.casino.partially_auto.format(
                    await get_name(event.sender_id),
                ),
            )
        await db.Users.add_lose_money(
            event.sender_id,
            config.coofs.PriceForCasino,
        )
        logger.info(f"{event.sender_id} проиграл в казино")
        await asyncio.sleep(2)
        return await fm.edit(
            phrase.casino.lose_auto.format(
                name=await get_name(event.sender_id),
                value=config.coofs.PriceForCasino,
            ),
        )
    return None


@client.on(events.CallbackQuery(func=checks, pattern=r"^nick"))
async def nick_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Nick), дата: {data}")
    if event.sender_id != int(data[2]):
        return await event.answer(phrase.not_for_you)
    old_nick = db.nicks(id=event.sender_id).get()
    if old_nick == data[1]:
        return await event.answer(phrase.nick.already_you, alert=True)
    balance = await db.get_money(event.sender_id)
    if balance - config.coofs.PriceForChangeNick < 0:
        return await event.answer(
            phrase.money.not_enough.format(
                formatter.value_to_str(balance, "изумруд"),
            ),
            alert=True,
        )
    try:
        async with mcrcon.Vanilla as rcon:
            await rcon.send(f"nwl remove name {old_nick}")
            await rcon.send(f"nwl add name {data[1]}")
    except Exception:
        logger.error("Внутренняя ошибка при управлении белым списком")
        return await event.answer(phrase.nick.error, alert=True)
    db.add_money(event.sender_id, -config.coofs.PriceForChangeNick)
    db.nicks(data[1], event.sender_id).link()
    user_name = await get_name(data[2])
    return await event.reply(
        phrase.nick.buy_nick.format(
            user=user_name,
            price=formatter.value_to_str(
                config.coofs.PriceForChangeNick,
                "изумруд",
            ),
        ),
    )


@client.on(events.CallbackQuery(func=checks, pattern=r"^word"))
async def word_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Word), дата: {data}")
    user_name = await get_name(data[3])
    if data[1] == "yes":
        with open(pathes.crocoall, encoding="utf-8") as f:
            if data[2] in f.read().split("\n"):
                return await client.edit_message(
                    event.sender_id,
                    event.message_id,
                    phrase.word.exists,
                )
        with open(pathes.crocoall, "a", encoding="utf-8") as f:
            f.write(f"\n{data[2]}")
        db.add_money(data[3], config.coofs.WordRequest)
        await client.send_message(
            config.chats.chat,
            phrase.word.success.format(
                word=data[2],
                user=user_name,
                money=formatter.value_to_str(
                    config.coofs.WordRequest,
                    "изумруд",
                ),
            ),
        )
        return await client.edit_message(
            event.sender_id,
            event.message_id,
            phrase.word.add,
        )
    if data[1] == "no":
        with open(pathes.crocobl, "a", encoding="utf-8") as f:
            f.write(f"\n{data[2]}")
        await client.send_message(
            config.chats.chat,
            phrase.word.no.format(word=data[2], user=user_name),
        )
        return await client.edit_message(
            event.sender_id,
            event.message_id,
            phrase.word.noadd,
        )
    return None


@client.on(events.CallbackQuery(func=checks, pattern=r"^cityadd"))
async def cityadd_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Cityadd), дата: {data}")
    user_name = await get_name(data[3])
    if data[1] == "yes":
        with open(pathes.chk_city, encoding="utf-8") as f:
            if data[2] in f.read().split("\n"):
                return await client.edit_message(
                    event.sender_id,
                    event.message_id,
                    phrase.cities.exists,
                )
        with open(pathes.chk_city, "a", encoding="utf-8") as f:
            f.write(f"\n{data[2]}")
        db.add_money(data[3], config.coofs.WordRequest)
        await client.send_message(
            config.chats.chat,
            phrase.cities.success.format(
                word=data[2].title(),
                user=user_name,
                money=formatter.value_to_str(
                    config.coofs.WordRequest,
                    "изумруд",
                ),
            ),
        )
        return await client.edit_message(
            event.sender_id,
            event.message_id,
            phrase.cities.add,
        )
    if data[1] == "no":
        with open(pathes.bl_city, "a", encoding="utf-8") as f:
            f.write(f"\n{data[2]}")
        await client.send_message(
            config.chats.chat,
            phrase.cities.no.format(word=data[2].title(), user=user_name),
        )
        return await client.edit_message(
            event.sender_id,
            event.message_id,
            phrase.cities.noadd,
        )
    return None


@client.on(events.CallbackQuery(func=checks, pattern=r"^shop"))
async def shop_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Shop), дата: {data}")
    if int(data[-1]) != db.database("shop_version"):
        return await event.answer(phrase.shop.old, alert=True)
    nick = db.nicks(id=event.sender_id).get()
    if nick is None:
        return await event.answer(phrase.nick.not_append, alert=True)
    shop = db.get_shop()
    del shop["theme"]
    balance = await db.get_money(event.sender_id)
    items = list(shop.keys())
    item = shop[items[int(data[1])]]
    if balance < item["price"]:
        return await event.answer(
            phrase.money.not_enough.format(
                formatter.value_to_str(balance, "изумруд"),
            ),
            alert=True,
        )
    try:
        async with mcrcon.Vanilla as rcon:
            command = f"invgive {nick} {item['name']} {item['value']}"
            logger.info(f"Выполняется команда: {command}")
            await rcon.send(command)
    except TimeoutError:
        return await event.answer(phrase.shop.timeout, alert=True)
    db.add_money(event.sender_id, -item["price"])
    return await event.answer(
        phrase.shop.buy.format(items[int(data[1])]),
        alert=True,
    )


@client.on(events.CallbackQuery(func=checks, pattern=r"^crocodile"))
async def crocodile_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Crocodile), дата: {data}")
    if data[1] == "start":
        if db.database("crocodile_super_game") == 1:
            return await event.answer(
                phrase.crocodile.super_game_here,
                alert=True,
            )
        if db.database("current_game") != 0:
            return await event.answer(phrase.crocodile.no, alert=True)
        with open(pathes.crocoall, encoding="utf8") as f:
            word = choice(f.read().split("\n"))
        unsec = ""
        for x in list(word):
            if x.isalpha():
                unsec += "_"
            elif x == " ":
                unsec += x
        db.database("current_game", {"hints": [], "word": word, "unsec": unsec})
        client.add_event_handler(
            crocodile_hint,
            events.NewMessage(pattern=r"(?i)^/подсказка"),
        )
        client.add_event_handler(
            crocodile_handler,
            events.NewMessage(chats=event.chat_id),
        )
        return await event.reply(phrase.crocodile.up)
    if data[1] == "stop":
        entity = await client.get_entity(event.sender_id)
        user = (
            f"@{entity.username}"
            if entity.username
            else entity.first_name + " " + entity.last_name
        )
        if db.database("current_game") == 0:
            return await event.answer(phrase.crocodile.already_down, alert=True)
        if db.database("crocodile_super_game") == 1:
            return await event.answer(
                phrase.crocodile.super_game_here,
                alert=True,
            )
        bets_json = db.database("crocodile_bets")
        if bets_json != {}:
            bets = round(sum(list(bets_json.values())) / 2)
            bets = max(bets, 1)
            sender_balance = await db.get_money(event.sender_id)
            if sender_balance < bets:
                return await event.answer(
                    phrase.crocodile.not_enough.format(
                        formatter.value_to_str(sender_balance, "изумруд"),
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
                    user=user,
                    money=formatter.value_to_str(bets, "изумруд"),
                    word=word,
                ),
            )
        return await event.reply(phrase.crocodile.down.format(word))
    return None


@client.on(events.CallbackQuery(func=checks, pattern=r"^mine"))
async def mine_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    action = data[1]
    user_id = int(data[2])
    sender_id = event.sender_id

    if sender_id != user_id:
        return await event.answer(choice(phrase.mine.not_for_you))

    session = mining.sessions.get(user_id)
    if not session:
        return await event.edit(phrase.mine.closed)

    if action == "no":
        total = session["gems"]
        db.add_money(user_id, total)
        del mining.sessions[user_id]
        return await event.edit(
            phrase.mine.quited.format(formatter.value_to_str(total, "изумруд")),
            buttons=None,
        )

    death_chance = session["death_chance"]
    rand = random()

    if rand < death_chance:
        balance = await db.get_money(user_id)
        penalty = min(session["gems"], balance)
        if penalty > 0:
            db.add_money(user_id, -penalty)
        del mining.sessions[user_id]
        return await event.edit(
            choice(phrase.mine.die).format(
                killer=choice(phrase.mine.killers),
                value=formatter.value_to_str(penalty, "изумруд"),
            ),
            buttons=None,
        )

    if rand < death_chance + config.coofs.Mining.BoostChance:
        extra = randint(
            config.coofs.Mining.BoostGemsMin, config.coofs.Mining.BoostGemsMax
        )
        note = choice(phrase.mine.boost).format(
            formatter.value_to_str(extra, "изумруд")
        )
    else:
        extra = randint(1, config.coofs.Mining.DefaultGems)
        note = phrase.mine.base.format(formatter.value_to_str(extra, "изумруд"))

    session["gems"] += extra
    session["step"] += 1
    session["death_chance"] = min(
        config.coofs.Mining.MaxDeathChance,
        config.coofs.Mining.BaseDeathChance
        + (session["step"] - 1) * config.coofs.Mining.IncDeathChance,
    )

    await event.edit(
        note
        + phrase.mine.sessionall.format(
            formatter.value_to_str(session["gems"], "изумруд")
        )
        + phrase.mine.q,
        buttons=[
            [Button.inline(phrase.mine.button_yes, f"mine.yes.{user_id}")],
            [Button.inline(phrase.mine.button_no, f"mine.no.{user_id}")],
        ],
    )
