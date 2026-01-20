import asyncio
import re
from datetime import datetime
from random import randint, choice
from time import time
import aioping
from loguru import logger
from telethon import errors as TGErrors
from telethon import Button
from telethon.tl import types
from telethon.tl.custom import Message
from telethon.tl.functions.users import GetFullUserRequest
from .. import (
    config,
    db,
    formatter,
    mcrcon,
    pathes,
    phrase,
    pic,
    mining,
    floodwait,
)
from ..system_info import get_system_info
from .client import client
from . import func

logger.info(f"Загружен модуль {__name__}!")


@func.new_command(r"/хост$")
@func.new_command(r"/host$")
@func.new_command(r"/айпи$")
@func.new_command(r"/ip")
async def host(event: Message):
    return await event.reply(
        phrase.server.host.format(
            v4=await db.database("host"),
            v6=await db.database("ipv6_host"),
            hint="https://lumintomc.ru/wiki/info/ipv6",
        ),
        link_preview=False,
    )


@func.new_command(r"/помощь$")
@func.new_command(r"/help")
@func.new_command(r"/команды$")
@func.new_command(r"/commands$")
@func.new_command(r"команды$")
@func.new_command(r"бот помощь$")
async def help(event: Message):
    return await event.reply(phrase.help.comm, link_preview=True)


@func.new_command(r"/пинг(.*)")
@func.new_command(r"/ping(.*)")
@func.new_command(r"пинг(.*)")
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


@func.new_command(r"/start$")
@func.new_command(r"/старт$")
async def start(event: Message):
    return await event.reply(
        phrase.start.format(await func.get_name(event.sender_id)),
        silent=True,
    )


@func.new_command(r"/обо мне$")
@func.new_command(r"/я$")
@func.new_command(r"/i$")
@func.new_command(r"/profile")
@func.new_command(r"/профиль$")
@func.new_command(r"/myprofile")
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
            name=await func.get_name(user_id),
            minecraft=nick,
            role_name=phrase.roles.types[role],
            role_number=role,
            state=state,
            m_day=m_day,
            m_week=m_week,
            m_month=m_month,
            m_all=m_all,
            balance=formatter.value_to_str(
                await db.get_money(user_id), phrase.currency
            ),
            time=time_played,
        ),
    )


@func.new_command(r"/time")
@func.new_command(r"/время$")
@func.new_command(r"/мск$")
@func.new_command(r"/msk$")
async def msktime(event: Message):
    return await event.reply(
        phrase.time.format(datetime.now().strftime("%H:%M:%S")),
    )


@func.new_command(r"(/г )?(шахта|майнить|копать)$")
@func.new_command(r"/mine")
@func.new_command(r"/(шахта|майнить|копать)$")
async def mine_start(event: Message):
    user_id = event.sender_id
    if not (db.states.if_player(user_id) or db.states.if_author(user_id)):
        return await event.reply(phrase.mine.not_in_state)
    if not db.ready_to_mine(user_id):
        return await event.reply(choice(phrase.mine.not_ready))
    if user_id in mining.sessions:
        return await event.reply(phrase.mine.already)
    initial = randint(1, config.cfg.Mining.InitialGems)
    mining.sessions[user_id] = {
        "gems": initial,
        "death_chance": config.cfg.Mining.BaseDeathChance,
        "step": 1,
    }
    asyncio.create_task(mining.cleanup_session(user_id))
    buttons = [
        [Button.inline(phrase.mine.button_yes, f"mine.yes.{user_id}")],
        [Button.inline(phrase.mine.button_no, f"mine.no.{user_id}")],
    ]
    return await event.reply(
        phrase.mine.done.format(
            formatter.value_to_str(initial, phrase.currency)
        )
        + phrase.mine.q,
        buttons=buttons,
    )


