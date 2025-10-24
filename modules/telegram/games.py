import asyncio

from random import randint, random

from telethon import events
from telethon.tl.custom import Message
from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback,
)

from .client import client
from .global_checks import checks
from . import func

from .. import phrase, ai, config, formatter, db
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

Cities = db.CitiesGame()
CitiesTimerTask: asyncio.Task = None


@client.on(
    events.NewMessage(config.chats.chat, pattern=r"(?i)^/казино$", func=checks)
)
async def casino(event: Message):
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None)
        != config.chats.topics.games
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
        phrase.casino.start.format(config.coofs.PriceForCasino),
        buttons=keyboard,
    )


@client.on(events.NewMessage(pattern=r"(?i)^/крокодил$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/crocodile$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^старт крокодил$", func=checks))
async def crocodile(event: Message):
    if not event.chat_id == config.chats.chat:
        return await event.reply(phrase.crocodile.chat)
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None)
        != config.chats.topics.games
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
        getattr(event.reply_to, "reply_to_top_id", None)
        != config.chats.topics.games
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
    sender_balance = await db.get_money(event.sender_id)
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
            phrase.roles.no_perms.format(
                level=roles.ADMIN, name=phrase.roles.admin
            )
        )
    arg = event.pattern_match.group(1).strip()
    bets = db.database("crocodile_bets")
    bets[str(config.tokens.bot.creator)] = 50
    db.database("crocodile_bets", bets)
    db.database("crocodile_super_game", 1)
    db.database("max_bet", 100)
    db.database("min_bet", 50)
    await client.send_message(
        config.chats.chat, phrase.crocodile.super_game_wait
    )
    await asyncio.sleep(60)
    db.database(
        "current_game", {"hints": [], "unsec": "_" * len(arg), "word": arg}
    )
    client.add_event_handler(
        crocodile_hint, events.NewMessage(pattern=r"(?i)^/подсказка")
    )
    client.add_event_handler(
        crocodile_handler, events.NewMessage(chats=config.chats.chat)
    )
    return await client.send_message(
        config.chats.chat, phrase.crocodile.super_game
    )


async def crocodile_handler(event: Message):
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None)
        != config.chats.topics.games
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
        return await event.reply(
            phrase.crocodile.win.format(current_word) + bets_str
        )
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
                phrase.crocodile.new.format(
                    "".join(current_mask).replace("_", "..")
                )
            )
        if list(db.database("current_game")["unsec"]) != current_mask:
            cgame = db.database("current_game")
            cgame["unsec"] = "".join(current_mask)
            db.database("current_game", cgame)
            return await event.reply(
                phrase.crocodile.new.format(
                    "".join(current_mask).replace("_", "..")
                )
            )


async def crocodile_hint(event: Message):
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None)
        != config.chats.topics.games
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
    if (random() < config.coofs.PercentForRandomLetter) and (len(hint) > 1):
        n = 1
        for letter in list(game["unsec"]):
            if letter == "_":
                return await event.reply(
                    f"{n} буква в слове - **{game['word'][n - 1]}**"
                )
            n += 1
    return await event.reply((await ai.crocodile.send_message(word)).text)


@logger.catch
async def cities_timeout(current_player: int, last_city: str):
    try:
        player_name = await func.get_name(current_player)
        message: Message = None
        for second in range(config.coofs.CitiesTimeout, 0, -1):
            if not Cities.get_game_status():
                return
            who_answer = Cities.who_answer()
            if who_answer != current_player:
                return
            if Cities.get_last_city() != last_city:
                return
            if second <= 1:
                await message.delete()
                Cities.logger("Игрока выбросило за тайм-аут!")
                players_list = Cities.get_players()
                count = Cities.get_count_players()
                rem_data = Cities.rem_player(current_player)
                Cities.logger(f"Удаляем игрока {current_player}...")
                if rem_data is False:
                    Cities.logger("Игра завершена")
                    win_money = count * config.coofs.CitiesBet
                    db.add_money(players_list[0], win_money)
                    Cities.logger(
                        f"Победитель {players_list[0]} получает {win_money}"
                    )
                    statistic = ""
                    n = 1
                    for key, value in Cities.get_all_stat().items():
                        statistic += f"{n if n != 1 else '👑 1'}. **{await func.get_name(key)}** назвал {value} городов\n"
                        n += 1
                    statistic = "Пусто!" if statistic == "" else statistic
                    await client.send_message(
                        config.chats.chat,
                        phrase.cities.winner.format(
                            await func.get_name(
                                players_list[0],
                            ),
                            formatter.value_to_str(
                                win_money - config.coofs.CitiesBet, "изумруд"
                            ),
                            statistic,
                        ),
                        reply_to=config.chats.topics.games,
                    )
                    return Cities.end_game()
                global CitiesTimerTask
                CitiesTimerTask = asyncio.create_task(
                    cities_timeout(rem_data, last_city)
                )
                return await client.send_message(
                    config.chats.chat,
                    phrase.cities.timeout_done.format(
                        player_name,
                        await func.get_name(rem_data),
                        last_city.title(),
                    ),
                    reply_to=config.chats.topics.games,
                )
            if second % 5 == 0 and config.coofs.CitiesTimeout / 2 >= second:
                if message:
                    await message.edit(
                        phrase.cities.timeout.format(
                            player=player_name, time=second
                        )
                    )
                else:
                    message: Message = await client.send_message(
                        config.chats.chat,
                        phrase.cities.timeout.format(
                            player=player_name, time=second
                        ),
                        reply_to=config.chats.topics.games,
                    )
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        try:
            logger.info("Принудительно завершаем тайм-аут")
            await message.delete()
        except Exception:
            pass


