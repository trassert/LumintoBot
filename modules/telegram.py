import asyncio
import re

from os import path
from xml.dom.expatbuilder import parseString
from loguru import logger
from random import choice, random, randint
from datetime import datetime

from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback,
)
from telethon import events
from telethon.sync import TelegramClient
from telethon import errors as TGErrors
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.custom import Message

from . import config
from . import db
from . import phrase
from . import dice
from . import ip
from . import vk
from . import chart
from . import crosssocial
from . import ai

from .system_info import get_system_info
from .mcrcon import MinecraftClient
from .formatter import decline_number, remove_section_marks


client = TelegramClient(
    session=path.join("db", "bot"),
    api_id=config.tokens.bot.id,
    api_hash=config.tokens.bot.hash,
    device_model="Bot",
    system_version="4.16.30-vxCUSTOM",
    use_ipv6=True,
)


crocodile_path = path.join("db", "crocodile", "all.txt")
crocodile_blacklist_path = path.join("db", "crocodile", "blacklist.txt")


"Вспомогательные функции"


async def get_name(id, push=True, minecraft=False):
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


"Глобал"


async def checks(event):
    roles = db.roles()
    if roles.get(event.sender_id) == roles.BLACKLIST:
        if isinstance(event, events.CallbackQuery.Event):
            await event.answer(phrase.blacklisted, alert=True)
        await event.reply(phrase.blacklisted)
        return False
    return True


"Кнопки бота"


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
            with open(crocodile_path, "r", encoding="utf8") as f:
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
                            decline_number(sender_balance, "изумруд")
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
                        user=user, money=decline_number(bets, "изумруд"), word=word
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
                phrase.money.not_enough.format(decline_number(balance, "изумруд")),
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
            with open(crocodile_path, "a", encoding="utf-8") as f:
                f.write(f"\n{data[2]}")
            db.add_money(data[3], config.coofs.WordRequest)
            await client.send_message(
                config.chats.chat,
                phrase.word.success.format(
                    word=data[2],
                    user=user_name,
                    money=decline_number(config.coofs.WordRequest, "изумруд"),
                ),
            )
            return await client.edit_message(
                event.sender_id, event.message_id, phrase.word.add
            )
        if data[1] == "no":
            with open(crocodile_blacklist_path, "a", encoding="utf-8") as f:
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
                phrase.money.not_enough.format(decline_number(balance, "изумруд"))
            )
        db.add_money(event.sender_id, -config.coofs.PriceForChangeNick)
        db.nicks(data[1], event.sender_id).link()
        user_name = await get_name(data[2])
        return await event.reply(
            phrase.nick.buy_nick.format(
                user=user_name,
                price=decline_number(config.coofs.PriceForChangeNick, "изумруд"),
            )
        )
    elif data[0] == "casino":
        if data[1] == "start":
            balance = db.get_money(event.sender_id)
            if balance < config.coofs.PriceForCasino:
                return await event.answer(
                    phrase.money.not_enough.format(decline_number(balance, "изумруд")),
                    alert=True,
                )
            db.add_money(event.sender_id, -config.coofs.PriceForCasino)
            await event.answer(phrase.casino.do)
            response = []

            async def check(message):
                if event.sender_id != message.sender_id:
                    return
                if getattr(message, "media", None) is None:
                    return
                if getattr(message.media, "emoticon", None) is None:
                    return
                if message.media.emoticon != "🎰":
                    return
                pos = dice.get(message.media.value)
                if (pos[0] == pos[1]) and (pos[1] == pos[2]):
                    logger.info(f"{message.sender_id} - победил в казино")
                    db.add_money(
                        message.sender_id,
                        config.coofs.PriceForCasino * config.coofs.CasinoWinRatio,
                    )
                    await asyncio.sleep(2)
                    await message.reply(
                        phrase.casino.win.format(
                            config.coofs.PriceForCasino * config.coofs.CasinoWinRatio
                        )
                    )
                elif (pos[0] == pos[1]) or (pos[1] == pos[2]):
                    db.add_money(message.sender_id, config.coofs.PriceForCasino)
                    await asyncio.sleep(2)
                    await message.reply(phrase.casino.partially)
                else:
                    logger.info(f"{message.sender_id} проиграл в казино")
                    await asyncio.sleep(2)
                    await message.reply(phrase.casino.lose)
                client.remove_event_handler(check)
                logger.info("Снят обработчик казино")
                response.append(1)

            client.add_event_handler(check, events.NewMessage(config.chats.chat))
            await asyncio.sleep(config.coofs.CasinoSleepTime)
            if 1 not in response:
                return await event.answer(
                    phrase.casino.timeout.format(await get_name(event.sender_id))
                )
    elif data[0] == "state":
        if data[1] == "pay":
            nick = db.nicks(id=event.sender_id).get()
            if nick is None:
                return await event.answer(phrase.state.not_connected, alert=True)
            balance = db.get_money(event.sender_id)
            state = db.state(data[2])
            if state.price > balance:
                return await event.answer(
                    phrase.money.not_enough.format(decline_number(balance, "изумруд")),
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
            state = db.state(data[2])
            db.add_money(state.author, state.money)
            if db.states.remove(data[2]) != True:
                return await event.answer(phrase.error, alert=True)
            await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.rem_public.format(name=data[2]),
                reply_to=config.chats.topics.rp
            )
            return await event.reply(
                phrase.state.removed.format(author=await get_name(state.author, push=False))
            )
    else:
        pass


"Обработчики событий"


