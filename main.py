import logging
import asyncio
import re
import aiohttp
import aiohttp.web

from time import time
from hashlib import sha1
from requests import codes
from os import listdir, path, remove
from datetime import timedelta
from random import choice, randint
from rich.logging import RichHandler
from datetime import datetime

from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback
)
from telethon import events
from telethon.sync import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import UserAdminInvalidError

from modules import phrases as phrase
from modules.db import (
    add_money,
    add_nick_minecraft,
    get_money,
    get_shop,
    give_id_by_nick_minecraft,
    give_nick_by_id_minecraft,
    give_stat,
    settings,
    add_stat,
    get_active,
    update_shop,
    set_warn,
    get_warns
)
from modules.morphy import decline_number
from modules.system_info import get_system_info
from modules.mcrcon import MinecraftClient

logging.basicConfig(
    level=logging.INFO,
    format="[%(funcName)s] : %(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(rich_tracebacks=True)
    ]
)
logger = logging.getLogger(__name__)


def remove_section_marks(text):
    'Удаляет из текста все вхождения "§n", где n - цифра или буква.'
    pattern = r"§[a-zA-Z0-9]"
    return re.sub(pattern, "", text)


def get_last_update():
    last = settings('shop_update_time')
    if last is not None:
        last = last.replace(
            ':', '-'
        ).replace(
            '.', '-'
        ).replace(
            ' ', '-'
        ).split('-')
    try:
        return datetime(
            int(last[0]),
            int(last[1]),
            int(last[2]),
            int(last[3]),
            int(last[4]),
            int(last[5]),
            int(last[6]),
        )
    except:
        settings('shop_update_time', str(datetime.now()))
        return get_last_update()


async def time_to_update_shop():
    while True:
        today = datetime.now()
        last = get_last_update()
        seconds = (
            timedelta(hours=3) - (today - last)
        ).total_seconds()
        'Если время прошло'
        if today - last > timedelta(hours=3):
            update_shop()
            settings('shop_version', settings('shop_version') + 1)
            settings(
                'shop_update_time', str(today).split(':')[0]+':00:00.000000'
            )
        await asyncio.sleep(abs(seconds))


async def async_ai_response(message):
    "Запрос к Google Gemini"
    logger.info(
        f"Выполняю запрос к AI: {message}"
    ) if len(message) < 100 else logger.info(
        f"Выполняю запрос к AI: {message[:100]}..."
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'https://'
            'trassert.pythonanywhere.com'
            f'/gemini?q={message}&token={settings("token_google")}'
        ) as main_server:
            if main_server.status == codes.ok:
                return await main_server.text()
        async with session.get(
            'https://'
            'trassert0reserve.pythonanywhere.com'
            f'/gemini?q={message}&token={settings("token_google")}'
        ) as reserve_server:
            if reserve_server.status == codes.ok:
                return await reserve_server.text()
    return None