# @func.new_command(r"/слово (.+)")
# async def word_request(event: Message):
#     word = event.pattern_match.group(1).strip().lower()
#     with open(pathes.crocoall, encoding="utf-8") as f:
#         if word in f.read().split("\n"):
#             return await event.reply(phrase.word.exists)
#     with open(pathes.crocobl, encoding="utf-8") as f:
#         if word in f.read().split("\n"):
#             return await event.reply(phrase.word.in_blacklist)
#     entity = await func.get_name(event.sender_id)
#     logger.info(f'Пользователь {event.sender_id} хочет добавить слово "{word}"')
#     keyboard = types.ReplyInlineMarkup(
#         [
#             types.KeyboardButtonRow(
#                 [
#                     types.KeyboardButtonCallback(
#                         "✅ Добавить",
#                         f"word.yes.{word}.{event.sender_id}".encode(),
#                     ),
#                     types.KeyboardButtonCallback(
#                         "❌ Отклонить",
#                         f"word.no.{word}.{event.sender_id}".encode(),
#                     ),
#                 ]
#             ),
#         ]
#     )
#     try:
#         await client.send_message(
#             config.tokens.bot.creator,
#             phrase.word.request.format(
#                 user=entity,
#                 word=word,
#                 hint=await ai.CrocodileChat.send_message(word),
#             ),
#             buttons=keyboard,
#         )
#     except TGErrors.ButtonDataInvalidError:
#         return await event.reply(phrase.word.long)
#     return await event.reply(phrase.word.set.format(word=word))


# @func.new_command(r"/слова\s([\s\S]+)")
# async def word_requests(event: Message):
#     words = [
#         w.strip()
#         for w in event.pattern_match.group(1).strip().lower().split()
#         if w.strip()
#     ]
#     if not words:
#         return await event.reply(phrase.word.empty_long)
#     text = ""
#     message = await event.reply(phrase.word.checker)

#     def load_wordlist(filepath):
#         with open(filepath, encoding="utf-8") as f:
#             return set(f.read().split("\n"))

#     existing = load_wordlist(pathes.crocoall)
#     blacklisted = load_wordlist(pathes.crocobl)
#     pending = []
#     for word in words:
#         if word in existing:
#             text += f"Слово **{word}** - есть\n"
#         elif word in blacklisted:
#             text += f"Слово **{word}** - в ЧС\n"
#         else:
#             pending.append(word)
#         await message.edit(text)
#         await asyncio.sleep(0.5)
#     if not pending:
#         return
#     entity = await func.get_name(event.sender_id)
#     for word in pending:
#         logger.info(
#             f'Пользователь {event.sender_id} хочет добавить слово "{word}"'
#         )
#         keyboard = types.ReplyInlineMarkup(
#             [
#                 types.KeyboardButtonRow(
#                     [
#                         types.KeyboardButtonCallback(
#                             "✅ Добавить",
#                             f"word.yes.{word}.{event.sender_id}".encode(),
#                         ),
#                         types.KeyboardButtonCallback(
#                             "❌ Отклонить",
#                             f"word.no.{word}.{event.sender_id}".encode(),
#                         ),
#                     ]
#                 ),
#             ]
#         )
#         try:
#             await client.send_message(
#                 config.tokens.bot.creator,
#                 phrase.word.request.format(
#                     user=entity,
#                     word=word,
#                     hint=await ai.CrocodileChat.send_message(word),
#                 ),
#                 buttons=keyboard,
#             )
#             text += f"Слово **{word}** - проверяется\n"
#         except TGErrors.ButtonDataInvalidError:
#             text += f"Слово **{word}** - слишком длинное\n"
#         await message.edit(text)
#         await asyncio.sleep(0.5)


# @func.new_command(r"/слова$")
# async def word_requests_empty(event: Message):
#     return await event.reply(phrase.word.empty_long)


# @func.new_command(r"/слово$")
# async def word_request_empty(event: Message):
#     return await event.reply(phrase.word.empty)


# @func.new_command(r"\-слово$")
# async def word_remove_empty(event: Message):
#     roles = db.roles()
#     if roles.get(event.sender_id) < roles.ADMIN:
#         return await event.reply(
#             phrase.roles.no_perms.format(
#                 level=roles.ADMIN, name=phrase.roles.admin
#             )
#         )
#     return await event.reply(phrase.word.rem_empty)