@client.on(events.ChatAction(chats=config.chats.chat))
async def chat_action(event: events.ChatAction.Event):
    user_name = await get_name(event.user_id, push=False)
    if event.user_left:
        return await client.send_message(
            config.chats.chat,
            phrase.chataction.leave.format(user_name)
        )
    elif event.user_joined:
        return await client.send_message(
            config.chats.chat,
            phrase.chataction.hello.format(user_name)
        )


"Обработчик вк-топика"


@client.on(events.NewMessage(config.chats.chat))
async def vk_chat(event):

    async def send():
        if event.text == "":
            return logger.info("Пустое сообщение")
        user_name = await client.get_entity(event.sender_id)
        if user_name.last_name is None:
            user_name = user_name.first_name
        else:
            user_name = user_name.first_name + " " + user_name.last_name
        logger.info(f"ТГ>ВК: {user_name} > {event.text}")
        await vk.client.api.messages.send(
            chat_id=config.tokens.vk.chat_id,
            message=f"{user_name}: {event.text}",
            random_id=0,
        )

    if event.reply_to_msg_id == config.chats.topics.vk:
        return await send()
    if event.reply_to is not None:
        if event.reply_to.reply_to_top_id == config.chats.topics.vk:
            return await send()


"Обработчики команд"


@client.on(events.NewMessage(config.chats.chat, pattern=r"(?i)^/казино$", func=checks))
async def casino(event: Message):
    keyboard = ReplyInlineMarkup(
        [
            KeyboardButtonRow(
                [
                    KeyboardButtonCallback(
                        text="💎 Внести изумруды", data=b"casino.start"
                    )
                ]
            )
        ]
    )
    return await event.reply(
        phrase.casino.start.format(config.coofs.PriceForCasino), buttons=keyboard
    )


@client.on(events.NewMessage(pattern=r"(?i)^\+чек(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+ticket(.*)", func=checks))
async def do_ticket(event: Message):
    if not event.is_private:
        return await event.reply(phrase.ticket.in_chat)
    arg = event.pattern_match.group(1).strip()
    if arg == "":
        return await event.reply(phrase.ticket.no_value)
    try:
        arg = int(arg)
    except ValueError:
        return await event.reply(phrase.ticket.not_int)
    if arg < 1:
        return await event.reply(phrase.ticket.bigger_than_zero)
    balance = db.get_money(event.sender_id)
    if balance < arg:
        return await event.reply(
            phrase.money.not_enough.format(decline_number(balance, "изумруд"))
        )
    db.add_money(event.sender_id, -arg)
    ticket_id = db.ticket.add(event.sender_id, arg)
    return await event.reply(
        phrase.ticket.added.format(
            value=arg, author=await get_name(event.sender_id), id=ticket_id
        )
    )


@client.on(events.NewMessage(pattern=r"(?i)^/чек(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ticket(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/активировать(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^активировать(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/activate(.*)", func=checks))
async def get_ticket(event: Message):
    arg = event.pattern_match.group(1).strip()
    if arg == "":
        return await event.reply(phrase.ticket.no_value)
    ticket_info = db.ticket.get(arg)
    if ticket_info is None:
        return await event.reply(phrase.ticket.no_such)
    db.add_money(event.sender_id, ticket_info["value"])
    db.ticket.delete(arg)
    return await event.reply(
        phrase.ticket.got.format(
            author=await get_name(ticket_info["author"]),
            value=decline_number(ticket_info["value"], "изумруд"),
        )
    )


@client.on(events.NewMessage(pattern=r"(?i)^/топ соо(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ сообщений(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ в чате(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/актив сервера(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мчат(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мстат(.*)", func=checks))
async def active_check(event: Message):
    arg = event.pattern_match.group(1).strip()
    if arg in phrase.all_arg:
        text = phrase.stat.chat.format("всё время")
        all_data = db.statistic().get_all(all_days=True)
        chart.create_plot(db.statistic().get_raw())
        n = 1
        for data in all_data:
            if n > config.coofs.MaxStatPlayers:
                break
            text += f"{n}. {data[0]} - {data[1]}\n"
            n += 1
        return await client.send_file(event.chat_id, chart.chart_path, caption=text)
    try:
        days = int(arg)
        text = phrase.stat.chat.format(decline_number(days, "день"))
        all_data = db.statistic(days=days).get_all()
        if days >= 7:
            chart.create_plot(db.statistic(days=days).get_raw())
            n = 1
            for data in all_data:
                if n > config.coofs.MaxStatPlayers:
                    break
                text += f"{n}. {data[0]} - {data[1]}\n"
                n += 1
            return await client.send_file(event.chat_id, chart.chart_path, caption=text)
    except ValueError:
        text = phrase.stat.chat.format("день")
        all_data = db.statistic().get_all()
    if all_data == []:
        return await event.reply(phrase.stat.empty)
    n = 1
    for data in all_data:
        if n > config.coofs.MaxStatPlayers:
            break
        text += f"{n}. {data[0]} - {data[1]}\n"
        n += 1
    return await event.reply(text)


