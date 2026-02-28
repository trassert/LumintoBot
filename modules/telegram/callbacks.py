import asyncio
from random import choice, randint, random

import aiofiles
from loguru import logger
from telethon import Button, events, types

from .. import (
    config,
    db,
    dice,
    floodwait,
    formatter,
    log,
    mcrcon,
    mining,
    pathes,
    phrase,
)
from . import func
from .client import client
from .games import CrocodileGame, crocodile_handler, crocodile_hint

logger.info(f"Загружен модуль {__name__}!")


async def _check_and_deduct_balance(
    user_id: int,
    price: int,
    currency: str = phrase.currency,
) -> bool | str:
    """Проверяет баланс и списывает сумму при успехе.
    Возвращает True или сообщение об ошибке."""
    balance = await db.get_money(user_id)
    if balance < price:
        return phrase.money.not_enough.format(formatter.value_to_str(balance, currency))
    await db.add_money(user_id, -price)
    return True


def _ensure_owner(sender_id: int, expected_id: int | str) -> bool:
    """Проверяет, является ли отправитель владельцем действия."""
    return sender_id == int(expected_id)


async def _handle_suggestion(
    event: events.CallbackQuery.Event,
    word: str,
    accept_file: str,
    reject_file: str,
    exists_phrase: str,
    success_phrase: str,
    reject_phrase: str,
    add_phrase: str,
    reject_add_phrase: str,
):
    """Унифицированная обработка предложений (слова/города)."""
    data = event.data.decode("utf-8").split(".")
    user_name = await func.get_name(data[3])
    sender_id = event.sender_id

    match data[1]:
        case "yes":
            async with aiofiles.open(accept_file) as aiof:
                if word in (await aiof.read()).split("\n"):
                    return await client.edit_message(
                        sender_id,
                        event.message_id,
                        exists_phrase,
                    )

            async with aiofiles.open(accept_file, "a") as aiof:
                await aiof.write(f"\n{word}")

            await db.add_money(sender_id, config.cfg.WordRequest)
            await client.send_message(
                config.chats.chat,
                success_phrase.format(
                    word=word,
                    user=user_name,
                    money=formatter.value_to_str(
                        config.cfg.WordRequest,
                        phrase.currency,
                    ),
                ),
            )
            return await client.edit_message(sender_id, event.message_id, add_phrase)

        case "no":
            async with aiofiles.open(reject_file, "a") as aiof:
                await aiof.write(f"\n{word}")
            await client.send_message(
                config.chats.chat,
                reject_phrase.format(word=word, user=user_name),
            )
            return await client.edit_message(
                sender_id,
                event.message_id,
                reject_add_phrase,
            )