# @func.new_command(r"\-слово\s(.+)")
# async def word_remove(event: Message):
#     roles = db.roles()
#     if roles.get(event.sender_id) < roles.ADMIN:
#         return await event.reply(
#             phrase.roles.no_perms.format(
#                 level=roles.ADMIN, name=phrase.roles.admin
#             )
#         )
#     word = event.pattern_match.group(1).strip().lower()
#     with open(pathes.crocoall, encoding="utf-8") as f:
#         wordlist = f.read().split("\n")
#     if word not in wordlist:
#         return await event.reply(phrase.word.not_exists)
#     wordlist.remove(word)
#     with open(pathes.crocoall, "w", encoding="utf-8") as f:
#         f.write("\n".join(wordlist))
#     return await event.reply(phrase.word.deleted.format(word))


@func.new_command(r"/nick(.*)")
@func.new_command(r"/ник(.*)")
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


@func.new_command(r"/скинуть(.*)")
@func.new_command(r"/кинуть(.*)")
@func.new_command(r"/дать(.*)")
@func.new_command(r"/перевести(.*)")
@func.new_command(r"перевести(.*)")
async def swap_money(event: Message):
    args = event.pattern_match.group(1).strip().split()
    if not args:
        return await event.reply(
            phrase.money.no_count + phrase.money.swap_balance_use
        )

    if args[0].lower() in {"все", "всё", "all", "весь"}:
        count = await db.get_money(event.sender_id)
    else:
        try:
            count = int(args[0])
        except ValueError:
            return await event.reply(
                phrase.money.nan_count + phrase.money.swap_balance_use
            )

    if count <= 0:
        return await event.reply(phrase.money.negative_count)

    sender_balance = await db.get_money(event.sender_id)

    if sender_balance < count:
        return await event.reply(
            phrase.money.not_enough.format(
                formatter.value_to_str(sender_balance, phrase.currency)
            )
        )

    user = await func.swap_resolve_recipient(event, args)
    if user is None:
        return await event.reply(
            phrase.money.no_people + phrase.money.swap_balance_use
        )

    if event.sender_id == user:
        return await event.reply(phrase.money.selfbyself)

    try:
        entity = await client.get_entity(user)
        if entity.bot:
            return await event.reply(phrase.money.bot)
    except Exception:
        return await event.reply(
            phrase.money.no_people + phrase.money.swap_balance_use
        )

    db.add_money(event.sender_id, -count)
    db.add_money(user, count)
    return await event.reply(
        phrase.money.swap_money.format(
            formatter.value_to_str(count, phrase.currency)
        )
    )


@func.new_command(r"/вывести (.+)")
@func.new_command(r"/вывод (.+)")
@func.new_command(r"/вмайн (.+)")
@func.new_command(r"/в майн (.+)")
@func.new_command(r"/вмаин (.+)")
@func.new_command(r"/в маин (.+)")
@func.new_command(r"вывести (.+)")
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
    if amount > config.cfg.WithdrawDailyLimit:
        return await event.reply(phrase.bank.daily_limit)
    if not db.check_withdraw_limit(event.sender_id, amount):
        limit = db.check_withdraw_limit(event.sender_id, 0)
        return await event.reply(
            phrase.bank.limit.format(
                formatter.value_to_str(limit, phrase.currency)
            )
        )
    balance = await db.get_money(event.sender_id)
    if balance < amount:
        return await event.reply(
            phrase.money.not_enough.format(
                formatter.value_to_str(balance, phrase.currency)
            )
        )
    db.add_money(event.sender_id, -amount)
    try:
        async with mcrcon.Vanilla as rcon:
            await rcon.send(f"invgive {nick} amethyst_shard {amount}")
    except Exception:
        db.add_money(event.sender_id, amount)
        db.check_withdraw_limit(event.sender_id, -amount)
        return await event.reply(phrase.bank.error)
    return await event.reply(
        phrase.bank.withdraw.format(
            formatter.value_to_str(amount, phrase.currency)
        )
    )