@client.on(events.NewMessage(pattern=r"(?i)^/linknick(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/привязать(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^привязать(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/новый ник(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/линкник(.*)", func=checks))
async def link_nick(event: Message):
    nick = event.pattern_match.group(1).strip()
    if len(nick) < 4:
        return await event.reply(phrase.nick.too_short)
    if len(nick) > 16:
        return await event.reply(phrase.nick.too_big)
    if not re.match("^[A-Za-z0-9_]*$", nick):
        return await event.reply(phrase.nick.invalid)

    if db.nicks(nick=nick).get() is not None:
        if db.nicks(id=event.sender_id).get() == nick:
            return await event.reply(phrase.nick.already_you)
        return await event.reply(phrase.nick.taken)
    elif db.nicks(id=event.sender_id).get() is not None:
        if db.nicks(id=event.sender_id).get() == nick:
            return await event.reply(phrase.nick.already_you)
        keyboard = ReplyInlineMarkup(
            [
                KeyboardButtonRow(
                    [
                        KeyboardButtonCallback(
                            text="✅ Сменить",
                            data=f"nick.{nick}.{event.sender_id}".encode(),
                        )
                    ]
                )
            ]
        )
        return await event.reply(
            phrase.nick.already_have.format(
                price=decline_number(config.coofs.PriceForChangeNick, "изумруд")
            ),
            buttons=keyboard,
        )

    db.add_money(event.sender_id, config.coofs.LinkGift)
    db.nicks(nick, event.sender_id).link()
    return await event.reply(
        phrase.nick.success.format(decline_number(config.coofs.LinkGift, "изумруд"))
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


@client.on(events.NewMessage(pattern=r"(?i)^/хост$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/host$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/айпи$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ip", func=checks))
async def host(event: Message):
    return await event.reply(
        phrase.server.host.format(
            v4=db.database("host"),
            v6=f'{db.database("ipv6_subdomain")}.{db.database("host")}'
        )
    )


@client.on(events.NewMessage(pattern=r"(?i)^/серв$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/сервер", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/server", func=checks))
async def sysinfo(event: Message):
    await event.reply(get_system_info())


@client.on(events.NewMessage(pattern=r"(?i)^/помощь$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/help", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/команды$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/commands$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^команды$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^бот помощь$", func=checks))
async def help(event: Message):
    return await event.reply(phrase.help.comm, link_preview=True)


@client.on(events.NewMessage(pattern=r"(?i)^/start$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/старт$", func=checks))
async def start(event: Message):
    return await event.reply(
        phrase.start.format(await get_name(event.sender_id, push=False)), silent=True
    )


@client.on(events.NewMessage(pattern=r"(?i)^/пинг(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ping", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ping(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^пинг(.*)", func=checks))
async def ping(event: Message):
    try:
        arg = event.pattern_match.group(1).strip()
    except IndexError:
        arg = ""
    text = await crosssocial.ping(arg, event.date.timestamp())
    if text is None:
        return
    return await event.reply(text)


@client.on(events.NewMessage(pattern=r"(?i)^/крокодил$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/crocodile$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^старт крокодил$", func=checks))
async def crocodile(event: Message):
    if not event.chat_id == config.chats.chat:
        return await event.reply(phrase.crocodile.chat)
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
    try:
        bet = int(event.pattern_match.group(1).strip())
        if bet < db.database("min_bet"):
            return await event.reply(
                phrase.money.min_count.format(
                    decline_number(db.database("min_bet"), "изумруд")
                )
            )
        elif bet > db.database("max_bet"):
            return await event.reply(
                phrase.money.max_count.format(
                    decline_number(db.database("max_bet"), "изумруд")
                )
            )
    except IndexError:
        bet = db.database("min_bet")
    except ValueError:
        return await event.reply(phrase.money.nan_count)
    sender_balance = db.get_money(event.sender_id)
    if sender_balance < bet:
        return await event.reply(
            phrase.money.not_enough.format(decline_number(sender_balance, "изумруд"))
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
        phrase.crocodile.bet.format(decline_number(bet, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/суперигра(.*)", func=checks))
async def super_game(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN,
                name=phrase.roles.admin
            )
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


@client.on(events.NewMessage(pattern=r"(?i)^/ии\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ai\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^ии\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/бот\s(.+)", func=checks))
async def gemini(event: Message):
    arg = event.pattern_match.group(1).strip()
    response = await ai.response(arg)
    if response is None:
        return await event.reply(phrase.server.overload)
    if len(response) > 4096:
        for x in range(0, len(response), 4096):
            await event.reply(response[x : x + 4096])
    else:
        return await event.reply(response)


@client.on(events.NewMessage(pattern=r"(?i)^/ии$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ai$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^ии$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/бот$", func=checks))
async def gemini_empty(event: Message):
    return await event.reply(phrase.no.response)


@client.on(events.NewMessage(pattern=r"//(.+)", func=checks))
async def mcrcon(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN,
                name=phrase.roles.admin
            )
        )
    command = event.pattern_match.group(1).strip()
    logger.info(f"Выполняется команда: {command}")
    try:
        async with MinecraftClient(
            host=db.database("ipv4"),
            port=config.tokens.rcon.port,
            password=config.tokens.rcon.password,
        ) as rcon:
            resp = remove_section_marks(await rcon.send(command))
            logger.info(f"Ответ команды:\n{resp}")
            if len(resp) > 4096:
                for x in range(0, len(resp), 4096):
                    await event.reply(f"```{resp[x:x+4096]}```")
            else:
                return await event.reply(f"```{resp}```")
    except TimeoutError:
        return await event.reply(phrase.server.stopped)


@client.on(events.NewMessage(pattern=r"(?i)^\+вт\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-вт\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+wl\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-wl\s(.+)", func=checks))
async def whitelist(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.VIP:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.VIP,
                name=phrase.roles.vip
            )
        )
    if event.text[0] == "-":
        command = f"swl remove {event.pattern_match.group(1).strip()}"
    else:
        command = f"swl add {event.pattern_match.group(1).strip()}"
    logger.info(f"Выполняется команда: {command}")
    try:
        async with MinecraftClient(
            host=db.database("ipv4"),
            port=config.tokens.rcon.port,
            password=config.tokens.rcon.password,
        ) as rcon:
            resp = remove_section_marks(await rcon.send(command))
            logger.info(f"Ответ команды:\n{resp}")
            return await event.reply(f"✍🏻 : {resp}")
    except TimeoutError:
        return await event.reply(phrase.server.stopped)


@client.on(events.NewMessage(pattern=r"(?i)^\+стафф(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+staff(.*)", func=checks))
async def add_staff(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.OWNER:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.OWNER,
                name=phrase.roles.owner
            )
        )
    arg = event.pattern_match.group(1).strip()
    try:
        user = await client(GetFullUserRequest(arg))
        user = user.full_user.id
        tag = await get_name(user)
    except (IndexError, ValueError):
        reply_to_msg = event.reply_to_msg_id
        if reply_to_msg:
            reply_message = await event.get_reply_message()
            user = reply_message.sender_id
            tag = await get_name(user)
        else:
            return await event.reply(phrase.money.no_people)
    new_role = roles.get(user)+1
    roles.set(user, new_role)
    return await event.reply(phrase.perms.upgrade.format(nick=tag, staff=new_role))


@client.on(events.NewMessage(pattern=r"(?i)^\-staff(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-стафф(.*)", func=checks))
async def add_staff(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.OWNER:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.OWNER,
                name=phrase.roles.owner
            )
        )
    arg = event.pattern_match.group(1).strip()
    try:
        user = await client(GetFullUserRequest(arg))
        user = user.full_user.id
        tag = await get_name(user)
    except (IndexError, ValueError):
        reply_to_msg = event.reply_to_msg_id
        if reply_to_msg:
            reply_message = await event.get_reply_message()
            user = reply_message.sender_id
            tag = await get_name(user)
        else:
            return await event.reply(phrase.money.no_people)
    new_role = roles.get(user)-1
    roles.set(user, new_role)
    return await event.reply(phrase.perms.downgrade.format(nick=tag, staff=new_role))


@client.on(events.NewMessage(pattern=r"(?i)^/топ игроков$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/topplayers$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/bestplayers$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/toppt", func=checks))
async def server_top_list(event: Message):
    try:
        async with MinecraftClient(
            host=db.database("ipv4"),
            port=config.tokens.rcon.port,
            password=config.tokens.rcon.password,
        ) as rcon:
            await event.reply(
                remove_section_marks(await rcon.send("playtime top"))
                .replace("[i] Лидеры по времени на сервере", phrase.stat.server)
                .replace("***", "")
            )
    except TimeoutError:
        return await event.reply(phrase.server.stopped)


@client.on(events.NewMessage(pattern=r"(?i)^/баланс$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^баланс$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/wallet", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^wallet$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мой баланс$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^мой баланс$", func=checks))
async def get_balance(event: Message):
    return await event.reply(
        phrase.money.wallet.format(
            decline_number(db.get_money(event.sender_id), "изумруд")
        )
    )


@client.on(events.NewMessage(pattern=r"(?i)^/изменить баланс(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/change balance(.*)", func=checks))
async def add_balance(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN,
                name=phrase.roles.admin
            )
        )
    args = event.pattern_match.group(1).strip().split()
    try:
        tag = args[1]
        user = await client(GetFullUserRequest(tag))
    except IndexError:
        return await event.reply(
            phrase.money.no_people + phrase.money.change_balance_use
        )
    except ValueError:
        return await event.reply(
            phrase.money.no_such_people + phrase.money.change_balance_use
        )
    try:
        new = int(args[0])
    except IndexError:
        return await event.reply(
            phrase.money.no_count + phrase.money.change_balance_use
        )
    except ValueError:
        return await event.reply(
            phrase.money.nan_count + phrase.money.change_balance_use
        )
    old = db.get_money(user.full_user.id)
    db.add_money(user.full_user.id, new)
    await event.reply(phrase.money.add_money.format(name=tag, old=old, new=old + new))


@client.on(events.NewMessage(pattern=r"(?i)^/скинуть(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/кинуть(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/дать(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/перевести(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^перевести(.*)", func=checks))
async def swap_money(event: Message):
    args = event.pattern_match.group(1).strip()
    if len(args) < 1:
        return await event.reply(phrase.money.no_count + phrase.money.swap_balance_use)
    args = args.split()

    try:
        count = int(args[0])
        if count <= 0:
            return await event.reply(phrase.money.negative_count)
    except ValueError:
        return await event.reply(phrase.money.nan_count + phrase.money.swap_balance_use)

    try:
        tag = args[1]
        user = await client(GetFullUserRequest(tag))
        user = user.full_user.id
    except (TypeError, ValueError, IndexError):
        reply_to_msg = event.reply_to_msg_id
        if reply_to_msg:
            reply_message = await event.get_reply_message()
            user = reply_message.sender_id
        else:
            return await event.reply(
                phrase.money.no_people + phrase.money.swap_balance_use
            )

    entity = await client.get_entity(user)
    if entity.bot:
        return await event.reply(
            phrase.money.bot
        )

    if event.sender_id == user:
        return await event.reply(
            phrase.money.selfbyself
        )
    sender_balance = db.get_money(event.sender_id)
    if sender_balance < count:
        return await event.reply(
            phrase.money.not_enough.format(decline_number(sender_balance, "изумруд"))
        )
    db.add_money(event.sender_id, -count)
    db.add_money(user, count)
    return await event.reply(
        phrase.money.swap_money.format(decline_number(count, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/dns$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/днс$", func=checks))
async def tg_dns(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN,
                name=phrase.roles.admin
            )
        )
    return await event.reply(phrase.dns.format(await ip.setup(True)), parse_mode="html")


@client.on(events.NewMessage(pattern=r"(?i)^/банк$", func=checks))
async def all_money(event: Message):
    return await event.reply(
        phrase.money.all_money.format(decline_number(db.get_all_money(), "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/топ крокодил$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ слова$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/стат крокодил$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/стат слова$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^топ крокодила$", func=checks))
async def crocodile_wins(event: Message):
    all = db.crocodile_stat.get_all()
    text = ""
    n = 1
    for id in all.keys():
        if n > 10:
            break
        text += f"{n}. {await get_name(id, minecraft=True)}: {all[id]}\n"
        n += 1
    return await event.reply(phrase.crocodile.stat.format(text), silent=True)


@client.on(events.NewMessage(pattern=r"(?i)^/слово\s(.+)", func=checks))
async def word_request(event: Message):
    word = event.pattern_match.group(1).strip().lower()
    with open(crocodile_path, "r", encoding="utf-8") as f:
        if word in f.read().split("\n"):
            return await event.reply(phrase.word.exists)
    with open(crocodile_blacklist_path, "r", encoding="utf-8") as f:
        if word in f.read().split("\n"):
            return await event.reply(phrase.word.in_blacklist)
    entity = await get_name(event.sender_id)
    logger.info(f'Пользователь {entity} хочет добавить слово "{word}"')
    keyboard = ReplyInlineMarkup(
        [
            KeyboardButtonRow(
                [
                    KeyboardButtonCallback(
                        text="✅ Добавить",
                        data=f"word.yes.{word}.{event.sender_id}".encode(),
                    ),
                    KeyboardButtonCallback(
                        text="❌ Отклонить",
                        data=f"word.no.{word}.{event.sender_id}".encode(),
                    ),
                ]
            )
        ]
    )
    hint = None
    while hint is None:
        hint = await ai.response(
            f'Сделай подсказку для слова "{word}". '
            'Ни в коем случае не добавляй никаких "подсказка для слова.." '
            "и т.п, ответ должен содержать только подсказку. "
            "Не забудь, что подсказка не должна "
            "содержать слово в любом случае. "
        )
    try:
        await client.send_message(
            config.tokens.bot.creator,
            phrase.word.request.format(user=entity, word=word, hint=hint),
            buttons=keyboard,
        )
    except TGErrors.ButtonDataInvalidError:
        return await event.reply(phrase.word.long)
    return await event.reply(phrase.word.set.format(word=word))


@client.on(events.NewMessage(pattern=r"(?i)^/слова\s(.+)", func=checks))
async def word_requests(event: Message):
    words = event.pattern_match.group(1).strip().lower().split()
    text = ""
    message = await event.reply(phrase.word.checker)
    with open(crocodile_path, "r", encoding="utf-8") as f:
        all_words = f.read().split("\n")
        for word in words:
            if word in all_words:
                text += f"Слово **{word}** - есть\n"
                await message.edit(text)
                words.remove(word)
    with open(crocodile_blacklist_path, "r", encoding="utf-8") as f:
        all_blacklist = f.read().split("\n")
        for word in words:
            if word in all_blacklist:
                text += f"Слово **{word}** - в ЧС\n"
                await message.edit(text)
                words.remove(word)
    if len(words) == 0:
        return
    entity = await get_name(event.sender_id)
    for word in words:
        logger.info(f'Пользователь {entity} хочет добавить слово "{word}"')
        keyboard = ReplyInlineMarkup(
            [
                KeyboardButtonRow(
                    [
                        KeyboardButtonCallback(
                            text="✅ Добавить",
                            data=f"word.yes.{word}.{event.sender_id}".encode(),
                        ),
                        KeyboardButtonCallback(
                            text="❌ Отклонить",
                            data=f"word.no.{word}.{event.sender_id}".encode(),
                        ),
                    ]
                )
            ]
        )
        hint = None
        while hint is None:
            hint = await ai.response(
                f'Сделай подсказку для слова "{word}". '
                'Ни в коем случае не добавляй никаких "подсказка для слова.." '
                "и т.п, ответ должен содержать только подсказку. "
                "Не забудь, что подсказка не должна "
                "содержать слово в любом случае. "
            )
        try:
            await client.send_message(
                config.tokens.bot.creator,
                phrase.word.request.format(user=entity, word=word, hint=hint),
                buttons=keyboard,
            )
            text += f"Слово **{word}** - проверяется\n"
            await message.edit(text)
        except TGErrors.ButtonDataInvalidError:
            text += f"Слово **{word}** - слишком длинное\n"
            await message.edit(text)


@client.on(events.NewMessage(pattern=r"(?i)^/слова$", func=checks))
async def word_requests_empty(event: Message):
    return await event.reply(phrase.word.empty_long)


@client.on(events.NewMessage(pattern=r"(?i)^/слово$", func=checks))
async def word_request_empty(event: Message):
    return await event.reply(phrase.word.empty)


@client.on(events.NewMessage(pattern=r"(?i)^\-слово$", func=checks))
async def word_remove_empty(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN,
                name=phrase.roles.admin
            )
        )
    return await event.reply(phrase.word.rem_empty)


@client.on(events.NewMessage(pattern=r"(?i)^\-слово\s(.+)", func=checks))
async def word_remove(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN,
                name=phrase.roles.admin
            )
        )
    word = event.pattern_match.group(1).strip().lower()
    with open(crocodile_path, "r", encoding="utf-8") as f:
        text = f.read().split("\n")
    if word not in text:
        return await event.reply(phrase.word.not_exists)
    text.remove(word)
    with open(crocodile_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text))
    return await event.reply(
        phrase.word.deleted.format(word)
    )


@client.on(events.NewMessage(pattern=r"(?i)^/nick(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ник(.*)", func=checks))
async def check_nick(event: Message):
    try:
        user = await client(GetFullUserRequest(event.pattern_match.group(1).strip()))
        user = user.full_user.id
    except (TypeError, ValueError, IndexError):
        reply_to_msg = event.reply_to_msg_id
        if reply_to_msg:
            reply_message = await event.get_reply_message()
            user = reply_message.sender_id
        else:
            return await event.reply(phrase.nick.who)
    nick = db.nicks(id=user).get()
    if nick is None:
        return await event.reply(phrase.nick.no_nick)
    return await event.reply(phrase.nick.usernick.format(nick))


@client.on(events.NewMessage(pattern=r"(?i)^/госва$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/государства$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^государства$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^список госв$", func=checks))
async def states_all(event: Message):
    data = db.states.get_all()
    if data == {}:
        return await event.reply(phrase.state.empty_list)
    text = phrase.state.all
    n = 1
    for state in data:
        text += f'{n}. **{state}** - {len(data[state]["players"])} чел.\n'
        n += 1
    return await event.reply(text)


@client.on(events.NewMessage(pattern=r"(?i)^\+госво(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+государство(.*)", func=checks))
async def state_make(event: Message):
    arg = event.pattern_match.group(1).strip()
    if arg == "":
        return await event.reply(phrase.state.no_name)
    if len(arg) > 28:
        return await event.reply(phrase.state.too_long)
    if (not re.fullmatch(r"^[а-яА-ЯёЁa-zA-Z\- ]+$", arg)) or (
        re.fullmatch(r"^[\- ]+$", arg)
    ):
        return await event.reply(phrase.state.not_valid)
    if db.nicks(id=event.sender_id).get() is None:
        return await event.reply(phrase.state.not_connected)
    if db.states.if_author(event.sender_id) is not False:
        return await event.reply(phrase.state.already_author)
    if db.states.if_player(event.sender_id) is not False:
        return await event.reply(phrase.state.already_player)
    arg = arg.capitalize()
    if db.states.add(arg, event.sender_id) is not True:
        return await event.reply(phrase.state.already_here)
    await client.send_message(
        entity=config.chats.chat,
        message=phrase.state.make.format(arg),
        reply_to=config.chats.topics.rp,
    )
    return await event.reply(phrase.state.make.format(arg))


@client.on(events.NewMessage(pattern=r"(?i)^/вступить(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^вступить(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г вступить(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г войти(.*)", func=checks))
async def state_enter(event: Message):
    arg = event.pattern_match.group(1).strip()
    if arg == "":
        return await event.reply(phrase.state.no_name)
    if db.states.find(arg) is False:
        return await event.reply(phrase.state.not_find)
    nick = db.nicks(id=event.sender_id).get()
    if nick is None:
        return await event.reply(phrase.state.not_connected)
    if db.states.if_player(event.sender_id) is not False:
        return await event.reply(phrase.state.already_player)
    if db.states.if_author(event.sender_id) is not False:
        return await event.reply(phrase.state.already_author)
    state = db.state(arg)
    if state.enter != True:
        return await event.reply(phrase.state.enter_exit)
    if state.price != 0:
        return await event.reply(
            phrase.state.pay_to_enter,
            buttons=ReplyInlineMarkup(
                [
                    KeyboardButtonRow(
                        [
                            KeyboardButtonCallback(
                                text=f"✅ Оплатить вход ({state.price})",
                                data=f"state.pay.{state.name}".encode(),
                            )
                        ]
                    )
                ]
            ),
        )
    players = state.players
    players.append(event.sender_id)
    state.change("players", players)
    state_name = state.name.capitalize()
    await client.send_message(
        entity=config.chats.chat,
        message=phrase.state.new_player.format(state=state_name, player=nick),
        reply_to=config.chats.topics.rp,
    )
    if (state.type == 0) and (len(players) >= config.coofs.Type1Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.up.format(name=state_name, type="Государство"),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 1)
    if (state.type == 1) and (len(players) >= config.coofs.Type2Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.up.format(name=state_name, type="Империя"),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 2)
    return await event.reply(phrase.state.admit.format(state_name))


@client.on(events.NewMessage(pattern=r"(?i)^/госво(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/государство(.*)", func=checks))
async def state_get(event: Message):
    arg = event.pattern_match.group(1).strip()
    if arg == "":
        player_in = db.states.if_player(event.sender_id)
        if player_in is not False:
            arg = player_in
        author_in = db.states.if_author(event.sender_id)
        if author_in is not False:
            arg = author_in
        else:
            return await event.reply(phrase.state.no_name)
    if db.states.find(arg) is False:
        return await event.reply(phrase.state.not_find)
    state = db.state(arg)
    enter = "Свободный" if state.enter else "Закрыт"
    if state.price > 0:
        enter = decline_number(state.price, "изумруд")
    tasks = [get_name(player, minecraft=True) for player in state.players]
    idented_players = await asyncio.gather(*tasks)
    return await event.reply(
        phrase.state.get.format(
            type=phrase.state_types[state.type],
            name=state.name.capitalize(),
            money=decline_number(int(state.money), "изумруд"),
            author=db.nicks(id=state.author).get(),
            enter=enter,
            desc=state.desc,
            date=state.date,
            players=len(state.players),
            list_players=", ".join(idented_players),
            xyz=state.coordinates,
        ),
        silent=True,
    )


@client.on(events.NewMessage(pattern=r"(?i)^/ливнуть", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/покинуть госво", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/покинуть государство", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^выйти из государства", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^выйти из госва", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г покинуть", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г выйти", func=checks))
async def state_leave(event: Message):
    state_name = db.states.if_player(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_member)
    state = db.state(state_name)
    state.players.remove(event.sender_id)
    state.change("players", state.players)
    state_name = state.name.capitalize()
    await client.send_message(
        entity=config.chats.chat,
        message=phrase.state.leave_player.format(
            state=state_name, player=db.nicks(id=event.sender_id).get()
        ),
        reply_to=config.chats.topics.rp,
    )
    if (state.type == 2) and (len(state.players) < config.coofs.Type2Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.down.format(name=state.name, type="Государство"),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 1)
    if (state.type == 1) and (len(state.players) < config.coofs.Type1Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.down.format(name=state_name, type="Княжество"),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 0)
    return await event.reply(phrase.state.leave)


@client.on(events.NewMessage(pattern=r"(?i)^/уничтожить госво", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/удалить госво", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/уничтожить государство", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/удалить государство", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^уничтожить государство", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^удалить государство", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г уничтожить", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г удалить", func=checks))
async def state_rem(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    keyboard = ReplyInlineMarkup(
        [
            KeyboardButtonRow(
                [
                    KeyboardButtonCallback(
                        text=phrase.state.rem_button, data=f"state.remove.{state_name}".encode()
                    )
                ]
            )
        ]
    )
    return await event.reply(
        phrase.state.rem_message.format(name=state_name),
        buttons=keyboard
    )


@client.on(events.NewMessage(pattern=r"(?i)^/г описание$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/о госве$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г о госве$", func=checks))
async def state_desc_empty(event: Message):
    return await event.reply(phrase.state.no_desc)


@client.on(events.NewMessage(pattern=r"(?i)^/г описание\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/о госве\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г о госве\s(.+)", func=checks))
async def state_desc(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    new_desc = event.pattern_match.group(1).strip()
    if len(new_desc) > config.coofs.DescriptionsMaxLen:
        return await event.reply(
            phrase.state.max_len.format(config.coofs.DescriptionsMaxLen)
        )
    db.state(state_name).change("desc", new_desc)
    return await event.reply(phrase.state.change_desc)


@client.on(events.NewMessage(pattern=r"(?i)^/г корды$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г координаты$", func=checks))
async def state_coords_empty(event: Message):
    return await event.reply(phrase.state.howto_change_coords)


@client.on(events.NewMessage(pattern=r"(?i)^/г корды\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г координаты\s(.+)", func=checks))
async def state_coords(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    arg = event.pattern_match.group(1).strip()
    try:
        arg = list(map(int, arg.split()))
    except ValueError:
        return await event.reply(phrase.state.howto_change_coords)
    if len(arg) != 3:
        return await event.reply(phrase.state.howto_change_coords)
    db.state(state_name).change("coordinates", ", ".join(list(map(str, arg))))
    return await event.reply(phrase.state.change_coords)


@client.on(events.NewMessage(pattern=r"(?i)^/г входы\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г вступления\s(.+)", func=checks))
async def state_enter(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    arg = event.pattern_match.group(1).strip()
    state = db.state(state_name)
    if arg in ["да", "+", "разрешить", "открыть", "true", "ok", "ок", "можно"]:
        if state.enter is True:
            return await event.reply(phrase.state.already_open)
        state.change("enter", True)
        return await event.reply(phrase.state.enter_open)
    elif arg in [
        "нет",
        "-",
        "запретить",
        "закрыть",
        "false",
        "no",
        "нельзя",
        "закрыто",
    ]:
        if state.enter is False:
            return await event.reply(phrase.state.already_close)
        state.change("enter", False)
        return await event.reply(phrase.state.enter_close)
    elif arg.isdigit():
        arg = int(arg)
        state.change("price", arg)
        state.change("enter", True)
        return await event.reply(
            phrase.state.enter_price.format(decline_number(arg, "изумруд"))
        )
    else:
        return await event.reply(phrase.state.howto_enter)


@client.on(events.NewMessage(pattern=r"(?i)^/г входы$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г вступления$", func=checks))
async def state_enter(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    state = db.state(state_name)
    if state.enter is True:
        if state.price != 0:
            state.change("price", 0)
        state.change("enter", False)
        return await event.reply(phrase.state.enter_close)
    elif state.enter is False:
        state.change("enter", True)
        return await event.reply(phrase.state.enter_open)


@client.on(events.NewMessage(pattern=r"(?i)^/пополнить казну\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г пополнить\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+казна\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^г пополнить\s(.+)", func=checks))
async def state_add_money(event: Message):
    state_name = db.states.if_player(event.sender_id)
    if state_name is False:
        state_name = db.states.if_author(event.sender_id)
        if state_name is False:
            return await event.reply(phrase.state.not_a_member)
    arg = event.pattern_match.group(1).strip()
    if not arg.isdigit():
        return await event.reply(phrase.state.howto_add_balance)
    try:
        arg = int(arg)
    except Exception:
        return await event.reply(phrase.state.howto_add_balance)
    if arg < 1:
        return await event.reply(phrase.money.negative_count)
    balance = db.get_money(event.sender_id)
    if arg > balance:
        return await event.reply(
            phrase.money.not_enough.format(decline_number(balance, "изумруд"))
        )
    db.add_money(event.sender_id, -arg)
    state = db.state(state_name)
    state.change("money", state.money + arg)
    logger.info(f"Казна {state_name} пополнена на {arg}")
    return await event.reply(
        phrase.state.add_treasury.format(decline_number(arg, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/пополнить казну$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г пополнить$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+казна$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^г пополнить$", func=checks))
async def state_add_money_empty(event: Message):
    return await event.reply(phrase.state.howto_add_balance)


@client.on(events.NewMessage(pattern=r"(?i)^/забрать из казны\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г снять\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-казна\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^г снять\s(.+)", func=checks))
async def state_rem_money(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    arg = event.pattern_match.group(1).strip()
    if not arg.isdigit():
        return await event.reply(phrase.state.howto_rem_balance)
    try:
        arg = int(arg)
    except Exception:
        return await event.reply(phrase.state.howto_rem_balance)
    if arg < 1:
        return await event.reply(phrase.money.negative_count)
    state = db.state(state_name)
    if state.money < arg:
        return await event.reply(phrase.state.too_low)
    state.change("money", state.money - arg)
    db.add_money(event.sender_id, arg)
    return await event.reply(
        phrase.state.rem_treasury.format(decline_number(arg, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/забрать из казны$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г снять$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-казна$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^г снять$", func=checks))
async def state_rem_money_empty(event: Message):
    return await event.reply(phrase.state.howto_rem_balance)


@client.on(events.NewMessage(pattern=r"(?i)^/г шахта$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г майнить$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г копать$, func=checks"))
@client.on(events.NewMessage(pattern=r"(?i)^/шахта$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/майнить$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/копать$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^шахта$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^майнить$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^копать$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/mine", func=checks))
async def mine(event: Message):
    if (db.states.if_player(event.sender_id) is False) and (
        db.states.if_author(event.sender_id) is False
    ):
        return await event.reply(phrase.mine.not_in_state)
    if db.ready_to_mine(event.sender_id) is False:
        return await event.reply(choice(phrase.mine.not_ready))
    added = randint(1, config.coofs.MineMaxGems)
    db.add_money(event.sender_id, added)
    return await event.reply(phrase.mine.done.format(decline_number(added, "изумруд")))


@client.on(events.NewMessage(pattern=r"(?i)^/time", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/время$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мск$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/msk$", func=checks))
async def msktime(event: Message):
    return await event.reply(phrase.time.format(datetime.now().strftime("%H:%M:%S")))


@client.on(events.NewMessage(pattern=r"(?i)^/обо мне$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/я$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/i$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/profile", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/myprofile", func=checks))
async def profile(event: Message):
    role = db.roles().get(event.sender_id)
    state = db.states.if_author(event.sender_id)
    if state is False:
        state = db.states.if_player(event.sender_id)
        if state is False:
            state = "Не состоит в государстве"
        else:
            state = f"{state}, Житель"
    else:
        state = f"**{state}, Глава**"
    nick = db.nicks(id=event.sender_id).get()
    if nick is not None:
        m_day = db.statistic(1).get(nick)
        m_week = db.statistic(7).get(nick)
        m_month = db.statistic(30).get(nick)
        m_all = db.statistic().get(nick, all_days=True)
    else:
        m_day = 0
        m_week = 0
        m_month = 0
        m_all = 0
        nick = "Не привязан"
    return await event.reply(
        phrase.profile.full.format(
            name=await get_name(event.sender_id, push=False),
            minecraft=nick,
            role_name=phrase.roles.types[role],
            role_number=role,
            state=state,
            m_day=m_day,
            m_week=m_week,
            m_month=m_month,
            m_all=m_all
        )
    )


@client.on(events.NewMessage(pattern=r"(?i)^/тест\s(.+)", func=checks))
async def test(event: Message):
    arg = event.pattern_match.group(1).strip()
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN,
                name=phrase.roles.admin
            )
        )
    return event.reply(event.stringify())


"Эвенты для крокодила"


async def crocodile_hint(event: Message):
    game = db.database("current_game")
    hint = game["hints"]
    if event.sender_id in hint:
        return await event.reply(phrase.crocodile.hints_all)
    hint.append(event.sender_id)
    game["hints"] = hint
    db.database("current_game", game)
    word = game["word"]
    last_hint = db.database("crocodile_last_hint")
    if random() < config.coofs.PercentForRandomLetter and last_hint != 0:
        n = 1
        for letter in list(db["unsec"]):
            if letter == "_":
                response = f'{n} буква в слове - **{db["word"][n-1]}**'
                break
            n += 1
    else:
        if last_hint != 0:
            check_last = "Так же учитывай, " f"что подсказка {last_hint} уже была."
        else:
            check_last = ""
        response = await ai.response(
            f'Сделай подсказку для слова "{word}". '
            'Ни в коем случае не добавляй никаких "подсказка для слова.." '
            "и т.п, ответ должен содержать только подсказку. "
            "Не забудь, что подсказка не должна "
            "содержать слово в любом случае. " + check_last
        )
        if response is None:
            game = db.database("current_game")
            hint = game["hints"]
            hint.remove(event.sender_id)
            game["hints"] = hint
            db.database("current_game", game)
            return await event.reply(phrase.crocodile.error)
        db.database("crocodile_last_hint", response)
    return await event.reply(response)


async def crocodile_handler(event: Message):
    text = event.text.strip().lower()
    if len(text) > 0:
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
                    decline_number(all, "изумруд"),
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


if db.database("current_game", log=False) != 0:
    client.add_event_handler(
        crocodile_handler, events.NewMessage(chats=config.chats.chat)
    )
    client.add_event_handler(
        crocodile_hint, events.NewMessage(pattern=r"(?i)^/подсказка$", func=checks)
    )