@client.on(events.CallbackQuery(func=func.checks, pattern=r"^state"))
async def state_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (States), дата: {data}")
    sender_id = event.sender_id

    match data[1]:
        case "pay":
            nick = db.nicks(id=sender_id).get()
            if nick is None:
                return await event.answer(phrase.state.not_connected, alert=True)
            if db.States.if_player(sender_id) is not False:
                return await event.answer(phrase.state.already_player, alert=True)
            if db.States.if_author(sender_id) is not False:
                return await event.answer(phrase.state.already_author, alert=True)

            state = db.State(data[2])
            balance_check = await _check_and_deduct_balance(sender_id, state.price)
            if balance_check is not True:
                return await event.answer(balance_check, alert=True)

            state.change("money", state.money + state.price)
            players = [*state.players, sender_id]
            state.change("players", players)

            await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.new_player.format(state=state.name, player=nick),
                reply_to=config.chats.topics.rp,
            )

            if state.type == 0 and len(players) >= config.cfg.Type1Players:
                await client.send_message(
                    entity=config.chats.chat,
                    message=phrase.state.up.format(name=state.name, type="Государство"),
                    reply_to=config.chats.topics.rp,
                )
                state.change("type", 1)

            elif state.type == 1 and len(players) >= config.cfg.Type2Players:
                await client.send_message(
                    entity=config.chats.chat,
                    message=phrase.state.up.format(name=state.name, type="Империя"),
                    reply_to=config.chats.topics.rp,
                )
                state.change("type", 2)

            return await event.answer(phrase.state.admit.format(state.name), alert=True)

        case "remove":
            try:
                state = db.State(data[2])
            except FileNotFoundError:
                return await event.answer(phrase.state.already_deleted, alert=True)

            if not _ensure_owner(sender_id, state.author):
                return await event.answer(phrase.not_for_you, alert=True)

            await db.add_money(state.author, state.money)
            if not db.States.remove(data[2]):
                return await event.answer(phrase.error, alert=True)

            await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.rem_public.format(name=data[2]),
                reply_to=config.chats.topics.rp,
            )
            return await event.reply(
                phrase.state.removed.format(author=await func.get_name(state.author)),
            )

        case "m":
            if not _ensure_owner(sender_id, data[2]):
                return await event.answer(phrase.not_for_you, alert=True)

            state_name = data[3].capitalize()
            balance_check = await _check_and_deduct_balance(
                sender_id,
                config.cfg.PriceForNewState,
            )
            if balance_check is not True:
                return await event.answer(balance_check, alert=True)

            if db.States.check(state_name):
                return await event.answer(phrase.state.already_here, alert=True)

            db.States.add(state_name, sender_id)
            await event.reply(
                phrase.state.make_by_callback.format(
                    author=await func.get_name(sender_id),
                    state_name=state_name,
                ),
            )
            return await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.make.format(state_name),
                reply_to=config.chats.topics.rp,
            )

        case "rn":
            if not _ensure_owner(sender_id, data[3]):
                return await event.answer(phrase.not_for_you)

            new_name = data[2].capitalize()
            if db.States.check(new_name):
                return await event.answer(phrase.state.already_here, alert=True)

            state_name = db.States.if_author(sender_id)
            if state_name is False:
                return await event.answer(phrase.state.not_a_author, alert=True)

            balance_check = await _check_and_deduct_balance(
                sender_id,
                config.cfg.PriceForChangeStateNick,
            )
            if balance_check is not True:
                return await event.answer(balance_check, alert=True)

            if db.State(state_name).rename(new_name) is False:
                return await event.answer(phrase.state.already_here, alert=True)

            await event.reply(
                phrase.state.renamed.format(old=state_name.capitalize(), new=new_name),
            )
            return await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.renamed.format(
                    old=state_name.capitalize(),
                    new=new_name,
                ),
                reply_to=config.chats.topics.rp,
            )


@client.on(events.CallbackQuery(func=func.checks, pattern=r"^casino"))
async def casino_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    request = floodwait.WaitCasino.request()
    if request is False:
        return await event.answer(phrase.casino.full_floodwait.format(request))
    await asyncio.sleep(request)

    logger.info(f"КБ кнопка (Casino), дата: {data}")
    sender_id = event.sender_id

    if data[1] != "auto":
        return None

    balance_check = await _check_and_deduct_balance(
        sender_id,
        config.cfg.PriceForCasino,
    )
    if balance_check is not True:
        return await event.answer(balance_check, alert=True)

    media_dice = await client.send_file(
        event.chat_id,
        types.InputMediaDice("🎰"),
        reply_to=config.chats.topics.games,
    )
    fm = await event.reply(phrase.casino.wait)
    pos = dice.get(media_dice.media.value)

    if pos[0] == pos[1] == pos[2]:
        await db.Users.add_win(sender_id)
        logger.info(f"{sender_id} - победил в казино")
        win_amount = config.cfg.PriceForCasino * config.cfg.CasinoWinRatio
        await db.add_money(sender_id, win_amount)
        await asyncio.sleep(2)
        return await fm.edit(
            phrase.casino.win_auto.format(
                value=win_amount,
                name=await func.get_name(sender_id),
            ),
        )

    if pos[0] == pos[1] or pos[1] == pos[2]:
        await db.add_money(sender_id, config.cfg.PriceForCasino)
        await asyncio.sleep(2)
        return await fm.edit(
            phrase.casino.partially_auto.format(await func.get_name(sender_id)),
        )

    await db.Users.add_lose_money(sender_id, config.cfg.PriceForCasino)
    logger.info(f"{sender_id} проиграл в казино")
    await asyncio.sleep(2)
    return await fm.edit(
        phrase.casino.lose_auto.format(
            name=await func.get_name(sender_id),
            value=config.cfg.PriceForCasino,
        ),
    )


@client.on(events.CallbackQuery(func=func.checks, pattern=r"^nick"))
async def nick_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Nick), дата: {data}")
    sender_id = event.sender_id

    if not _ensure_owner(sender_id, data[2]):
        return await event.answer(phrase.not_for_you)

    old_nick = db.nicks(id=sender_id).get()
    if old_nick == data[1]:
        return await event.answer(phrase.nick.already_you, alert=True)

    balance_check = await _check_and_deduct_balance(
        sender_id,
        config.cfg.PriceForChangeNick,
    )
    if balance_check is not True:
        return await event.answer(balance_check, alert=True)

    try:
        async with mcrcon.Vanilla as rcon:
            await rcon.send(f"nwl remove name {old_nick}")
            await rcon.send(f"nwl add name {data[1]}")
    except Exception:
        logger.error("Внутренняя ошибка при управлении белым списком")
        return await event.answer(phrase.nick.error, alert=True)

    db.nicks(data[1], sender_id).link()
    user_name = await func.get_name(sender_id)
    return await event.reply(
        phrase.nick.buy_nick.format(
            user=user_name,
            price=formatter.value_to_str(
                config.cfg.PriceForChangeNick,
                phrase.currency,
            ),
        ),
    )