@client.on(events.NewMessage(chats=config.chats.chat))
async def cities_answer(event: Message):
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None)
        != config.chats.topics.games
    ):
        return
    if event.text.startswith("/"):
        return
    # Активна ли игра
    if not Cities.get_game_status():
        return
    # Участвует ли пользователь в игре
    if event.sender_id not in Cities.get_players():
        return
    city = event.text.strip()
    result_code = Cities.answer(event.sender_id, city)

    async def autodelete(text):
        message: Message = await event.reply(text)
        await asyncio.sleep(config.coofs.CitiesAutodelete)
        await message.delete()

    if result_code == 0:  # Успех
        global CitiesTimerTask
        if CitiesTimerTask:
            CitiesTimerTask.cancel()
        current_player = Cities.who_answer()
        current_name = await func.get_name(current_player)
        last_city = Cities.get_last_city()
        await event.reply(
            phrase.cities.city_accepted.format(last_city.title(), current_name)
        )
        CitiesTimerTask = asyncio.create_task(
            cities_timeout(current_player, last_city)
        )
    elif result_code == 1:
        await autodelete(phrase.cities.unknown_city)
    elif result_code == 2:
        await autodelete(phrase.cities.not_your_turn)
    elif result_code == 4:
        last_city = Cities.get_last_city()
        required_letter = formatter.city_last_letter(last_city).upper()
        await autodelete(phrase.cities.wrong_letter.format(required_letter))
    elif result_code == 5:
        await autodelete(phrase.cities.already_inlist)


@client.on(events.CallbackQuery(pattern=r"^cities\."))
async def cities_callback(event: events.CallbackQuery.Event):
    """Обработчик кнопок игры"""
    data = event.data.decode("utf-8").split(".")
    action = data[1]

    if action == "join":
        if event.sender_id in Cities.get_players():
            return await event.answer(phrase.cities.already_ingame, alert=True)

        balance = await db.get_money(event.sender_id)
        if config.coofs.PriceForCities > balance:
            return await event.answer(
                phrase.money.not_enough.format(
                    formatter.value_to_str(balance, "изумруд")
                )
            )
        db.add_money(event.sender_id, -config.coofs.PriceForCities)
        await event.answer(
            phrase.cities.set_ingame.format(
                formatter.value_to_str(config.coofs.PriceForCities, "изумруд")
            )
        )

        Cities.add_player(event.sender_id)

        # Обновляем список игроков
        players_names = []
        for player_id in Cities.get_players():
            name = await func.get_name(player_id)
            players_names.append(name)

        keyboard = [
            [
                KeyboardButtonCallback(
                    text="➕ Присоединиться", data="cities.join"
                )
            ],
            [
                KeyboardButtonCallback(
                    text="🎮 Начать игру", data="cities.start"
                )
            ],
            [KeyboardButtonCallback(text="❌ Отменить", data="cities.cancel")],
        ]

        await event.edit(
            phrase.cities.start.format(", ".join(players_names)),
            buttons=keyboard,
        )
        return await event.answer(phrase.cities.set_ingame)

    elif action == "start":
        if len(Cities.get_players()) < 2:
            return await event.answer(phrase.cities.low_players, alert=True)
        data = Cities.start_game()
        current_player = Cities.who_answer()
        global CitiesTimerTask
        CitiesTimerTask = asyncio.create_task(
            cities_timeout(current_player, Cities.get_last_city())
        )
        return await event.edit(
            phrase.cities.game_started.format(
                Cities.get_last_city().title(),
                await func.get_name(current_player),
            )
        )

    elif action == "cancel":
        if event.sender_id not in Cities.get_players():
            return await event.answer(phrase.cities.not_in_players, alert=True)
        Cities.end_game()
        return await event.edit("❌ Игра отменена.")


@client.on(events.NewMessage(pattern=r"(?i)^/города$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/города старт$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/cities start$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/миниигра города$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/minigame cities$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/cities$"))
async def cities_start(event: Message):
    """Команда запуска игры"""
    if not event.chat_id == config.chats.chat:
        return await event.reply(phrase.cities.chat)
    if (event.reply_to_msg_id != config.chats.topics.games) and (
        getattr(event.reply_to, "reply_to_top_id", None)
        != config.chats.topics.games
    ):
        return await event.reply(phrase.game_topic_warning)
    if len(Cities.get_players()) > 0 or Cities.get_game_status():
        keyboard = [
            [KeyboardButtonCallback(text="❌ Отменить", data="cities.cancel")]
        ]
        return await event.reply(
            phrase.cities.already_started, buttons=keyboard
        )

    # Очищаем предыдущую игру
    Cities.end_game()
    Cities.add_player(event.sender_id)

    keyboard = [
        [KeyboardButtonCallback(text="➕ Присоединиться", data="cities.join")],
        [KeyboardButtonCallback(text="🎮 Начать игру", data="cities.start")],
        [KeyboardButtonCallback(text="❌ Отменить", data="cities.cancel")],
    ]

    user_name = await func.get_name(event.sender_id)
    message: Message = await event.reply(
        phrase.cities.start.format(user_name), buttons=keyboard
    )
    id = Cities.get_id()
    await asyncio.sleep(300)
    if Cities.get_game_status() is False and Cities.get_id() == id:
        await message.edit(phrase.cities.wait_exceeded, buttons=None)
        Cities.end_game()


if db.database("current_game") != 0:
    client.add_event_handler(
        crocodile_handler, events.NewMessage(chats=config.chats.chat)
    )
    client.add_event_handler(
        crocodile_hint,
        events.NewMessage(pattern=r"(?i)^/подсказка$", func=checks),
    )