@func.new_command(r"/вывести$")
@func.new_command(r"/вывод$")
@func.new_command(r"/вмайн$")
@func.new_command(r"/в майн$")
@func.new_command(r"/вмаин$")
@func.new_command(r"/в маин$")
@func.new_command(r"вывести$")
async def money_to_server_empty(event: Message):
    return await event.reply(phrase.money.no_count)


@func.new_command(r"/аметисты$")
@func.new_command(r"/баланс$")
@func.new_command(r"баланс$")
@func.new_command(r"/wallet")
@func.new_command(r"wallet$")
@func.new_command(r"/мой баланс$")
@func.new_command(r"мой баланс$")
async def get_balance(event: Message):
    balance = await db.get_money(event.sender_id)
    return await event.reply(
        phrase.money.wallet.format(
            formatter.value_to_str(balance, phrase.currency)
        )
    )


@func.new_command(r"/linknick (\S+)\s*(\S*)$")
@func.new_command(r"/привязать (\S+)\s*(\S*)$")
@func.new_command(r"привязать (\S+)\s*(\S*)$")
@func.new_command(r"/новый ник (\S+)\s*(\S*)$")
@func.new_command(r"/линкник (\S+)\s*(\S*)$")
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
            config.cfg.PriceForChangeNick, phrase.currency
        )
        return await event.reply(
            phrase.nick.already_have.format(price=price), buttons=keyboard
        )
    try:
        async with mcrcon.Vanilla as rcon:
            await rcon.send(f"nwl add name {nick}")
    except Exception:
        logger.error("Внутренняя ошибка при добавлении в белый список")
        return await event.reply(phrase.nick.error)
    reftext = ""
    if refcode:
        author = await db.RefCodes().check_ref(refcode)
        if author is None:
            return await event.reply(phrase.ref.invalid)
        await db.RefCodes().add_uses(author, event.sender_id)
        db.add_money(author, config.cfg.RefGift)
        db.add_money(event.sender_id, config.cfg.RefGift)
        reftext = phrase.ref.gift.format(config.cfg.RefGift)
    db.add_money(event.sender_id, config.cfg.LinkGift)
    db.nicks(nick, event.sender_id).link()
    await event.reply(
        phrase.nick.success.format(
            formatter.value_to_str(config.cfg.LinkGift, phrase.currency)
        )
    )
    if reftext:
        try:
            await event.reply(reftext)
            await client.send_message(
                int(author),
                phrase.ref.used.format(
                    user=await func.get_name(event.sender_id, minecraft=True),
                    amount=config.cfg.RefGift,
                ),
            )
        except Exception:
            logger.info(
                f"Ref {author} is active, but private is closed. Skipping mention."
            )


@func.new_command(r"/linknick$")
@func.new_command(r"/привязать$")
@func.new_command(r"привязать$")
@func.new_command(r"/новый ник$")
@func.new_command(r"/линкник$")
async def link_nick_empty(event: Message):
    if event.chat_id != config.chats.chat:
        return await event.reply(phrase.nick.chat)
    return await event.reply(phrase.nick.not_select)


@func.new_command(r"/серв$")
@func.new_command(r"/сервер")
@func.new_command(r"/server")
async def sysinfo(event: Message):
    await event.reply(await get_system_info())


@func.new_command(r"/randompic")
@func.new_command(r"/рандомпик$")
@func.new_command(r"/картинка$")
async def randompic(event: Message):
    logger.info(f"Запрошена случайная картинка (id {event.sender_id})")
    request = floodwait.WaitPic.request()
    if request is False:
        return await event.reply(phrase.pic.wait)
    await asyncio.sleep(request)
    return await client.send_file(
        entity=event.chat_id,
        file=pic.get_random(),
        reply_to=event.id,
        caption=phrase.pic.get,
    )


@func.new_command(r"/map")
@func.new_command(r"/мап$")
@func.new_command(r"/карта$")
async def getmap(event: Message):
    return await event.reply(
        phrase.get_map.format(await db.database("host")),
        link_preview=False,
    )