@client.on(events.CallbackQuery(func=func.checks, pattern=r"^cityadd"))
async def cityadd_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Cityadd), дата: {data}")
    return await _handle_suggestion(
        event,
        word=data[2],
        accept_file=pathes.chk_city,
        reject_file=pathes.bl_city,
        exists_phrase=phrase.cities.exists,
        success_phrase=phrase.cities.success,
        reject_phrase=phrase.cities.no,
        add_phrase=phrase.cities.add,
        reject_add_phrase=phrase.cities.noadd,
    )


@client.on(events.CallbackQuery(func=func.checks, pattern=r"^shop"))
async def shop_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Shop), дата: {data}")
    sender_id = event.sender_id

    if int(data[-1]) != await db.shop_version():
        return await event.answer(phrase.shop.old, alert=True)

    nick = db.nicks(id=sender_id).get()
    if nick is None:
        return await event.answer(phrase.nick.not_append, alert=True)

    shop = await db.get_shop()
    del shop["theme"]
    items = list(shop.keys())
    item = shop[items[int(data[1])]]

    balance_check = await _check_and_deduct_balance(sender_id, item["price"])
    if balance_check is not True:
        return await event.answer(balance_check, alert=True)

    try:
        async with mcrcon.Vanilla as rcon:
            await log.buy(nick, item["name"], item["value"])
            command = f"invgive {nick} {item['name']} {item['value']}"
            await rcon.send(command)
    except TimeoutError:
        return await event.answer(phrase.shop.timeout, alert=True)

    return await event.answer(phrase.shop.buy.format(items[int(data[1])]), alert=True)


@client.on(events.CallbackQuery(func=func.checks, pattern=r"^crocodile"))
async def crocodile_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Crocodile), дата: {data}")
    sender_id = event.sender_id

    match data[1]:
        case "start":
            if await CrocodileGame.is_running():
                return await event.answer(phrase.crocodile.no, alert=True)

            word = await db.get_crocodile_word()
            await CrocodileGame.start_game(word)

            client.add_event_handler(
                crocodile_hint,
                events.NewMessage(pattern=r"(?i)^/подсказка"),
            )
            client.add_event_handler(
                crocodile_handler,
                events.NewMessage(chats=event.chat_id),
            )
            return await event.reply(phrase.crocodile.up)

        case "stop":
            entity = await client.get_entity(sender_id)
            user = (
                f"@{entity.username}"
                if entity.username
                else f"{entity.first_name} {entity.last_name}".strip()
            )

            if not await CrocodileGame.is_running():
                return await event.answer(phrase.crocodile.already_down, alert=True)

            bets_json = CrocodileGame.get_bets()
            bets = 0
            if bets_json:
                bets = max(round(sum(bets_json.values()) / 2), 1)
                balance_check = await _check_and_deduct_balance(sender_id, bets)
                if balance_check is not True:
                    return await event.answer(balance_check, alert=True)

            game = CrocodileGame.get_current()
            word = game.get("word") if isinstance(game, dict) else None
            await CrocodileGame.stop_game()
            await CrocodileGame.set_last_hint(0)

            client.remove_event_handler(crocodile_hint)
            client.remove_event_handler(crocodile_handler)

            if bets_json:
                return await event.reply(
                    phrase.crocodile.down_payed.format(
                        user=user,
                        money=formatter.value_to_str(bets, phrase.currency),
                        word=word,
                    ),
                )
            return await event.reply(phrase.crocodile.down.format(word))


