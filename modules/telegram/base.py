from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

import ping3
import aiohttp
import re
import asyncio

from time import time
from random import choice, randint, random
from datetime import datetime

from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon import errors as TGErrors
from telethon import events
from telethon.tl.custom import Message

from .client import client
from .global_checks import *
from .func import get_name

from .. import (
    ai,
    config,
    patches,
    formatter,
    pic
)
from ..system_info import get_system_info


@client.on(events.NewMessage(pattern=r"(?i)^/хост$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/host$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/айпи$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ip", func=checks))
async def host(event: Message):
    return await event.reply(
        phrase.server.host.format(
            v4=db.database("host"),
            v6=f'{db.database("ipv6_subdomain")}.{db.database("host")}',
        )
    )


@client.on(events.NewMessage(pattern=r"(?i)^/помощь$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/help", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/команды$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/commands$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^команды$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^бот помощь$", func=checks))
async def help(event: Message):
    return await event.reply(phrase.help.comm, link_preview=True)


@client.on(events.NewMessage(pattern=r"(?i)^/пинг(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ping(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^пинг(.*)", func=checks))
async def ping(event: Message):
    arg = event.pattern_match.group(1).strip()
    ping = round(time() - event.date.timestamp(), 2)
    if ping < 0:
        ping = phrase.ping.min
    else:
        ping = f"за {str(ping)} сек."
    all_servers_ping = []
    if arg in [
        "all",
        "подробно",
        "подробный",
        "полн",
        "полный",
        "весь",
        "ии",
        "фулл",
        "full",
    ]:
        async with aiohttp.ClientSession() as session:
            n = 1
            for server in ai.ai_servers:
                timestamp = time()
                async with session.get(f"https://{server}/") as request:
                    try:
                        if await request.text() == "ok":
                            server_ping = round(time() - timestamp, 1)
                            textping = (
                                f"{server_ping} сек."
                                if server_ping > 0
                                else phrase.ping.min_ai
                            )
                            all_servers_ping.append(f"🌐 : ИИ сервер №{n} - {textping}")
                        else:
                            all_servers_ping.append(f"❌ : ИИ сервер №{n} - Ошибка!")
                    except Exception:
                        all_servers_ping.append(f"❌ : ИИ сервер №{n} - Выключен!")
                n += 1
        all_servers_ping.append(
            f"🌐 : Пинг сервера - {int(round(ping3.ping('yandex.ru'), 3)*1000)} мс"
        )
    text = f"{phrase.ping.set.format(ping)}\n{'\n'.join(all_servers_ping)}"
    return await event.reply(text)


@client.on(events.NewMessage(pattern=r"(?i)^/start$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/старт$", func=checks))
async def start(event: Message):
    return await event.reply(
        phrase.start.format(await get_name(event.sender_id, push=False)), silent=True
    )


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
            m_all=m_all,
            balance=formatter.value_to_str(db.get_money(event.sender_id), "изумруд"),
        )
    )