async def bot():
    global bot_client
    bot_client = TelegramClient(
        session="bot",
        api_id=settings("api_id"),
        api_hash=settings("api_hash"),
        device_model="Bot",
        system_version="4.16.30-vxCUSTOM",
        use_ipv6=True
    )

    async def stat(event):
        entity = await bot_client.get_entity(event.sender_id)
        if event.text.startswith('🗣'):
            if event.sender_id in settings('api_bot_id', log=False):
                id = give_id_by_nick_minecraft(
                    event.text.split(
                        '›'
                    )[0].split(
                        '‹'
                    )[1]
                )
                if id is not None:
                    add_stat(id)
        try:
            if not entity.bot:
                add_stat(event.sender_id)
        except AttributeError:
            pass

    async def push_unactive(event):
        participants = await bot_client.get_participants(
            settings('default_chat')
        )
        list_ids = [user.id for user in participants]
        list_db = []
        for filename in listdir(path.join('db', 'user_stats')):
            if filename.endswith('.json'):
                list_db.append(int(filename.replace('.json', '')))
        list_names = []
        for id in list_ids:
            if id not in list_db:
                user = await bot_client.get_entity(id)
                if not user.bot:
                    if user.username:
                        list_names.append(
                            f'@{user.username}'
                        )
                    else:
                        list_names.append(
                            f'[{user.first_name}](tg://user?id={id})'
                        )
        return await event.reply(
            phrase.unactive+' '.join(list_names)
        )

    async def stat_check(event):
        try:
            days = int(
                event.text.replace(
                    '/моя стата', ''
                ).replace(
                    '/mystat', ''
                ).replace(
                    '/мстат', ''
                ).replace(
                    'сколько я написал', ''
                )
            )
        except ValueError:
            days = 1
        return await event.reply(
            phrase.stat.format(
                messages=give_stat(event.sender_id, days),
                time=days
            )
        )

    async def active_check(event):
        try:
            days = int(
                event.text.replace(
                    '/актив', ''
                ).replace(
                    '/топ актив', ''
                ).replace(
                    '/топ соо', ''
                ).replace(
                    '/top active', ''
                )
            )
        except ValueError:
            days = 1
        text = phrase.active.format(days)
        n = 1
        for data in get_active(days):
            try:
                if data[1] != 1:
                    entity = await bot_client.get_entity(int(data[0]))
                    name = entity.first_name
                    if entity.last_name is not None:
                        name += f' {entity.last_name}'
                    text += f'{n}. {name}: {data[1]}\n'
                    n += 1
            except ValueError as e:
                logger.error(e)
                remove(path.join('db', 'user_stats', f'{data[0]}.json'))
        return await event.reply(text)

    async def link_nick(event):
        nick = event.text.split(' ', maxsplit=1)[1].strip()
        if len(nick) < 4:
            return await event.reply(phrase.nick.too_short)
        if len(nick) > 16:
            return await event.reply(phrase.nick.too_big)
        if not re.match("^[A-Za-z0-9_]*$", nick):
            return await event.reply(phrase.nick.invalid)

        if give_id_by_nick_minecraft(nick) is not None:
            return await event.reply(phrase.nick.taken)
        if give_nick_by_id_minecraft(event.sender_id) is not None:
            return await event.reply(phrase.nick.already_have)

        add_money(event.sender_id, settings('link_gift'))
        add_nick_minecraft(nick, event.sender_id)
        return await event.reply(
            phrase.nick.success.format(
                decline_number(settings('link_gift'), 'изумруд')
            )
        )

    async def shop(event):
        version = settings('shop_version')
        keyboard = ReplyInlineMarkup(
            [
                KeyboardButtonRow(
                    [
                        KeyboardButtonCallback(
                            text="1️⃣", data=f"shop.0.{version}".encode()
                        ),
                        KeyboardButtonCallback(
                            text="2️⃣", data=f"shop.1.{version}".encode()
                        ),
                        KeyboardButtonCallback(
                            text="3️⃣", data=f"shop.2.{version}".encode()
                        ),
                        KeyboardButtonCallback(
                            text="4️⃣", data=f"shop.3.{version}".encode()
                        ),
                        KeyboardButtonCallback(
                            text="5️⃣", data=f"shop.4.{version}".encode()
                        ),
                    ]
                )
            ]
        )
        shop = get_shop()
        theme = shop['theme']
        del shop['theme']
        items = list(shop.keys())
        return await event.reply(
            phrase.shop.shop.format(
                trade_1=items[0],
                value_1=f' ({shop[items[0]]['value']})' if
                shop[items[0]]['value'] != 1 else '',
                price_1=decline_number(shop[items[0]]['price'], 'изумруд'),

                trade_2=items[1],
                value_2=f' ({shop[items[1]]['value']})' if
                shop[items[1]]['value'] != 1 else '',
                price_2=decline_number(shop[items[1]]['price'], 'изумруд'),

                trade_3=items[2],
                value_3=f' ({shop[items[2]]['value']})' if
                shop[items[2]]['value'] != 1 else '',
                price_3=decline_number(shop[items[2]]['price'], 'изумруд'),

                trade_4=items[3],
                value_4=f' ({shop[items[3]]['value']})' if
                shop[items[3]]['value'] != 1 else '',
                price_4=decline_number(shop[items[3]]['price'], 'изумруд'),

                trade_5=items[4],
                value_5=f' ({shop[items[4]]['value']})' if
                shop[items[4]]['value'] != 1 else '',
                price_5=decline_number(shop[items[4]]['price'], 'изумруд'),

                quote=choice(phrase.shop_quotes[theme]['quotes']),
                emo=phrase.shop_quotes[theme]['emo']
            ),
            buttons=keyboard,
            parse_mode="html"
        )

    async def callback_handler(event):
        data = event.data
        logger.info(f'{event.sender_id} отправил КБ - {data}')
        if data == b"crocodile.start":
            if settings('crocodile_super_game') == 1:
                return await event.answer(
                    phrase.crocodile.super_game_here, alert=True
                )
            if settings("current_game") != 0:
                return await event.answer(phrase.crocodile.no, alert=True)
            with open("db\\crocodile_words.txt", 'r', encoding='utf8') as f:
                word = choice(f.read().split('\n'))
            unsec = ""
            for x in list(word):
                if x.isalpha():
                    unsec += "_"
                elif x == " ":
                    unsec += x
            settings(
                "current_game",
                {"hints": [], "word": word, "unsec": unsec}
            )
            bot_client.add_event_handler(
                crocodile_hint,
                events.NewMessage(incoming=True, pattern="/подсказка")
            )
            bot_client.add_event_handler(
                crocodile_handler,
                events.NewMessage(incoming=True, chats=event.chat_id)
            )
            return await event.reply(phrase.crocodile.up)
        elif data == b"crocodile.stop":
            if settings('crocodile_super_game') == 1:
                return await event.answer(
                    phrase.crocodile.super_game_here, alert=True
                )
            if settings("current_game") == 0:
                return await event.answer(
                    phrase.crocodile.already_down, alert=True
                )
            word = settings("current_game")["word"]
            settings("current_game", 0)
            settings('crocodile_last_hint', 0)
            bot_client.remove_event_handler(crocodile_hint)
            bot_client.remove_event_handler(crocodile_handler)
            return await event.reply(phrase.crocodile.down.format(word))
        elif data.decode('utf-8').startswith('shop'):
            args = data.decode('utf-8').split('.')
            if int(args[-1]) != settings("shop_version"):
                return await event.answer(phrase.shop.old, alert=True)
            nick = give_nick_by_id_minecraft(event.sender_id)
            if nick is None:
                return await event.answer(phrase.nick.not_append, alert=True)
            shop = get_shop()
            del shop['theme']
            balance = get_money(event.sender_id)
            items = list(shop.keys())
            item = shop[items[int(args[1])]]
            if balance < item['price']:
                return await event.answer(
                    phrase.money.not_enough.format(
                        decline_number(balance, 'изумруд')
                    ),
                    alert=True
                )
            try:
                async with MinecraftClient(
                    host=settings('ipv4'),
                    port=settings('rcon_port_purpur'),
                    password=settings('rcon_password_purpur')
                ) as rcon:
                    command = f'invgive {nick} {item["name"]} {item["value"]}'
                    logger.info(f'Выполняется команда: {command}')
                    await rcon.send(command)
            except TimeoutError:
                return await event.answer(phrase.shop.timeout, alert=True)
            add_money(event.sender_id, -item['price'])
            return await event.answer(
                phrase.shop.buy.format(
                    items[int(args[1])]
                ),
                alert=True
            )

    async def host(event):
        await event.reply(phrase.server.host.format(settings("host")))

    async def sysinfo(event):
        await event.reply(get_system_info())

    async def help(event):
        await event.reply(phrase.help.mods, link_preview=True)
        await asyncio.sleep(1)
        await event.reply(phrase.help.comm, link_preview=True)

    async def ping(event):
        timestamp = event.date.timestamp()
        ping = round(time() - timestamp, 2)
        if ping < 0:
            ping = phrase.ping.min
        else:
            ping = f"за {str(ping)} сек."
        await event.reply(phrase.ping.set.format(ping))

    async def crocodile_hint(event):
        hint = settings("current_game")["hints"]
        if event.sender_id in hint:
            return await event.reply(phrase.crocodile.hints_all)
        word = settings("current_game")["word"]
        last_hint = settings("crocodile_last_hint")
        if last_hint != 0:
            check_last = f'Так же учитывай, что подсказка {last_hint} уже была.'
        else:
            check_last = ''
        response = await async_ai_response(
            f'Сделай подсказку для слова "{word}". '
            'Ни в коем случае не добавляй никаких "подсказка для слова.." '
            'и т.п, ответ должен содержать только подсказку. '
            'Не забудь, что подсказка не должна '
            'содержать слово в любом случае. ' + check_last
        )
        if response is None:
            return await event.reply(phrase.crocodile.error)
        settings("crocodile_last_hint", response)
        await event.reply(response)
        hint.append(event.sender_id)
        db = settings("current_game")
        db["hints"] = hint
        settings("current_game", db)

    async def crocodile_handler(event):
        text = event.text.strip().lower()
        current_word = settings("current_game")["word"]
        current_mask = list(settings("current_game")["unsec"])
        if text == current_word:
            bets = settings('crocodile_bets')
            all = 0
            bets_str = ''
            if bets != {}:
                for key in list(bets.keys()):
                    if str(event.sender_id) == key:
                        all += round(bets[key]*settings('crocodile_bet_coo'))
                    else:
                        all += bets[key]
                add_money(event.sender_id, all)
                bets_str = phrase.crocodile.bet_win.format(
                    decline_number(all, 'изумруд'),
                )
            settings("current_game", 0)
            settings("crocodile_bets", {})
            settings("crocodile_last_hint", 0)
            if settings('crocodile_super_game') == 1:
                settings('crocodile_super_game', 0)
                settings('max_bet', settings('default_max_bet'))
                settings('min_bet', settings('default_min_bet'))
            bot_client.remove_event_handler(crocodile_hint)
            bot_client.remove_event_handler(crocodile_handler)
            return await event.reply(
                phrase.crocodile.win.format(current_word)+bets_str
            )
        else:
            pass
        if text[0] != '/':
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
                current_mask[randint(0, len(current_mask)-1)] = '_'
                cgame = settings("current_game")
                cgame["unsec"] = "".join(current_mask)
                settings("current_game", cgame)
                return await event.reply(
                    phrase.crocodile.new.format(
                        "".join(current_mask).replace("_", "..")
                    )
                )
            if list(settings("current_game")["unsec"]) != current_mask:
                cgame = settings("current_game")
                cgame["unsec"] = "".join(current_mask)
                settings("current_game", cgame)
                return await event.reply(
                    phrase.crocodile.new.format(
                        "".join(current_mask).replace("_", "..")
                    )
                )

    async def crocodile(event):
        if not event.chat_id == settings("default_chat"):
            return await event.reply(phrase.default_chat)
        else:
            pass
        if settings("current_game") == 0:
            keyboard = ReplyInlineMarkup(
                [
                    KeyboardButtonRow(
                        [
                            KeyboardButtonCallback(
                                text="✅ Играть", data=b"crocodile.start"
                            ),
                            KeyboardButtonCallback(
                                text="❌ Остановить игру", data=b"crocodile.stop"
                            )
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

    async def crocodile_bet(event):
        try:
            bet = int(
                event.text.split(" ", maxsplit=1)[1]
            )
            if bet < settings('min_bet'):
                return await event.reply(
                    phrase.money.min_count.format(
                        decline_number(settings('min_bet'), 'изумруд')
                    )
                )
            elif bet > settings('max_bet'):
                return await event.reply(
                    phrase.money.max_count.format(
                        decline_number(settings('max_bet'), 'изумруд')
                    )
                )
        except IndexError:
            bet = settings('min_bet')
        except ValueError:
            return await event.reply(
                phrase.money.nan_count
            )
        sender_balance = get_money(event.sender_id)
        if sender_balance < bet:
            return await event.reply(
                phrase.money.not_enough.format(
                    decline_number(sender_balance, 'изумруд')
                )
            )
        if settings("current_game") != 0:
            return await event.reply(
                phrase.crocodile.no
            )
        all_bets = settings('crocodile_bets')
        if str(event.sender_id) in all_bets:
            return await event.reply(
                phrase.crocodile.bet_already
            )
        add_money(event.sender_id, -bet)
        all_bets[str(event.sender_id)] = bet
        settings('crocodile_bets', all_bets)
        return await event.reply(
            phrase.crocodile.bet.format(
                decline_number(bet, 'изумруд')
            )
        )

    async def super_game(event):
        if event.sender_id not in settings('admins_id'):
            return await event.reply(phrase.no_perm)
        arg = event.text.lower().split(" ", maxsplit=1)[1]
        bets = settings('crocodile_bets')
        bets[str(settings('creator'))] = 50
        settings('crocodile_bets', bets)
        settings('crocodile_super_game', 1)
        settings('max_bet', 100)
        settings('min_bet', 50)
        await bot_client.send_message(
            settings('default_chat'), phrase.crocodile.super_game_wait
        )
        await asyncio.sleep(60)
        settings(
            'current_game',
            {
                'hints': [],
                'unsec': '_'*len(arg),
                'word': arg
            }
        )
        bot_client.add_event_handler(
            crocodile_hint,
            events.NewMessage(incoming=True, pattern="/подсказка")
        )
        bot_client.add_event_handler(
            crocodile_handler,
            events.NewMessage(incoming=True, chats=settings('default_chat'))
        )
        return await bot_client.send_message(
            settings('default_chat'), phrase.crocodile.super_game
        )

    async def gemini(event):
        try:
            arg = event.text.split(" ", maxsplit=1)[1]
        except IndexError:
            return await event.reply(phrase.no_response)
        response = await async_ai_response(arg)
        if response is None:
            return await event.reply(phrase.server.overload)
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await event.reply(response[x:x+4096])
        else:
            return await event.reply(response)

    async def mcrcon(event):
        if event.text[0] == 'f':
            host = settings('ipv4')
            port = settings('rcon_port_fabric')
            password = settings('rcon_password_fabric')
        elif event.text[0] == 'p':
            host = settings('ipv4')
            port = settings('rcon_port_purpur')
            password = settings('rcon_password_purpur')
        else:
            return await event.reply(phrase.no_server)

        if event.sender_id not in settings('admins_id'):
            return await event.reply(phrase.no_perm)
        command = event.text[2:]
        logger.info(f'Выполняется команда: {command}')
        try:
            async with MinecraftClient(
                host=host,
                port=port,
                password=password
            ) as rcon:
                resp = remove_section_marks(await rcon.send(command))
                logger.info(f'Ответ команды:\n{resp}')
                if len(resp) > 4096:
                    for x in range(0, len(resp), 4096):
                        await event.reply(f'```{resp[x:x+4096]}```')
                else:
                    return await event.reply(f'```{resp}```')
        except TimeoutError:
            return await event.reply(phrase.server.stopped)

    async def add_admins(event):
        if event.sender_id != settings('creator'):
            return await event.reply(phrase.no_perm)
        tag = event.text.split(" ", maxsplit=1)[1]
        user = await bot_client(
            GetFullUserRequest(tag)
        )
        admins = settings('admins_id')
        admins.append(user.full_user.id)
        settings('admins_id', admins)
        return await event.reply(
            phrase.new_admin.format(nick=tag, id=user.full_user.id)
        )

    async def del_admins(event):
        if event.sender_id != settings('creator'):
            return await event.reply(phrase.no_perm)
        tag = event.text.split(" ", maxsplit=1)[1]
        user = await bot_client(
            GetFullUserRequest(tag)
        )
        admins = settings('admins_id')
        admins.remove(user.full_user.id)
        settings('admins_id', admins)
        return await event.reply(phrase.del_admin)

    async def mute_user(event):
        if event.sender_id not in settings('admins_id'):
            return await event.reply(phrase.no_perm)
        args = event.text.split(" ", maxsplit=3)[1:]
        if args[0] in ['помощь', 'help']:
            return await event.reply(phrase.mute_help)
        user_link = args[0]
        if len(args) > 2:
            reason = ' '.join(args[2:])
        else:
            reason = 'Нет'
        if '.' in args[1]:
            stamp = args[1].split(".")
            if len(stamp) == 3:
                until_date = timedelta(
                    minutes=int(stamp[0]),
                    hours=int(stamp[1]),
                    days=int(stamp[2])
                )
            elif len(stamp) == 2:
                until_date = timedelta(
                    minutes=int(stamp[0]),
                    hours=int(stamp[1]),
                )
            else:
                return await event.reply(phrase.mute_time_error)
        else:
            until_date = timedelta(minutes=int(args[1]))
        user = await bot_client.get_entity(user_link)
        try:
            await bot_client.edit_permissions(
                entity=event.chat_id,
                user=user.id,
                send_messages=False,
                send_media=False,
                send_stickers=False,
                send_gifs=False,
                send_games=False,
                send_inline=False,
                send_polls=False,
                until_date=until_date
            )
            return await event.reply(
                phrase.muted.format(
                    user=user.first_name,
                    time=str(until_date).replace(':00', '').replace('day', 'дней'),
                    reason=reason
                ),
            )
        except UserAdminInvalidError:
            return await event.reply(phrase.is_admin)

    async def server_top_list(event):
        try:
            async with MinecraftClient(
                host=settings('ipv4'),
                port=settings('rcon_port_purpur'),
                password=settings('rcon_password_purpur')
            ) as rcon:
                await event.reply(
                    remove_section_marks(
                        await rcon.send('playtime top')
                    ).replace(
                        '[Лидеры по времени на сервере]',
                        phrase.stat_server.format("ванильного")
                    ).replace(
                        '****************************************',
                        ''
                    )
                )
        except TimeoutError:
            return await event.reply(phrase.server.stopped)

    async def get_balance(event):
        return await event.reply(
            phrase.money.wallet.format(
                decline_number(
                    get_money(event.sender_id), 'изумруд'
                )
            )
        )

    async def add_balance(event):
        if event.sender_id not in settings('admins_id'):
            return await event.reply(phrase.no_perm)
        args = event.text.split(" ", maxsplit=3)
        try:
            tag = args[2]
            user = await bot_client(
                GetFullUserRequest(tag)
            )
        except IndexError:
            return await event.reply(
                phrase.money.no_people+phrase.money.change_balance_use
            )
        except ValueError:
            return await event.reply(
                phrase.money.no_such_people+phrase.money.change_balance_use
            )
        try:
            new = int(args[3])
        except IndexError:
            return await event.reply(
                phrase.money.no_count+phrase.money.change_balance_use
            )
        except ValueError:
            return await event.reply(
                phrase.money.nan_count+phrase.money.change_balance_use
            )
        old = get_money(user.full_user.id)
        add_money(user.full_user.id, new)
        await event.reply(
            phrase.money.add_money.format(
                name=tag,
                old=old,
                new=old+new
            )
        )

    async def swap_money(event):
        args = event.text.split(" ", maxsplit=2)
        try:
            tag = args[1]
            user = await bot_client(
                GetFullUserRequest(tag)
            )
        except IndexError:
            return await event.reply(
                phrase.money.no_people+phrase.money.swap_balance_use
            )
        except TypeError or ValueError:
            return await event.reply(
                phrase.money.no_such_people+phrase.money.swap_balance_use
            )
        try:
            count = int(args[2])
            if count <= 0:
                return await event.reply(
                    phrase.money.negative_count
                )
        except IndexError:
            return await event.reply(
                phrase.money.no_count+phrase.money.swap_balance_use
            )
        except ValueError:
            return await event.reply(
                phrase.money.nan_count+phrase.money.swap_balance_use
            )
        sender_balance = get_money(event.sender_id)
        if sender_balance < count:
            return await event.reply(
                phrase.money.not_enough.format(
                    decline_number(sender_balance, 'изумруд')
                )
            )
        add_money(event.sender_id, -count)
        add_money(user.full_user.id, count)
        return await event.reply(
            phrase.money.swap_money.format(
                decline_number(count, 'изумруд')
            )
        )

    async def tg_dns(event):
        if event.sender_id not in settings('admins_id'):
            return await event.reply(phrase.no_perm)
        return await event.reply(
            phrase.dns.format(await setup_ip(check_set=False)),
            parse_mode="html"
        )

    async def warn(event):
        if event.sender_id not in settings('admins_id'):
            return await event.reply(phrase.no_perm)
        reply_to_msg = event.reply_to_msg_id
        if reply_to_msg:
            reply_message = await event.get_reply_message()
            print(reply_message.sender_id)
        warns = set_warn(reply_message.sender_id)
        if warns == settings('max_warns'):
            return await event.reply(phrase.max_warns)

    await bot_client.start(bot_token=settings("token_bot"))

    'Варн'
    bot_client.add_event_handler(
        warn, events.NewMessage(incoming=True, pattern="/варн")
    )

    'Добавление статистики'
    bot_client.add_event_handler(
        stat, events.NewMessage(chats=settings("default_chat"))
    )

    'ДНС'
    bot_client.add_event_handler(
        tg_dns, events.NewMessage(incoming=True, pattern="/днс")
    )
    bot_client.add_event_handler(
        tg_dns, events.NewMessage(incoming=True, pattern="/dns")
    )

    'Супер-игра'
    bot_client.add_event_handler(
        super_game, events.NewMessage(incoming=True, pattern="/суперигра")
    )

    'Пуш неактивных'
    bot_client.add_event_handler(
        push_unactive, events.NewMessage(incoming=True, pattern="/пуш неактив")
    )
    bot_client.add_event_handler(
        push_unactive, events.NewMessage(incoming=True, pattern="/unactive")
    )

    'Линк ника к майнкрафту'
    bot_client.add_event_handler(
        link_nick, events.NewMessage(incoming=True, pattern="/linknick")
    )
    bot_client.add_event_handler(
        link_nick, events.NewMessage(incoming=True, pattern="/привязать")
    )
    bot_client.add_event_handler(
        link_nick, events.NewMessage(incoming=True, pattern="/connect")
    )

    'Магазин'
    bot_client.add_event_handler(
        shop, events.NewMessage(incoming=True, pattern="/shop")
    )
    bot_client.add_event_handler(
        shop, events.NewMessage(incoming=True, pattern="/магазин")
    )

    'Кошелек'
    bot_client.add_event_handler(
        get_balance,
        events.NewMessage(incoming=True, pattern="/баланс")
    )
    bot_client.add_event_handler(
        get_balance,
        events.NewMessage(incoming=True, pattern="/мой баланс")
    )
    bot_client.add_event_handler(
        get_balance,
        events.NewMessage(incoming=True, pattern="/wallet")
    )

    'Добавить монет'
    bot_client.add_event_handler(
        add_balance,
        events.NewMessage(incoming=True, pattern="/изменить баланс")
    )
    bot_client.add_event_handler(
        add_balance,
        events.NewMessage(incoming=True, pattern="/change balance")
    )

    'Переслать монет'
    bot_client.add_event_handler(
        swap_money,
        events.NewMessage(incoming=True, pattern="/скинуть")
    )
    bot_client.add_event_handler(
        swap_money,
        events.NewMessage(incoming=True, pattern="/переслать")
    )
    bot_client.add_event_handler(
        swap_money,
        events.NewMessage(incoming=True, pattern="/кинуть")
    )
    bot_client.add_event_handler(
        swap_money,
        events.NewMessage(incoming=True, pattern="/дать")
    )

    'Моя стата'
    bot_client.add_event_handler(
        stat_check,
        events.NewMessage(incoming=True, pattern="/моя стата")
    )
    bot_client.add_event_handler(
        stat_check,
        events.NewMessage(incoming=True, pattern="/mystat")
    )
    bot_client.add_event_handler(
        stat_check,
        events.NewMessage(incoming=True, pattern="/мстат")
    )
    bot_client.add_event_handler(
        stat_check,
        events.NewMessage(incoming=True, pattern="сколько я написал")
    )

    'Стата беседы'
    bot_client.add_event_handler(
        active_check, events.NewMessage(incoming=True, pattern="/актив")
    )
    bot_client.add_event_handler(
        active_check, events.NewMessage(incoming=True, pattern="/топ актив")
    )
    bot_client.add_event_handler(
        active_check, events.NewMessage(incoming=True, pattern="/топ соо")
    )
    bot_client.add_event_handler(
        active_check, events.NewMessage(incoming=True, pattern="/top active")
    )

    'Топ игроков'
    bot_client.add_event_handler(
        server_top_list,
        events.NewMessage(incoming=True, pattern="/топ игроков")
    )
    bot_client.add_event_handler(
        server_top_list,
        events.NewMessage(incoming=True, pattern="/top players")
    )
    bot_client.add_event_handler(
        server_top_list,
        events.NewMessage(incoming=True, pattern="/bestplayers")
    )

    'Сервер'
    bot_client.add_event_handler(
        sysinfo, events.NewMessage(incoming=True, pattern="/серв")
    )
    bot_client.add_event_handler(
        sysinfo, events.NewMessage(incoming=True, pattern="/сервер")
    )
    bot_client.add_event_handler(
        sysinfo, events.NewMessage(incoming=True, pattern="/server")
    )

    'Айпи'
    bot_client.add_event_handler(
        host, events.NewMessage(incoming=True, pattern="/хост")
    )
    bot_client.add_event_handler(
        host, events.NewMessage(incoming=True, pattern="/host")
    )

    'Помощь'
    bot_client.add_event_handler(
        help, events.NewMessage(incoming=True, pattern="/помощь")
    )
    bot_client.add_event_handler(
        help, events.NewMessage(incoming=True, pattern="/help")
    )

    'Пинг'
    bot_client.add_event_handler(
        ping, events.NewMessage(incoming=True, pattern="/пинг")
    )
    bot_client.add_event_handler(
        ping, events.NewMessage(incoming=True, pattern="/ping")
    )

    'ИИ'
    bot_client.add_event_handler(
        gemini, events.NewMessage(incoming=True, pattern="/ии")
    )
    bot_client.add_event_handler(
        gemini, events.NewMessage(incoming=True, pattern="ии")
    )
    bot_client.add_event_handler(
        gemini, events.NewMessage(incoming=True, pattern="/ai")
    )

    'Мут'
    bot_client.add_event_handler(
        mute_user, events.NewMessage(incoming=True, pattern="/мут")
    )
    bot_client.add_event_handler(
        mute_user, events.NewMessage(incoming=True, pattern="/mute")
    )

    'RCON'
    bot_client.add_event_handler(
        mcrcon, events.NewMessage(incoming=True, pattern=r"f/|p/")
    )

    'Админы'
    bot_client.add_event_handler(
        add_admins, events.NewMessage(incoming=True, pattern=r"\+админ")
    )
    bot_client.add_event_handler(
        add_admins, events.NewMessage(incoming=True, pattern=r"\+admin")
    )
    bot_client.add_event_handler(
        del_admins, events.NewMessage(incoming=True, pattern=r"\-админ")
    )
    bot_client.add_event_handler(
        del_admins, events.NewMessage(incoming=True, pattern=r"\-admin")
    )

    'Крокодил'
    bot_client.add_event_handler(
        crocodile, events.NewMessage(incoming=True, pattern="/крокодил")
    )
    bot_client.add_event_handler(
        crocodile, events.NewMessage(incoming=True, pattern="/crocodile")
    )
    bot_client.add_event_handler(
        crocodile_bet, events.NewMessage(incoming=True, pattern="/ставка")
    )
    bot_client.add_event_handler(callback_handler, events.CallbackQuery())

    if settings("current_game") != 0:
        bot_client.add_event_handler(
            crocodile_handler,
            events.NewMessage(incoming=True, chats=settings("default_chat"))
        )
        bot_client.add_event_handler(
            crocodile_hint,
            events.NewMessage(incoming=True, pattern="/подсказка")
        )

    await bot_client.run_until_disconnected()


# def update_server(host):
#     app = Flask(__name__)

#     @app.route("/download")
#     def download():
#         logger.info("Отдаю файл")
#         q = request.args.get("q")
#         try:
#             client_version = int(request.args.get("version"))
#             logger.info(f'Версия клиента: {client_version}')
#         except:
#             return "versionerror"
#         if q not in ["prog", "mods"]:
#             return "typeerror"
#         logger.info(
#             'Клиенту нужно - {type}'.format(
#                 type='Программа' if q == 'prog' else 'Моды'
#                 )
#             )
#         file = path.join("update", q, str(client_version), "content.zip")
#         logger.info(file)
#         return send_file(file, None, True)

#     @app.route("/get_image")
#     def get_image():
#         image = choice(listdir("images"))
#         return send_file(path.join("images", image), download_name=image)

#     serve(app, host=host, port="5000")


async def setup_ip(check_set=True):
    "NOIP синхронизация"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://v4.ident.me") as v4_ident:
                v4 = await v4_ident.text()
        except:
            v4 = False
        try:
            async with session.get("https://v6.ident.me") as v6_ident:
                v6 = await v6_ident.text()
        except:
            v6 = False
        if not v4 or not v6:
            return logger.error('Ошибка при получении IP.'
                                'Сервер может быть недоступен')
        elif v4 == settings('ipv4') and v6 == settings('ipv6') and check_set:
            return logger.warning("IPv4 и IPv6 не изменились")
        if check_set:
            logger.warning("IPv4 или IPv6 изменились")
        else:
            logger.warning('Принудительно выставляю IP')
        settings('ipv4', v4)
        settings('ipv6', v6)
        async with session.get(
            f'http://{settings("noip_username")}:{settings("noip_password")}'
            '@dynupdate.no-ip.com/'
            f'nic/update?hostname={settings("host")}&myip={v4},{v6}',
            headers={
                "User-Agent": "Trassert MinecraftServer' \
                    '/Windows 11-22000 s3pple@yandex.ru"
            },
        ) as noip:
            logger.info(f"Ответ NOIP: {await noip.text()}")
            return await noip.text()


async def web_server():
    async def hotmc(request):
        data = await request.post()
        nick = data['nick']
        sign = data['sign']
        time = data['time']
        logger.warning(f'{nick} проголосовал в {time} с хешем {sign}')
        hash = sha1(
            f'{nick}{time}{settings("hotmc_key")}'.encode()
        ).hexdigest()
        if sign != hash:
            logger.warning('Хеш не совпал!')
            logger.warning(f'Должен быть: {sign}')
            logger.warning(f'Имеется: {hash}')
            return aiohttp.web.Response(
                text='Переданные данные не прошли проверку.'
            )
        tg_id = give_id_by_nick_minecraft(nick)
        if tg_id is not None:
            add_money(tg_id, 10)
            give = phrase.hotmc_money.format(
                decline_number(10, 'изумруд')
            )
        else:
            give = ''
        await bot_client.send_message(
            settings('default_chat'),
            phrase.hotmc.format(nick=nick, money=give),
            link_preview=False
        )
        return aiohttp.web.Response(text='ok')

    async def version(request):
        q = request.query.get('q')
        try:
            client_version = int(request.args.get("version"))
        except ValueError:
            return aiohttp.web.Response(
                text="versionerror"
            )
        if q not in ["prog", "mods"]:
            return aiohttp.web.Response(
                text="typeerror"
            )
        current = max(list(map(int, listdir(path.join("update", q)))))
        if client_version < current:
            return aiohttp.web.Response(
                text=str(client_version + 1)
            )
        else:
            return aiohttp.web.Response(
                text="True"
            )

    app = aiohttp.web.Application()
    app.add_routes(
        [
            aiohttp.web.post('/hotmc', hotmc),
            aiohttp.web.get('/version', version),
        ]
    )
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    ipv4 = aiohttp.web.TCPSite(runner, '0.0.0.0', 5000)
    ipv6 = aiohttp.web.TCPSite(runner, settings('ipv6'), 5000)
    await ipv4.start()
    await ipv6.start()


async def main():
    while True:
        try:
            await setup_ip()
            await web_server()
            await asyncio.gather(bot(), time_to_update_shop())
        except ConnectionError:
            logger.error('Жду 20 секунд (нет подключения к интернету)')
            await asyncio.sleep(20)
        except KeyboardInterrupt:
            logger.warning('Закрываю бота!')
            break

if __name__ == "__main__":
    # Thread(
    #     target=update_server,
    #     args=(settings("ipv6"),),
    #     daemon=True
    # ).start()
    # Thread(
    #     target=update_server,
    #     args=("0.0.0.0",),
    #     daemon=True
    # ).start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning('Закрываю бота!')
