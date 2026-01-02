import asyncio
import re
from datetime import datetime
from random import randint, choice
from time import time
import aioping
from loguru import logger
from telethon import errors as TGErrors
from telethon import events, Button
from telethon.tl import types
from telethon.tl.custom import Message
from telethon.tl.functions.users import GetFullUserRequest
from .. import ai, config, db, formatter, mcrcon, pathes, phrase, pic, mining
from ..system_info import get_system_info
from .client import client
from .func import get_name
from .global_checks import checks, func

logger.info(f"Загружен модуль {__name__}!")


@client.on(events.NewMessage(pattern=r"(?i)^/хост$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/host$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/айпи$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ip", func=checks))
async def host(event: Message):
    return await event.reply(
        phrase.server.host.format(
            v4=db.database("host"),
            v6=db.database("ipv6_host"),
            hint="https://trassert.ru/wiki/info/ipv6",
        ),
        link_preview=False,
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
    latency = round(time() - event.date.timestamp(), 2)
    latency_text = phrase.ping.min if latency <= 0 else f"за {latency!s} сек."
    extra_pings = []
    if arg in {
        "all",
        "подробно",
        "подробный",
        "полн",
        "полный",
        "весь",
        "фулл",
        "full",
    }:
        ms = int((await aioping.ping("yandex.ru")) * 1000)
        extra_pings.append(f"🌐 : Пинг сервера - {ms} мс")
    text = f"{phrase.ping.set.format(latency_text)}\n{'\n'.join(extra_pings)}"
    return await event.reply(text)


@client.on(events.NewMessage(pattern=r"(?i)^/start$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/старт$", func=checks))
async def start(event: Message):
    return await event.reply(
        phrase.start.format(await get_name(event.sender_id, push=False)),
        silent=True,
    )


@client.on(events.NewMessage(pattern=r"(?i)^/обо мне$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/я$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/i$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/profile", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/профиль$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/myprofile", func=checks))
async def profile(event: Message):
    user_id = event.sender_id
    role = db.roles().get(user_id)
    state = db.states.if_author(user_id)
    if state is False:
        state = db.states.if_player(user_id)
        state = state if state is not False else "Не состоит в государстве"
    else:
        state = f"**{state}, Глава**"
    nick = db.nicks(id=user_id).get()
    if nick is not None:
        m_day = db.statistic(1).get(nick)
        m_week = db.statistic(7).get(nick)
        m_month = db.statistic(30).get(nick)
        m_all = db.statistic().get(nick, all_days=True)
        try:
            async with mcrcon.Vanilla as rcon:
                time_played = (
                    await rcon.send(
                        f"papi parse --null %PTM_playtime_{nick}:luminto%"
                    )
                ).replace("\n", "")
        except Exception:
            time_played = "Неизвестно"
    else:
        m_day = m_week = m_month = m_all = 0
        nick = "Не привязан"
        time_played = "-"
    return await event.reply(
        phrase.profile.full.format(
            name=await get_name(user_id, push=False),
            minecraft=nick,
            role_name=phrase.roles.types[role],
            role_number=role,
            state=state,
            m_day=m_day,
            m_week=m_week,
            m_month=m_month,
            m_all=m_all,
            balance=formatter.value_to_str(
                await db.get_money(user_id), "изумруд"
            ),
            time=time_played,
        ),
    )


@client.on(events.NewMessage(pattern=r"(?i)^/time", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/время$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мск$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/msk$", func=checks))
async def msktime(event: Message):
    return await event.reply(
        phrase.time.format(datetime.now().strftime("%H:%M:%S")),
    )


@client.on(
    events.NewMessage(
        pattern=r"(?i)^(/г )?(шахта|майнить|копать)$", func=checks
    )
)
@client.on(events.NewMessage(pattern=r"(?i)^/mine$", func=checks))
@client.on(
    events.NewMessage(pattern=r"(?i)^/(шахта|майнить|копать)$", func=checks)
)
async def mine_start(event: Message):
    user_id = event.sender_id
    if not (db.states.if_player(user_id) or db.states.if_author(user_id)):
        return await event.reply(phrase.mine.not_in_state)
    if not db.ready_to_mine(user_id):
        return await event.reply(choice(phrase.mine.not_ready))
    if user_id in mining.sessions:
        return await event.reply(phrase.mine.already)
    initial = randint(1, config.coofs.Mining.InitialGems)
    mining.sessions[user_id] = {
        "gems": initial,
        "death_chance": config.coofs.Mining.BaseDeathChance,
        "step": 1,
    }
    asyncio.create_task(mining.cleanup_session(user_id))
    buttons = [
        [Button.inline(phrase.mine.button_yes, f"mine.yes.{user_id}")],
        [Button.inline(phrase.mine.button_no, f"mine.no.{user_id}")],
    ]
    return await event.reply(
        phrase.mine.done.format(formatter.value_to_str(initial, "изумруд"))
        + phrase.mine.q,
        buttons=buttons,
    )


@client.on(events.NewMessage(pattern=r"(?i)^/слово (.+)", func=checks))
async def word_request(event: Message):
    word = event.pattern_match.group(1).strip().lower()
    with open(pathes.crocoall, encoding="utf-8") as f:
        if word in f.read().split("\n"):
            return await event.reply(phrase.word.exists)
    with open(pathes.crocobl, encoding="utf-8") as f:
        if word in f.read().split("\n"):
            return await event.reply(phrase.word.in_blacklist)
    entity = await get_name(event.sender_id)
    logger.info(f'Пользователь {event.sender_id} хочет добавить слово "{word}"')
    keyboard = types.ReplyInlineMarkup(
        [
            types.KeyboardButtonRow(
                [
                    types.KeyboardButtonCallback(
                        "✅ Добавить",
                        f"word.yes.{word}.{event.sender_id}".encode(),
                    ),
                    types.KeyboardButtonCallback(
                        "❌ Отклонить",
                        f"word.no.{word}.{event.sender_id}".encode(),
                    ),
                ]
            ),
        ]
    )
    try:
        await client.send_message(
            config.tokens.bot.creator,
            phrase.word.request.format(
                user=entity,
                word=word,
                hint=await ai.CrocodileChat.send_message(word),
            ),
            buttons=keyboard,
        )
    except TGErrors.ButtonDataInvalidError:
        return await event.reply(phrase.word.long)
    return await event.reply(phrase.word.set.format(word=word))


@client.on(events.NewMessage(pattern=r"(?i)^/слова\s([\s\S]+)", func=checks))
async def word_requests(event: Message):
    words = [
        w.strip()
        for w in event.pattern_match.group(1).strip().lower().split()
        if w.strip()
    ]
    if not words:
        return await event.reply(phrase.word.empty_long)
    text = ""
    message = await event.reply(phrase.word.checker)

    def load_wordlist(filepath):
        with open(filepath, encoding="utf-8") as f:
            return set(f.read().split("\n"))

    existing = load_wordlist(pathes.crocoall)
    blacklisted = load_wordlist(pathes.crocobl)
    pending = []
    for word in words:
        if word in existing:
            text += f"Слово **{word}** - есть\n"
        elif word in blacklisted:
            text += f"Слово **{word}** - в ЧС\n"
        else:
            pending.append(word)
        await message.edit(text)
        await asyncio.sleep(0.5)
    if not pending:
        return
    entity = await get_name(event.sender_id)
    for word in pending:
        logger.info(
            f'Пользователь {event.sender_id} хочет добавить слово "{word}"'
        )
        keyboard = types.ReplyInlineMarkup(
            [
                types.KeyboardButtonRow(
                    [
                        types.KeyboardButtonCallback(
                            "✅ Добавить",
                            f"word.yes.{word}.{event.sender_id}".encode(),
                        ),
                        types.KeyboardButtonCallback(
                            "❌ Отклонить",
                            f"word.no.{word}.{event.sender_id}".encode(),
                        ),
                    ]
                ),
            ]
        )
        try:
            await client.send_message(
                config.tokens.bot.creator,
                phrase.word.request.format(
                    user=entity,
                    word=word,
                    hint=await ai.CrocodileChat.send_message(word),
                ),
                buttons=keyboard,
            )
            text += f"Слово **{word}** - проверяется\n"
        except TGErrors.ButtonDataInvalidError:
            text += f"Слово **{word}** - слишком длинное\n"
        await message.edit(text)
        await asyncio.sleep(0.5)


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
                level=roles.ADMIN, name=phrase.roles.admin
            )
        )
    return await event.reply(phrase.word.rem_empty)


@client.on(events.NewMessage(pattern=r"(?i)^\-слово\s(.+)", func=checks))
async def word_remove(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN, name=phrase.roles.admin
            )
        )
    word = event.pattern_match.group(1).strip().lower()
    with open(pathes.crocoall, encoding="utf-8") as f:
        wordlist = f.read().split("\n")
    if word not in wordlist:
        return await event.reply(phrase.word.not_exists)
    wordlist.remove(word)
    with open(pathes.crocoall, "w", encoding="utf-8") as f:
        f.write("\n".join(wordlist))
    return await event.reply(phrase.word.deleted.format(word))


@client.on(events.NewMessage(pattern=r"(?i)^/nick(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ник(.*)", func=checks))
async def check_nick(event: Message):
    arg = event.pattern_match.group(1).strip()
    if arg:
        try:
            user = (await client(GetFullUserRequest(arg))).full_user.id
        except (TypeError, ValueError, IndexError):
            user = await func.get_author_by_msgid(
                event.chat_id, func.get_reply_message_id(event)
            )
    else:
        user = await func.get_author_by_msgid(
            event.chat_id, func.get_reply_message_id(event)
        )
    if user is None:
        author_nick = db.nicks(id=event.sender_id).get()
        if author_nick is None:
            return await event.reply(phrase.nick.who)
        return await event.reply(phrase.nick.urnick.format(author_nick))
    nick = db.nicks(id=user).get()
    await event.reply(
        phrase.nick.no_nick
        if nick is None
        else phrase.nick.usernick.format(nick)
    )


@client.on(events.NewMessage(pattern=r"(?i)^/скинуть(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/кинуть(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/дать(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/перевести(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^перевести(.*)", func=checks))
async def swap_money(event: Message):
    args = event.pattern_match.group(1).strip().split()
    if not args:
        return await event.reply(
            phrase.money.no_count + phrase.money.swap_balance_use
        )
    try:
        count = int(args[0])
        if count <= 0:
            return await event.reply(phrase.money.negative_count)
    except ValueError:
        if args[0].lower() not in {"все", "всё", "all", "весь"}:
            return await event.reply(
                phrase.money.nan_count + phrase.money.swap_balance_use
            )
        count = await db.get_money(event.sender_id)
        if count == 0:
            return await event.reply(phrase.money.empty)
    try:
        tag = args[1]
        user = (await client(GetFullUserRequest(tag))).full_user.id
    except (TypeError, ValueError, IndexError):
        if event.reply_to_msg_id:
            user = (await event.get_reply_message()).sender_id
        else:
            return await event.reply(
                phrase.money.no_people + phrase.money.swap_balance_use
            )
    entity = await client.get_entity(user)
    if entity.bot:
        return await event.reply(phrase.money.bot)
    if event.sender_id == user:
        return await event.reply(phrase.money.selfbyself)
    sender_balance = await db.get_money(event.sender_id)
    if sender_balance < count:
        return await event.reply(
            phrase.money.not_enough.format(
                formatter.value_to_str(sender_balance, "изумруд")
            )
        )
    db.add_money(event.sender_id, -count)
    db.add_money(user, count)
    return await event.reply(
        phrase.money.swap_money.format(formatter.value_to_str(count, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/вывести (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/вывод (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/вмайн (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/в майн (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/вмаин (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/в маин (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^вывести (.+)", func=checks))
async def money_to_server(event: Message):
    nick = db.nicks(id=event.sender_id).get()
    if nick is None:
        return await event.reply(phrase.nick.not_append)
    try:
        amount = int(event.pattern_match.group(1).strip())
    except ValueError:
        return await event.reply(phrase.money.nan_count)
    if amount < 1:
        return await event.reply(phrase.money.negative_count)
    if amount > config.coofs.WithdrawDailyLimit:
        return await event.reply(phrase.bank.daily_limit)
    if not db.check_withdraw_limit(event.sender_id, amount):
        limit = db.check_withdraw_limit(event.sender_id, 0)
        return await event.reply(
            phrase.bank.limit.format(formatter.value_to_str(limit, "изумруд"))
        )
    balance = await db.get_money(event.sender_id)
    if balance < amount:
        return await event.reply(
            phrase.money.not_enough.format(
                formatter.value_to_str(balance, "изумруд")
            )
        )
    db.add_money(event.sender_id, -amount)
    try:
        async with mcrcon.Vanilla as rcon:
            await rcon.send(f"invgive {nick} emerald {amount}")
    except Exception:
        db.add_money(event.sender_id, amount)
        db.check_withdraw_limit(event.sender_id, -amount)
        return await event.reply(phrase.bank.error)
    return await event.reply(
        phrase.bank.withdraw.format(formatter.value_to_str(amount, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/вывести$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/вывод$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/вмайн$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/в майн$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/вмаин$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/в маин$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^вывести$", func=checks))
async def money_to_server_empty(event: Message):
    return await event.reply(phrase.money.no_count)


@client.on(events.NewMessage(pattern=r"(?i)^/изумруды$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/баланс$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^баланс$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/wallet", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^wallet$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мой баланс$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^мой баланс$", func=checks))
async def get_balance(event: Message):
    balance = await db.get_money(event.sender_id)
    return await event.reply(
        phrase.money.wallet.format(formatter.value_to_str(balance, "изумруд"))
    )


@client.on(
    events.NewMessage(pattern=r"(?i)^/linknick (\S+)\s*(\S*)$", func=checks)
)
@client.on(
    events.NewMessage(pattern=r"(?i)^/привязать (\S+)\s*(\S*)$", func=checks)
)
@client.on(
    events.NewMessage(pattern=r"(?i)^привязать (\S+)\s*(\S*)$", func=checks)
)
@client.on(
    events.NewMessage(pattern=r"(?i)^/новый ник (\S+)\s*(\S*)$", func=checks)
)
@client.on(
    events.NewMessage(pattern=r"(?i)^/линкник (\S+)\s*(\S*)$", func=checks)
)
async def link_nick(event: Message):
    if event.chat_id != config.chats.chat:
        return await event.reply(phrase.nick.chat)
    nick = event.pattern_match.group(1).strip()
    refcode = event.pattern_match.group(2).strip()
    if len(nick) < 4:
        return await event.reply(phrase.nick.too_short)
    if len(nick) > 16:
        return await event.reply(phrase.nick.too_big)
    if not re.match(r"^[A-Za-z0-9_]*$", nick):
        return await event.reply(phrase.nick.invalid)
    if db.nicks(id=event.sender_id).get() == nick:
        return await event.reply(phrase.nick.already_you)
    if db.nicks(nick=nick).get() is not None:
        return await event.reply(phrase.nick.taken)
    if db.nicks(id=event.sender_id).get() is not None:
        keyboard = types.ReplyInlineMarkup(
            [
                types.KeyboardButtonRow(
                    [
                        types.KeyboardButtonCallback(
                            "✅ Сменить",
                            f"nick.{nick}.{event.sender_id}".encode(),
                        ),
                    ]
                ),
            ]
        )
        price = formatter.value_to_str(
            config.coofs.PriceForChangeNick, "изумруд"
        )
        return await event.reply(
            phrase.nick.already_have.format(price=price), buttons=keyboard
        )
    reftext = ""
    if refcode:
        author = db.RefCodes().check_ref(refcode)
        if author is None:
            return await event.reply(phrase.ref.invalid)
        db.add_money(author, config.coofs.RefGift)
        db.add_money(event.sender_id, config.coofs.RefGift)
        reftext = phrase.ref.gift.format(config.coofs.RefGift)
    try:
        async with mcrcon.Vanilla as rcon:
            await rcon.send(f"nwl add name {nick}")
    except Exception:
        logger.error("Внутренняя ошибка при добавлении в белый список")
        return await event.reply(phrase.nick.error)
    db.add_money(event.sender_id, config.coofs.LinkGift)
    db.nicks(nick, event.sender_id).link()
    await event.reply(
        phrase.nick.success.format(
            formatter.value_to_str(config.coofs.LinkGift, "изумруд")
        )
    )
    if reftext:
        try:
            await event.reply(reftext)
            await client.send_message(
                int(author),
                phrase.ref.used.format(
                    user=await get_name(event.sender_id, minecraft=True),
                    amount=config.coofs.RefGift,
                ),
            )
        except Exception:
            logger.info(
                f"Ref {author} is active, but private is closed. Skipping mention."
            )
    return None


@client.on(events.NewMessage(pattern=r"(?i)^/linknick$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/привязать$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^привязать$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/новый ник$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/линкник$", func=checks))
async def link_nick_empty(event: Message):
    if event.chat_id != config.chats.chat:
        return await event.reply(phrase.nick.chat)
    return await event.reply(phrase.nick.not_select)


@client.on(events.NewMessage(pattern=r"(?i)^/серв$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/сервер", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/server", func=checks))
async def sysinfo(event: Message):
    await event.reply(await get_system_info())


@client.on(events.NewMessage(pattern=r"(?i)^/randompic", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/рандомпик$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/картинка$", func=checks))
async def randompic(event: Message):
    logger.info(f"Запрошена случайная картинка (id {event.sender_id})")
    return await client.send_file(
        entity=event.chat_id,
        file=pic.get_random(),
        reply_to=event.id,
        caption=phrase.pic.get,
    )


@client.on(events.NewMessage(pattern=r"(?i)^/map", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мап$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/карта$", func=checks))
async def getmap(event: Message):
    return await event.reply(
        phrase.get_map.format(db.database("host")),
        link_preview=False,
    )


@client.on(events.NewMessage(pattern=r"(?i)^/vote@", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/vote$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/голос$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/голосование$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/проголосовать$", func=checks))
async def vote(event: Message):
    return await client.send_message(
        event.chat_id,
        reply_to=event.id,
        message=phrase.vote,
        link_preview=False,
    )


@client.on(events.NewMessage(pattern=r"(?i)^/нпоиск (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/пник (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/игрок (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/поискпонику (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^игрок (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^нпоиск (.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^пник (.+)", func=checks))
async def check_info_by_nick(event: Message):
    nick = event.pattern_match.group(1).strip()
    userid = db.nicks(nick=nick).get()
    if userid is None:
        return await event.reply(phrase.nick.not_find)
    state = db.states.if_player(userid)
    if state is False:
        state = db.states.if_author(userid)
    state = state if state is not False else "Нет"
    return await event.reply(
        phrase.nick.info.format(
            tg=await func.get_name(userid),
            role=phrase.roles.types[db.roles().get(userid)],
            state=state,
        ),
    )


@client.on(events.NewMessage(pattern=r"(?i)^/нпоиск$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/пник$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/игрок$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/поискпонику$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^игрок$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^нпоиск$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^пник$", func=checks))
async def check_info_by_nick_empty(event: Message):
    return await event.reply(phrase.nick.empty)


@client.on(events.NewMessage(pattern=r"(?i)^\+город (.+)", func=checks))
async def cities_request(event: Message):
    word = event.pattern_match.group(1).strip().lower()
    with open(pathes.chk_city, encoding="utf-8") as f:
        if word in f.read().split("\n"):
            return await event.reply(phrase.cities.exists)
    with open(pathes.bl_city, encoding="utf-8") as f:
        if word in f.read().split("\n"):
            return await event.reply(phrase.cities.in_blacklist)
    entity = await get_name(event.sender_id)
    logger.info(f'Пользователь {event.sender_id} хочет добавить город "{word}"')
    keyboard = types.ReplyInlineMarkup(
        [
            types.KeyboardButtonRow(
                [
                    types.KeyboardButtonCallback(
                        "✅ Добавить",
                        f"cityadd.yes.{word}.{event.sender_id}".encode(),
                    ),
                    types.KeyboardButtonCallback(
                        "❌ Отклонить",
                        f"cityadd.no.{word}.{event.sender_id}".encode(),
                    ),
                ]
            ),
        ]
    )
    try:
        await client.send_message(
            config.tokens.bot.creator,
            phrase.cities.request.format(user=entity, word=word),
            buttons=keyboard,
        )
    except TGErrors.ButtonDataInvalidError:
        return await event.reply(phrase.cities.long)
    return await event.reply(phrase.cities.set.format(word=word))


@client.on(events.NewMessage(pattern=r"(?i)^\+города\s([\s\S]+)", func=checks))
async def cities_requests(event: Message):
    words = [
        w.strip()
        for w in event.pattern_match.group(1).strip().lower().split("\n")
        if w.strip()
    ]
    if not words:
        return await event.reply(phrase.cities.empty_long)
    text = ""
    message = await event.reply(phrase.cities.checker)

    def read_lines(path):
        with open(path, encoding="utf-8") as f:
            return set(f.read().split("\n"))

    existing = read_lines(pathes.chk_city)
    blacklisted = read_lines(pathes.bl_city)
    pending = []
    for word in words:
        if word in existing:
            text += f"Город **{word}** - есть\n"
        elif word in blacklisted:
            text += f"Город **{word}** - в ЧС\n"
        else:
            pending.append(word)
        try:
            await message.edit(text)
        except TGErrors.MessageTooLongError:
            message = await event.reply(phrase.cities.checker)
        await asyncio.sleep(0.5)
    if not pending:
        return
    entity = await get_name(event.sender_id)
    for word in pending:
        logger.info(
            f'Пользователь {event.sender_id} хочет добавить город "{word}"'
        )
        keyboard = types.ReplyInlineMarkup(
            [
                types.KeyboardButtonRow(
                    [
                        types.KeyboardButtonCallback(
                            "✅ Добавить",
                            f"cityadd.yes.{word}.{event.sender_id}".encode(),
                        ),
                        types.KeyboardButtonCallback(
                            "❌ Отклонить",
                            f"cityadd.no.{word}.{event.sender_id}".encode(),
                        ),
                    ]
                ),
            ]
        )
        try:
            await client.send_message(
                config.tokens.bot.creator,
                phrase.cities.request.format(user=entity, word=word),
                buttons=keyboard,
            )
            text += f"Город **{word}** - проверяется\n"
        except TGErrors.ButtonDataInvalidError:
            text += f"Город **{word}** - слишком длинный\n"
        try:
            await message.edit(text)
        except TGErrors.MessageTooLongError:
            message = await event.reply(phrase.cities.checker)
        await asyncio.sleep(0.5)


@client.on(events.NewMessage(pattern=r"(?i)^\+города$", func=checks))
async def cities_requests_empty(event: Message):
    return await event.reply(phrase.cities.empty_long)


@client.on(events.NewMessage(pattern=r"(?i)^\+город$", func=checks))
async def cities_request_empty(event: Message):
    return await event.reply(phrase.cities.empty)


@client.on(events.NewMessage(pattern=r"(?i)^\-город$", func=checks))
async def cities_remove_empty(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN, name=phrase.roles.admin
            )
        )
    return await event.reply(phrase.cities.rem_empty)


@client.on(events.NewMessage(pattern=r"(?i)^\-город\s(.+)", func=checks))
async def cities_remove(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN, name=phrase.roles.admin
            )
        )
    word = event.pattern_match.group(1).strip().lower()
    with open(pathes.chk_city, encoding="utf-8") as f:
        lines = f.read().split("\n")
    if word not in lines:
        return await event.reply(phrase.cities.not_exists)
    lines.remove(word)
    with open(pathes.chk_city, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return await event.reply(phrase.cities.deleted.format(word))


@client.on(events.NewMessage(pattern=r"(?i)^/rules", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/правила$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/правилачата$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/правила сервера$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^rules", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^правила$", func=checks))
async def rules(event: Message):
    return await event.reply(
        phrase.rules.base.format(db.database("host")),
        link_preview=False,
    )


@client.on(events.NewMessage(pattern=r"(?i)^онлайн$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/онлайн$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^online$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/online", func=checks))
async def online(event: Message):
    async with mcrcon.Vanilla as rcon:
        response = await rcon.send("list")
    players = response.split(":", 1)[1].strip() if ":" in response else ""
    player_list = [p.strip() for p in players.split(",")] if players else []
    player_list = [p for p in player_list if p]
    return await event.reply(
        phrase.online.format(
            list=", ".join(player_list), count=len(player_list)
        )
    )