@func.new_command(r"/vote@")
@func.new_command(r"/vote$")
@func.new_command(r"/голос$")
@func.new_command(r"/голосование$")
@func.new_command(r"/проголосовать$")
async def vote(event: Message):
    return await client.send_message(
        event.chat_id,
        reply_to=event.id,
        message=phrase.vote,
        link_preview=False,
    )


@func.new_command(r"/нпоиск (.+)")
@func.new_command(r"/пник (.+)")
@func.new_command(r"/игрок (.+)")
@func.new_command(r"/поискпонику (.+)")
@func.new_command(r"игрок (.+)")
@func.new_command(r"нпоиск (.+)")
@func.new_command(r"пник (.+)")
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


@func.new_command(r"/нпоиск$")
@func.new_command(r"/пник$")
@func.new_command(r"/игрок$")
@func.new_command(r"/поискпонику$")
@func.new_command(r"игрок$")
@func.new_command(r"нпоиск$")
@func.new_command(r"пник$")
async def check_info_by_nick_empty(event: Message):
    return await event.reply(phrase.nick.empty)


@func.new_command(r"\+город (.+)")
async def cities_request(event: Message):
    word = event.pattern_match.group(1).strip().lower()
    with open(pathes.chk_city, encoding="utf-8") as f:
        if word in f.read().split("\n"):
            return await event.reply(phrase.cities.exists)
    with open(pathes.bl_city, encoding="utf-8") as f:
        if word in f.read().split("\n"):
            return await event.reply(phrase.cities.in_blacklist)
    entity = await func.get_name(event.sender_id)
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


@func.new_command(r"\+города\s([\s\S]+)")
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
    entity = await func.get_name(event.sender_id)
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


@func.new_command(r"\+города$")
async def cities_requests_empty(event: Message):
    return await event.reply(phrase.cities.empty_long)


@func.new_command(r"\+город$")
async def cities_request_empty(event: Message):
    return await event.reply(phrase.cities.empty)


@func.new_command(r"\-город$")
async def cities_remove_empty(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN, name=phrase.roles.admin
            )
        )
    return await event.reply(phrase.cities.rem_empty)


@func.new_command(r"\-город\s(.+)")
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


@func.new_command(r"/rules")
@func.new_command(r"/правила$")
@func.new_command(r"/правилачата$")
@func.new_command(r"/правила сервера$")
@func.new_command(r"rules")
@func.new_command(r"правила$")
async def rules(event: Message):
    return await event.reply(
        phrase.rules.base.format(await db.database("host")),
        link_preview=False,
    )


@func.new_command(r"онлайн$")
@func.new_command(r"/онлайн$")
@func.new_command(r"online$")
@func.new_command(r"/online")
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


@func.new_command(r"/newhint")
@func.new_command(r"/addhint")
async def add_new_hint(event: Message):
    if not event.is_private:
        return await event.reply(phrase.newhints.private)
    word = await db.get_crocodile_word()
    async with client.conversation(event.sender_id, timeout=300) as conv:
        await conv.send_message(phrase.newhints.ask_hint.format(word=word))

        while True:
            try:
                response = await conv.get_response()
            except TimeoutError:
                return await event.reply(phrase.newhints.timeout)
            text: str = response.raw_text.strip().capitalize()

            if text == "/стоп":
                await conv.send_message(phrase.newhints.cancel)
                return

            if text.startswith("/"):
                continue

            pending_id = await db.add_pending_hint(event.sender_id, text, word)

            await client.send_message(
                config.tokens.bot.creator,
                phrase.newhints.admin_alert.format(
                    word=word,
                    hint=text,
                    user=await func.get_name(event.sender_id),
                ),
                buttons=[
                    [
                        Button.inline("✅", f"hint.accept.{pending_id}"),
                        Button.inline("❌", f"hint.reject.{pending_id}"),
                    ]
                ],
            )
            return await conv.send_message(
                phrase.newhints.sent.format(pending_id)
            )