@client.on(events.NewMessage(pattern=r"(?i)^/time", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/время$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мск$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/msk$", func=checks))
async def msktime(event: Message):
    return await event.reply(phrase.time.format(datetime.now().strftime("%H:%M:%S")))


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

    if random() < config.coofs.ChanceToDie:
        added = randint(1, config.coofs.MineMaxGems)
        balance = db.get_money(event.sender_id)
        if balance < added:
            added = balance
        text = choice(phrase.mine.die).format(
            killer=choice(phrase.mine.killers), value=formatter.value_to_str(added, "изумруд")
        )
        db.add_money(event.sender_id, -added)
    if random() < config.coofs.ChanceToBoost:
        added = randint(config.coofs.MineMaxGems, config.coofs.MineMaxBoost)
        text = choice(phrase.mine.boost).format(formatter.value_to_str(added, "изумруд"))
        db.add_money(event.sender_id, added)
    else:
        added = randint(1, config.coofs.MineMaxGems)
        text = phrase.mine.done.format(formatter.value_to_str(added, "изумруд"))
        db.add_money(event.sender_id, added)
    return await event.reply(text)


@client.on(events.NewMessage(pattern=r"(?i)^/слово\s(.+)", func=checks))
async def word_request(event: Message):
    word = event.pattern_match.group(1).strip().lower()
    with open(patches.crocodile_path, "r", encoding="utf-8") as f:
        if word in f.read().split("\n"):
            return await event.reply(phrase.word.exists)
    with open(patches.crocodile_blacklist_path, "r", encoding="utf-8") as f:
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
    with open(patches.crocodile_path, "r", encoding="utf-8") as f:
        all_words = f.read().split("\n")
        for word in words:
            if word in all_words:
                text += f"Слово **{word}** - есть\n"
                await message.edit(text)
                words.remove(word)
    with open(patches.crocodile_blacklist_path, "r", encoding="utf-8") as f:
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
            phrase.roles.no_perms.format(level=roles.ADMIN, name=phrase.roles.admin)
        )
    return await event.reply(phrase.word.rem_empty)


@client.on(events.NewMessage(pattern=r"(?i)^\-слово\s(.+)", func=checks))
async def word_remove(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(level=roles.ADMIN, name=phrase.roles.admin)
        )
    word = event.pattern_match.group(1).strip().lower()
    with open(patches.crocodile_path, "r", encoding="utf-8") as f:
        text = f.read().split("\n")
    if word not in text:
        return await event.reply(phrase.word.not_exists)
    text.remove(word)
    with open(patches.crocodile_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text))
    return await event.reply(phrase.word.deleted.format(word))


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
            return await event.reply(
                phrase.nick.urnick.format(db.nicks(id=event.sender_id).get())
            )
    nick = db.nicks(id=user).get()
    if nick is None:
        return await event.reply(phrase.nick.no_nick)
    return await event.reply(phrase.nick.usernick.format(nick))


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
        return await event.reply(phrase.money.bot)

    if event.sender_id == user:
        return await event.reply(phrase.money.selfbyself)
    sender_balance = db.get_money(event.sender_id)
    if sender_balance < count:
        return await event.reply(
            phrase.money.not_enough.format(formatter.value_to_str(sender_balance, "изумруд"))
        )
    db.add_money(event.sender_id, -count)
    db.add_money(user, count)
    return await event.reply(
        phrase.money.swap_money.format(formatter.value_to_str(count, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/баланс$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^баланс$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/wallet", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^wallet$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мой баланс$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^мой баланс$", func=checks))
async def get_balance(event: Message):
    return await event.reply(
        phrase.money.wallet.format(
            formatter.value_to_str(db.get_money(event.sender_id), "изумруд")
        )
    )


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
                price=formatter.value_to_str(config.coofs.PriceForChangeNick, "изумруд")
            ),
            buttons=keyboard,
        )

    db.add_money(event.sender_id, config.coofs.LinkGift)
    db.nicks(nick, event.sender_id).link()
    return await event.reply(
        phrase.nick.success.format(formatter.value_to_str(config.coofs.LinkGift, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/серв$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/сервер", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/server", func=checks))
async def sysinfo(event: Message):
    await event.reply(get_system_info())


@client.on(events.NewMessage(pattern=r"(?i)^/randompic", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/рандомпик$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/картинка$", func=checks))
async def randompic(event: Message):
    logger.info(f"Запрошена случайная картинка (id {event.sender_id})")
    return await client.send_file(
        entity=event.chat_id,
        file=pic.get_random(),
        reply_to=event.id,
        caption=phrase.pic.get
    )


@client.on(events.NewMessage(pattern=r"(?i)^/map", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мап$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/карта$", func=checks))
async def getmap(event: Message):
    return await event.reply(phrase.get_map)


@client.on(events.NewMessage(pattern=r"(?i)^/тест$", func=checks))
async def test(event: Message):
    t1 = time()
    # await event.reply(
    #     f"urid {await db.Users.get_by_id(event.sender_id)}"
    # )
    # await event.reply(
    #     f"allid {await db.Users.get_all()}"
    # )

    message = await event.reply(f"ping is {round(time() - t1, 2)} s.")
    await asyncio.sleep(3)
    await message.edit('edited.')