@client.on(events.CallbackQuery(func=func.checks, pattern=r"^mine"))
async def mine_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Mine), дата: {data}")
    sender_id = event.sender_id

    if not _ensure_owner(sender_id, data[2]):
        return await event.answer(choice(phrase.mine.not_for_you))

    session = mining.sessions.get(sender_id)
    if not session:
        try:
            return await event.edit(phrase.mine.closed)
        except Exception:
            return None

    match data[1]:
        case "no":
            try:
                del mining.sessions[sender_id]
            except Exception:
                logger.info("Триггернуто удаление сессии, но её и так нет. Пропускаю..")
                return None
            total = session["gems"]
            await db.add_money(sender_id, total)
            await db.add_mine_top(sender_id, total)
            return await event.edit(
                phrase.mine.quited.format(
                    formatter.value_to_str(total, phrase.currency),
                ),
                buttons=None,
            )

        case "yes":
            death_chance = session["death_chance"]
            rand = random()

            if rand < death_chance:
                balance = await db.get_money(sender_id)
                penalty = min(session["gems"], balance)
                post = ""
                if penalty > 0:
                    await db.add_money(sender_id, -penalty)
                    post = phrase.mine.post_die.format(
                        formatter.value_to_str(penalty, phrase.currency),
                    )
                del mining.sessions[sender_id]
                return await event.edit(
                    f"{
                        choice(phrase.mine.die).format(
                            killer=choice(phrase.mine.killers),
                        )
                    }{post}",
                    buttons=None,
                )

            if rand < death_chance + config.cfg.Mining.BoostChance:
                extra = randint(
                    config.cfg.Mining.BoostGemsMin,
                    config.cfg.Mining.BoostGemsMax,
                )
                note = choice(phrase.mine.boost).format(
                    formatter.value_to_str(extra, phrase.currency),
                )
            else:
                extra = randint(1, config.cfg.Mining.DefaultGems)
                note = phrase.mine.base.format(
                    formatter.value_to_str(extra, phrase.currency),
                )

            session["gems"] += extra
            session["step"] += 1
            session["death_chance"] = min(
                config.cfg.Mining.MaxDeathChance,
                config.cfg.Mining.BaseDeathChance
                + (session["step"] - 1) * config.cfg.Mining.IncDeathChance,
            )

            await event.edit(
                note
                + phrase.mine.sessionall.format(
                    formatter.value_to_str(session["gems"], phrase.currency),
                )
                + phrase.mine.q,
                buttons=[
                    [Button.inline(phrase.mine.button_yes, f"mine.yes.{sender_id}")],
                    [Button.inline(phrase.mine.button_no, f"mine.no.{sender_id}")],
                ],
            )
    return None


@client.on(events.CallbackQuery(func=func.checks, pattern=r"^hint"))
async def hint_callback(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    logger.info(f"КБ кнопка (Mine), дата: {data}")
    roles = db.Roles()
    if await roles.get(event.sender_id) < roles.ADMIN:
        return None
    hint_data = await db.get_hint_byid(data[2])
    if hint_data is None:
        await event.answer(phrase.newhints.not_found)
        return await event.delete()
    match data[1]:
        case "accept":
            remove_data = await db.remove_pending_hint(data[2])
            if remove_data is None:
                await event.answer(phrase.newhints.not_found)
                return await event.delete()
            await db.append_hint(word=hint_data["word"], hint=hint_data["hint"])
            await db.add_money(hint_data["user"], config.cfg.HintGift)
            await client.send_message(
                int(hint_data["user"]),
                phrase.newhints.accept.format(
                    word=hint_data["word"],
                    get=formatter.value_to_str(config.cfg.HintGift, phrase.currency),
                ),
            )
            return await event.edit(
                phrase.newhints.accept_edit.format(
                    word=hint_data["word"],
                    hint=hint_data["hint"],
                ),
                buttons=None,
            )
        case "reject":
            remove_data = await db.remove_pending_hint(data[2])
            if remove_data is None:
                await event.answer(phrase.newhints.not_found)
                return await event.delete()
            await client.send_message(
                int(hint_data["user"]),
                phrase.newhints.reject.format(word=hint_data["word"]),
            )
            return await event.edit(
                phrase.newhints.reject_edit.format(
                    word=hint_data["word"],
                    hint=hint_data["hint"],
                ),
                buttons=None,
            )


@client.on(events.CallbackQuery(func=func.checks, pattern=r"^test"))
async def simple_antibot(event: events.CallbackQuery.Event):
    data = event.data.decode("utf-8").split(".")
    if str(event.sender_id) != data[1]:
        return await event.answer(phrase.not_for_you, alert=True)
    await client.edit_permissions(
        config.chats.chat,
        event.sender_id,
        send_messages=True,
    )
    await event.answer(phrase.chataction.test_passed)
    await event.delete()
    if not db.hellomsg_check(event.sender_id):
        return logger.info(f"{event.sender_id} вступил, но приветствие уже было.")

    return await client.send_message(
        config.chats.chat,
        phrase.chataction.hello.format(await func.get_name(event.sender_id)),
        link_preview=False,
    )
