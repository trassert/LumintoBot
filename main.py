import logging
import asyncio
import re
import aiohttp
import aiohttp.web

from time import time
from hashlib import sha1, md5
from os import listdir, path
from datetime import timedelta
from random import choice, randint, random
from rich.logging import RichHandler
from datetime import datetime
from bestconfig import Config
from traceback import format_exc

from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback
)
from telethon import events
from telethon.sync import TelegramClient
from telethon import errors as TGErrors
from telethon.tl.functions.users import GetFullUserRequest

from modules import phrases as phrase
from modules.db import (
    add_money,
    crocodile_stat,
    get_money,
    get_shop,
    setting,
    update_shop,
    get_all_money,
    nicks
)
from modules.formatter import decline_number
from modules.system_info import get_system_info
from modules.mcrcon import MinecraftClient
from modules.ai import ai_response, ai_servers
from modules.diff import get_enchant_desc

tokens = Config(path.join('configs', 'tokens.yml'))
coofs = Config(path.join('configs', 'coofs.yml'))

file_handler = logging.FileHandler(
    filename=path.join('logs', 'log.log'),
    mode='a',
    encoding='utf-8'
)
logging_fileformat = logging.Formatter(
    '[%(asctime)s] %(levelname)s – '
    '[%(name)s:%(lineno)s] : %(message)s',
    datefmt='%H:%M:%S'
)
file_handler.setFormatter(logging_fileformat)

logging.basicConfig(
    format="[%(funcName)s] : %(message)s",
    datefmt="[%X]",
    level=logging.INFO,
    handlers=[
        file_handler,
        RichHandler(rich_tracebacks=True)
    ]
)
logger = logging.getLogger(__name__)


def remove_section_marks(text):
    'Удаляет из текста все вхождения "§n", где n - цифра или буква.'
    pattern = r"§[a-zA-Z0-9]"
    return re.sub(pattern, "", text)


def get_last_update():
    last = setting('shop_update_time')
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
    except Exception:
        setting('shop_update_time', str(datetime.now()))
        return get_last_update()


async def time_to_update_shop():
    await asyncio.sleep(10)  # ! Для предотвращения блокировки
    while True:
        today = datetime.now()
        last = get_last_update()
        seconds = (
            timedelta(hours=2) - (today - last)
        ).total_seconds()
        'Если время прошло'
        if today - last > timedelta(hours=2):
            theme = update_shop()
            await client.send_message(
                tokens.bot.chat,
                phrase.shop.update.format(
                    theme=phrase.shop_quotes[theme]['translate']
                )
            )
            setting('shop_version', setting('shop_version') + 1)
            setting(
                'shop_update_time', str(today).split(':')[0]+':00:00.000000'
            )
        await asyncio.sleep(abs(seconds))


async def bot():
    global client
    client = TelegramClient(
        session=path.join('db', 'bot'),
        api_id=tokens.bot.id,
        api_hash=tokens.bot.hash,
        device_model="Bot",
        system_version="4.16.30-vxCUSTOM",
        use_ipv6=True
    )

    # Вспомогательные функции

    async def get_name(id):
        'Выдает @пуш, если нет - имя + фамилия'
        user_name = await client.get_entity(int(id))
        if user_name.username is None:
            if user_name.last_name is None:
                user_name = user_name.first_name
            else:
                user_name = user_name.first_name + " " + user_name.last_name
        else:
            user_name = user_name.username
        return user_name

    # Кнопки бота

    @client.on(events.CallbackQuery())
    async def callback_action(event):
        data = event.data.decode('utf-8').split('.')
        logger.info(f'{event.sender_id} отправил КБ - {data}')
        if data[0] == 'crocodile':
            if data[1] == 'start':
                if setting('crocodile_super_game') == 1:
                    return await event.answer(
                        phrase.crocodile.super_game_here, alert=True
                    )
                if setting("current_game") != 0:
                    return await event.answer(phrase.crocodile.no, alert=True)
                with open("db\\crocodile_words.txt", 'r', encoding='utf8') as f:
                    word = choice(f.read().split('\n'))
                unsec = ""
                for x in list(word):
                    if x.isalpha():
                        unsec += "_"
                    elif x == " ":
                        unsec += x
                setting(
                    "current_game",
                    {"hints": [], "word": word, "unsec": unsec}
                )
                client.add_event_handler(
                    crocodile_hint,
                    events.NewMessage(incoming=True, pattern="/подсказка")
                )
                client.add_event_handler(
                    crocodile_handler,
                    events.NewMessage(incoming=True, chats=event.chat_id)
                )
                return await event.reply(phrase.crocodile.up)
            elif data[1] == 'stop':
                entity = await client.get_entity(event.sender_id)
                user = f'@{entity.username}' if entity.username \
                    else entity.first_name + " " + entity.last_name
                if setting("current_game") == 0:
                    return await event.answer(
                        phrase.crocodile.already_down, alert=True
                    )
                if setting('crocodile_super_game') == 1:
                    return await event.answer(
                        phrase.crocodile.super_game_here, alert=True
                    )
                bets_json = setting('crocodile_bets')
                if bets_json != {}:
                    bets = round(sum(list(bets_json.values())) / 2)
                    bets = 1 if bets < 1 else bets
                    sender_balance = get_money(event.sender_id)
                    if sender_balance < bets:
                        return await event.answer(
                            phrase.crocodile.not_enough.format(
                                decline_number(sender_balance, 'изумруд')
                            ),
                            alert=True
                        )
                    add_money(event.sender_id, -bets)
                word = setting("current_game")["word"]
                setting("current_game", 0)
                setting('crocodile_last_hint', 0)
                client.remove_event_handler(crocodile_hint)
                client.remove_event_handler(crocodile_handler)
                if bets_json != {}:
                    return await event.reply(
                        phrase.crocodile.down_payed.format(
                            user=user,
                            money=decline_number(
                                bets,
                                'изумруд'
                            ),
                            word=word
                        )
                    )
                return await event.reply(phrase.crocodile.down.format(word))
        elif data[0] == 'shop':
            if int(data[-1]) != setting("shop_version"):
                return await event.answer(phrase.shop.old, alert=True)
            nick = nicks(id=event.sender_id).get()
            if nick is None:
                return await event.answer(phrase.nick.not_append, alert=True)
            shop = get_shop()
            del shop['theme']
            balance = get_money(event.sender_id)
            items = list(shop.keys())
            item = shop[items[int(data[1])]]
            if balance < item['price']:
                return await event.answer(
                    phrase.money.not_enough.format(
                        decline_number(balance, 'изумруд')
                    ),
                    alert=True
                )
            try:
                async with MinecraftClient(
                    host=setting('ipv4'),
                    port=setting('rcon_port_purpur'),
                    password=tokens.rcon
                ) as rcon:
                    command = f'invgive {nick} {item["name"]} {item["value"]}'
                    logger.info(f'Выполняется команда: {command}')
                    await rcon.send(command)
            except TimeoutError:
                return await event.answer(phrase.shop.timeout, alert=True)
            add_money(event.sender_id, -item['price'])
            return await event.answer(
                phrase.shop.buy.format(
                    items[int(data[1])]
                ),
                alert=True
            )
        elif data[0] == 'word':
            user_name = await get_name(data[3])
            if data[1] == 'yes':
                with open(
                    path.join('db', 'crocodile_words.txt'),
                    'a',
                    encoding='utf-8'
                ) as f:
                    f.write(f'\n{data[2]}')
                add_money(data[3], coofs.WordRequest)
                await client.send_message(
                    tokens.bot.chat,
                    phrase.word.success.format(
                        word=data[2],
                        user=user_name,
                        money=decline_number(
                            coofs.WordRequest, 'изумруд'
                        )
                    )
                )
                return await client.edit_message(
                    event.sender_id,
                    event.message_id,
                    phrase.word.add
                )
            if data[1] == 'no':
                await client.send_message(
                    tokens.bot.chat,
                    phrase.word.no.format(
                        word=data[2],
                        user=user_name
                    )
                )
                return await client.edit_message(
                    event.sender_id,
                    event.message_id,
                    phrase.word.noadd
                )
        elif data[0] == 'nick':
            if event.sender_id != int(data[2]):
                return await event.answer(phrase.not_for_you)
            if nicks(id=event.sender_id).get() == data[1]:
                return await event.answer(phrase.nick.already_you, alert=True)
            balance = get_money(event.sender_id)
            if balance - coofs.PriceForChangeNick < 0:
                return await event.answer(
                    phrase.money.not_enough.format(
                        decline_number(balance, 'изумруд')
                    )
                )
            add_money(event.sender_id, -coofs.PriceForChangeNick)
            nicks(data[1], event.sender_id).link()
            user_name = await get_name(data[2])
            return await event.reply(
                phrase.nick.buy_nick.format(
                    user=user_name,
                    price=decline_number(
                        coofs.PriceForChangeNick, 'изумруд'
                    )
                )
            )

    # Обработчики событий

    @client.on(events.ChatAction(chats=tokens.bot.chat))
    async def chat_action(event):
        if event.user_left:
            # ! Если пидорас ушёл из чата
            user_name = await get_name(event.user_id)
            return await client.send_message(
                tokens.bot.chat,
                phrase.leave_message.format(
                    user_name
                )
            )

    # Статистика

    @client.on(events.NewMessage(chats=tokens.bot.chat))
    async def add_stat(event):
        if event.text.startswith('‹'):
            if event.sender_id in setting('api_bot_id', log=False):
                id = nicks.get(
                    event.text.split(
                        '›'
                    )[0].split(
                        '‹'
                    )[1]
                )
                if id is not None:
                    add_stat(id)
    # Обработчики команд

    async def link_nick(event):
        nick = event.text.split(' ', maxsplit=1)[1].strip()
        if len(nick) < 4:
            return await event.reply(phrase.nick.too_short)
        if len(nick) > 16:
            return await event.reply(phrase.nick.too_big)
        if not re.match("^[A-Za-z0-9_]*$", nick):
            return await event.reply(phrase.nick.invalid)

        if nicks(nick=nick).get() is not None:
            if nicks(id=event.sender_id).get() == nick:
                return await event.reply(phrase.nick.already_you)
            return await event.reply(phrase.nick.taken)
        elif nicks(id=event.sender_id).get() is not None:
            if nicks(id=event.sender_id).get() == nick:
                return await event.reply(phrase.nick.already_you)
            keyboard = ReplyInlineMarkup(
                [
                    KeyboardButtonRow(
                        [
                            KeyboardButtonCallback(
                                text="✅ Сменить",
                                data=f'nick.{nick}.{event.sender_id}'.encode()
                            )
                        ]
                    )
                ]
            )
            return await event.reply(
                phrase.nick.already_have.format(
                    price=decline_number(
                        coofs.PriceForChangeNick, 'изумруд'
                    )
                ),
                buttons=keyboard
            )

        add_money(event.sender_id, coofs.LinkGift)
        nicks(nick, event.sender_id).link()
        return await event.reply(
            phrase.nick.success.format(
                decline_number(coofs.LinkGift, 'изумруд')
            )
        )

    async def shop(event):
        version = setting('shop_version')
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

    async def host(event):
        await event.reply(phrase.server.host.format(setting("host")))

    async def sysinfo(event):
        await event.reply(get_system_info())

    async def help(event):
        await event.reply(phrase.help.comm, link_preview=True)

    async def ping(event):
        timestamp = event.date.timestamp()
        ping = round(time() - timestamp, 2)
        if ping < 0:
            ping = phrase.ping.min
        else:
            ping = f"за {str(ping)} сек."
        try:
            arg = event.text.split(' ')[1].lower()
        except IndexError:
            arg = None
        all_servers_ping = []
        if arg in [
            'all',
            'подробно',
            'подробный',
            'полн',
            'полный',
            'весь',
            'ии',
            'фулл',
            'full'
        ]:
            async with aiohttp.ClientSession() as session:
                n = 1
                for server in ai_servers:
                    timestamp = time()
                    async with session.get(server) as request:
                        try:
                            if await request.text() == 'ok':
                                server_ping = round(time() - timestamp, 2)
                                if server_ping > 0:
                                    server_ping = f"за {server_ping} сек."
                                else:
                                    server_ping = phrase.ping.min
                                all_servers_ping.append(
                                    f'\n🌐 : Сервер {n} ответил {server_ping}'
                                )
                            else:
                                all_servers_ping.append(
                                    f'\n❌ : Сервер {n} - Ошибка!'
                                )
                        except TimeoutError:
                            all_servers_ping.append(
                                f'❌ : Сервер {n} - Нет подключения!'
                            )
                    n += 1
        return await event.reply(phrase.ping.set.format(ping)+''.join(all_servers_ping))

    async def crocodile_hint(event):
        db = setting("current_game")
        hint = db["hints"]
        if event.sender_id in hint:
            return await event.reply(phrase.crocodile.hints_all)
        hint.append(event.sender_id)
        db["hints"] = hint
        setting("current_game", db)
        word = db["word"]
        last_hint = setting("crocodile_last_hint")
        if random() < coofs.PercentForRandomLetter and last_hint != 0:
            n = 1
            for letter in list(db['unsec']):
                if letter == '_':
                    response = f'{n} буква в слове - **{db["word"][n-1]}**'
                    break
                n += 1
        else:
            if last_hint != 0:
                check_last = 'Так же учитывай, ' \
                    f'что подсказка {last_hint} уже была.'
            else:
                check_last = ''
            response = await ai_response(
                f'Сделай подсказку для слова "{word}". '
                'Ни в коем случае не добавляй никаких "подсказка для слова.." '
                'и т.п, ответ должен содержать только подсказку. '
                'Не забудь, что подсказка не должна '
                'содержать слово в любом случае. ' + check_last
            )
            if response is None:
                db = setting("current_game")
                hint = db["hints"]
                hint.remove(event.sender_id)
                db["hints"] = hint
                setting("current_game", db)
                return await event.reply(phrase.crocodile.error)
            setting("crocodile_last_hint", response)
        return await event.reply(response)

    async def crocodile_handler(event):
        text = event.text.strip().lower()
        if len(text) > 0:
            current_word = setting("current_game")["word"]
            current_mask = list(setting("current_game")["unsec"])
            if text == current_word:
                bets = setting('crocodile_bets')
                all = 0
                bets_str = ''
                topers = []
                n = 1
                for toper in crocodile_stat.get_all().keys():
                    if n > coofs.TopLowerBets:
                        break
                    topers.append(toper)
                    n += 1
                if bets != {}:
                    for key in list(bets.keys()):
                        if str(event.sender_id) == key:
                            if str(event.sender_id) in topers:
                                all += round(bets[key]*coofs.TopBets)
                            else:
                                all += round(
                                    bets[key]*setting('crocodile_bet_coo')
                                )
                        else:
                            all += bets[key]
                    add_money(event.sender_id, all)
                    bets_str = phrase.crocodile.bet_win.format(
                        decline_number(all, 'изумруд'),
                    )
                setting("current_game", 0)
                setting("crocodile_bets", {})
                setting("crocodile_last_hint", 0)
                if setting('crocodile_super_game') == 1:
                    setting('crocodile_super_game', 0)
                    setting('max_bet', setting('default_max_bet'))
                    setting('min_bet', setting('default_min_bet'))
                client.remove_event_handler(crocodile_hint)
                client.remove_event_handler(crocodile_handler)
                crocodile_stat(event.sender_id).add()
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
                    cgame = setting("current_game")
                    cgame["unsec"] = "".join(current_mask)
                    setting("current_game", cgame)
                    return await event.reply(
                        phrase.crocodile.new.format(
                            "".join(current_mask).replace("_", "..")
                        )
                    )
                if list(setting("current_game")["unsec"]) != current_mask:
                    cgame = setting("current_game")
                    cgame["unsec"] = "".join(current_mask)
                    setting("current_game", cgame)
                    return await event.reply(
                        phrase.crocodile.new.format(
                            "".join(current_mask).replace("_", "..")
                        )
                    )

    async def crocodile(event):
        if not event.chat_id == setting("default_chat"):
            return await event.reply(phrase.default_chat)
        else:
            pass
        if setting("current_game") == 0:
            keyboard = ReplyInlineMarkup(
                [
                    KeyboardButtonRow(
                        [
                            KeyboardButtonCallback(
                                text="✅ Играть", data=b"crocodile.start"
                            ),
                            KeyboardButtonCallback(
                                text="❌ Остановить игру",
                                data=b"crocodile.stop"
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
                                text="❌ Остановить игру",
                                data=b"crocodile.stop"
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
            if bet < setting('min_bet'):
                return await event.reply(
                    phrase.money.min_count.format(
                        decline_number(setting('min_bet'), 'изумруд')
                    )
                )
            elif bet > setting('max_bet'):
                return await event.reply(
                    phrase.money.max_count.format(
                        decline_number(setting('max_bet'), 'изумруд')
                    )
                )
        except IndexError:
            bet = setting('min_bet')
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
        if setting("current_game") != 0:
            return await event.reply(
                phrase.crocodile.no
            )
        all_bets = setting('crocodile_bets')
        if str(event.sender_id) in all_bets:
            return await event.reply(
                phrase.crocodile.bet_already
            )
        add_money(event.sender_id, -bet)
        all_bets[str(event.sender_id)] = bet
        setting('crocodile_bets', all_bets)
        return await event.reply(
            phrase.crocodile.bet.format(
                decline_number(bet, 'изумруд')
            )
        )

    async def super_game(event):
        if event.sender_id not in setting('admins_id'):
            return await event.reply(phrase.perms.no)
        arg = event.text.lower().split(" ", maxsplit=1)[1]
        bets = setting('crocodile_bets')
        bets[str(tokens.bot.creator)] = 50
        setting('crocodile_bets', bets)
        setting('crocodile_super_game', 1)
        setting('max_bet', 100)
        setting('min_bet', 50)
        await client.send_message(
            tokens.bot.chat, phrase.crocodile.super_game_wait
        )
        await asyncio.sleep(60)
        setting(
            'current_game',
            {
                'hints': [],
                'unsec': '_'*len(arg),
                'word': arg
            }
        )
        client.add_event_handler(
            crocodile_hint,
            events.NewMessage(incoming=True, pattern="/подсказка")
        )
        client.add_event_handler(
            crocodile_handler,
            events.NewMessage(incoming=True, chats=tokens.bot.chat)
        )
        return await client.send_message(
            tokens.bot.chat, phrase.crocodile.super_game
        )

    async def gemini(event):
        try:
            arg = event.text.split(" ", maxsplit=1)[1]
        except IndexError:
            return await event.reply(phrase.no.response)
        response = await ai_response(arg)
        if response is None:
            return await event.reply(phrase.server.overload)
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await event.reply(response[x:x+4096])
        else:
            return await event.reply(response)

    @client.on(events.NewMessage(incoming=True, pattern=r"f/|p/"))
    async def mcrcon(event):
        if event.text[0] == 'f':
            host = setting('ipv4')
            port = setting('rcon_port_fabric')
            password = tokens.rcon
        elif event.text[0] == 'p':
            host = setting('ipv4')
            port = setting('rcon_port_purpur')
            password = tokens.rcon
        else:
            return await event.reply(phrase.no.server)

        if event.sender_id not in setting('admins_id'):
            return await event.reply(phrase.perms.no)
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

    async def add_staff(event):
        if event.sender_id != tokens.bot.creator:
            return await event.reply(phrase.perms.no)
        try:
            tag = event.text.split(" ", maxsplit=1)[1]
            user = await client(
                GetFullUserRequest(tag)
            )
            user = user.full_user.id
        except IndexError:
            reply_to_msg = event.reply_to_msg_id
            if reply_to_msg:
                reply_message = await event.get_reply_message()
                user = reply_message.sender_id
                entity = await client.get_entity(user)
                if entity.username is None:
                    if entity.last_name is None:
                        tag = entity.first_name
                    else:
                        tag = entity.first_name + " " + entity.last_name
                else:
                    tag = f'@{entity.username}'
            else:
                return await event.reply(
                    phrase.money.no_people
                )
        admins = setting('admins_id')
        admins.append(user)
        setting('admins_id', admins)
        return await event.reply(
            phrase.perms.admin_add.format(nick=tag, id=user)
        )

    async def del_staff(event):
        if event.sender_id != tokens.bot.creator:
            return await event.reply(phrase.perms.no)
        try:
            tag = event.text.split(" ", maxsplit=1)[1]
            user = await client(
                GetFullUserRequest(tag)
            )
            user = user.full_user.id
        except IndexError:
            reply_to_msg = event.reply_to_msg_id
            if reply_to_msg:
                reply_message = await event.get_reply_message()
                user = reply_message.sender_id
                entity = await client.get_entity(user)
                if entity.username is None:
                    if entity.last_name is None:
                        tag = entity.first_name
                    else:
                        tag = entity.first_name + " " + entity.last_name
                else:
                    tag = f'@{entity.username}'
            else:
                return await event.reply(
                    phrase.money.no_people
                )
        admins = setting('admins_id')
        while user.full_user.id in admins:
            admins.remove(user.full_user.id)
        setting('admins_id', admins)
        return await event.reply(phrase.perms.admin_del)

    async def server_top_list(event):
        try:
            async with MinecraftClient(
                host=setting('ipv4'),
                port=setting('rcon_port_purpur'),
                password=tokens.rcon
            ) as rcon:
                await event.reply(
                    remove_section_marks(
                        await rcon.send('playtime top')
                    ).replace(
                        '(Лидеры по времени на сервере)',
                        phrase.stat_server.format("ванильного")
                    ).replace(
                        '***',
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
        if event.sender_id not in setting('admins_id'):
            return await event.reply(phrase.perms.no)
        args = event.text.split(" ", maxsplit=3)
        try:
            tag = args[2]
            user = await client(
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
            count = int(args[1])
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

        try:
            tag = args[2]
            user = await client(
                GetFullUserRequest(tag)
            )
            user = user.full_user.id
        except (TypeError, ValueError, IndexError):
            reply_to_msg = event.reply_to_msg_id
            if reply_to_msg:
                reply_message = await event.get_reply_message()
                user = reply_message.sender_id
            else:
                return await event.reply(
                    phrase.money.no_people+phrase.money.swap_balance_use
                )

        sender_balance = get_money(event.sender_id)
        if sender_balance < count:
            return await event.reply(
                phrase.money.not_enough.format(
                    decline_number(sender_balance, 'изумруд')
                )
            )
        add_money(event.sender_id, -count)
        add_money(user, count)
        return await event.reply(
            phrase.money.swap_money.format(
                decline_number(count, 'изумруд')
            )
        )

    async def tg_dns(event):
        if event.sender_id not in setting('admins_id'):
            return await event.reply(phrase.perms.no)
        return await event.reply(
            phrase.dns.format(await setup_ip(check_set=False)),
            parse_mode="html"
        )

    async def all_money(event):
        return await event.reply(
            phrase.money.all_money.format(
                decline_number(get_all_money(), 'изумруд')
            )
        )

    async def crocodile_wins(event):
        all = crocodile_stat.get_all()
        text = ''
        n = 1
        for id in all.keys():
            if n > 10:
                break
            try:
                entity = await client.get_entity(int(id))
                name = entity.first_name
                if entity.last_name is not None:
                    name += f' {entity.last_name}'
            except:
                name = 'Неопознанный персонаж'
            text += f'{n}. {name}: {all[id]}\n'
            n += 1
        return await event.reply(
            phrase.crocodile.stat.format(text)
        )

    async def word_request(event):
        word = event.text.split(' ', maxsplit=1)[1].lower()
        with open(
            path.join('db', 'crocodile_words.txt'), 'r', encoding='utf-8'
        ) as f:
            if f'\n{word}\n' in f.read():
                return await event.reply(
                    phrase.word.exists
                )
        try:
            entity = await client.get_entity(event.sender_id)
        except TypeError:
            return await event.reply(
                phrase.word.no_user
            )
        entity = entity.username
        logger.info(f'Пользователь {entity} хочет добавить слово "{word}"')
        keyboard = ReplyInlineMarkup(
            [
                KeyboardButtonRow(
                    [
                        KeyboardButtonCallback(
                            text="✅ Добавить",
                            data=f"word.yes.{word}.{event.sender_id}".encode()
                        ),
                        KeyboardButtonCallback(
                            text="❌ Отклонить",
                            data=f"word.no.{word}.{event.sender_id}".encode()
                        )
                    ]
                )
            ]
        )
        try:
            await client.send_message(
                tokens.bot.creator,
                phrase.word.request.format(
                    user=f'@{entity}',
                    word=word
                ),
                buttons=keyboard
            )
        except TGErrors.ButtonDataInvalidError:
            return await event.reply(
                phrase.word.long
            )
        return await event.reply(
            phrase.word.set.format(word=word)
        )

    async def check_nick(event):
        args = event.text.split(' ', maxsplit=1)
        try:
            tag = args[1]
            user = await client(
                GetFullUserRequest(tag)
            )
            user = user.full_user.id
        except (TypeError, ValueError, IndexError):
            reply_to_msg = event.reply_to_msg_id
            if reply_to_msg:
                reply_message = await event.get_reply_message()
                user = reply_message.sender_id
            else:
                return await event.reply(phrase.nick.who)
        nick = nicks(id=user).get()
        if nick is None:
            return await event.reply(phrase.nick.no_nick)
        return await event.reply(phrase.nick.usernick.format(nick))

    @client.on(events.NewMessage(pattern=r'/чара(.*)'))
    @client.on(events.NewMessage(pattern=r'/чарка(.*)'))
    @client.on(events.NewMessage(pattern=r'/зачарование(.*)'))
    @client.on(events.NewMessage(pattern=r'/enchant(.*)'))
    @client.on(events.NewMessage(pattern=r'что за чара(.*)'))
    @client.on(events.NewMessage(pattern=r'чарка(.*)'))
    @client.on(events.NewMessage(pattern=r'зачарование(.*)'))
    async def get_enchant(event):
        arg = event.pattern_match.group(1)
        if arg.strip() == '':
            return await event.reply(phrase.enchant.no_arg)
        desc = get_enchant_desc(arg)
        if desc is None:
            return await event.reply(phrase.enchant.no_diff)
        return await event.reply(phrase.enchant.main.format(desc))

    await client.start(bot_token=tokens.bot.token)

    'Посмотреть ник'
    client.add_event_handler(
        check_nick, events.NewMessage(incoming=True, pattern="/ник")
    )
    client.add_event_handler(
        check_nick, events.NewMessage(incoming=True, pattern="/nick")
    )

    'Запрос на слово'
    client.add_event_handler(
        word_request, events.NewMessage(incoming=True, pattern="/слово")
    )

    'Все деньги'
    client.add_event_handler(
        all_money, events.NewMessage(incoming=True, pattern="/банк")
    )

    'Стата крокодила'
    client.add_event_handler(
        crocodile_wins, events.NewMessage(
            incoming=True, pattern="/стат крокодил"
        )
    )

    'ДНС'
    client.add_event_handler(
        tg_dns, events.NewMessage(incoming=True, pattern="/днс")
    )
    client.add_event_handler(
        tg_dns, events.NewMessage(incoming=True, pattern="/dns")
    )

    'Супер-игра'
    client.add_event_handler(
        super_game, events.NewMessage(incoming=True, pattern="/суперигра")
    )

    'Линк ника к майнкрафту'
    client.add_event_handler(
        link_nick, events.NewMessage(incoming=True, pattern="/linknick")
    )
    client.add_event_handler(
        link_nick, events.NewMessage(incoming=True, pattern="/привязать")
    )
    client.add_event_handler(
        link_nick, events.NewMessage(incoming=True, pattern="/connect")
    )

    'Магазин'
    client.add_event_handler(
        shop, events.NewMessage(incoming=True, pattern="/shop")
    )
    client.add_event_handler(
        shop, events.NewMessage(incoming=True, pattern="/магазин")
    )

    'Кошелек'
    client.add_event_handler(
        get_balance,
        events.NewMessage(incoming=True, pattern="/баланс")
    )
    client.add_event_handler(
        get_balance,
        events.NewMessage(incoming=True, pattern="/мой баланс")
    )
    client.add_event_handler(
        get_balance,
        events.NewMessage(incoming=True, pattern="/wallet")
    )

    'Добавить монет'
    client.add_event_handler(
        add_balance,
        events.NewMessage(incoming=True, pattern="/изменить баланс")
    )
    client.add_event_handler(
        add_balance,
        events.NewMessage(incoming=True, pattern="/change balance")
    )

    'Переслать монет'
    client.add_event_handler(
        swap_money,
        events.NewMessage(incoming=True, pattern="/скинуть")
    )
    client.add_event_handler(
        swap_money,
        events.NewMessage(incoming=True, pattern="/переслать")
    )
    client.add_event_handler(
        swap_money,
        events.NewMessage(incoming=True, pattern="/кинуть")
    )
    client.add_event_handler(
        swap_money,
        events.NewMessage(incoming=True, pattern="/дать")
    )

    'Топ игроков'
    client.add_event_handler(
        server_top_list,
        events.NewMessage(incoming=True, pattern="/топ игроков")
    )
    client.add_event_handler(
        server_top_list,
        events.NewMessage(incoming=True, pattern="/top players")
    )
    client.add_event_handler(
        server_top_list,
        events.NewMessage(incoming=True, pattern="/bestplayers")
    )

    'Сервер'
    client.add_event_handler(
        sysinfo, events.NewMessage(incoming=True, pattern="/серв")
    )
    client.add_event_handler(
        sysinfo, events.NewMessage(incoming=True, pattern="/сервер")
    )
    client.add_event_handler(
        sysinfo, events.NewMessage(incoming=True, pattern="/server")
    )

    'Айпи'
    client.add_event_handler(
        host, events.NewMessage(incoming=True, pattern="/хост")
    )
    client.add_event_handler(
        host, events.NewMessage(incoming=True, pattern="/host")
    )

    'Помощь'
    client.add_event_handler(
        help, events.NewMessage(incoming=True, pattern="/помощь")
    )
    client.add_event_handler(
        help, events.NewMessage(incoming=True, pattern="/команды")
    )
    client.add_event_handler(
        help, events.NewMessage(incoming=True, pattern="/help")
    )

    'Пинг'
    client.add_event_handler(
        ping, events.NewMessage(incoming=True, pattern="/пинг")
    )
    client.add_event_handler(
        ping, events.NewMessage(incoming=True, pattern="/ping")
    )

    'ИИ'
    client.add_event_handler(
        gemini, events.NewMessage(incoming=True, pattern="/ии")
    )
    client.add_event_handler(
        gemini, events.NewMessage(incoming=True, pattern="ии")
    )
    client.add_event_handler(
        gemini, events.NewMessage(incoming=True, pattern="/ai")
    )

    'Админы'
    client.add_event_handler(
        add_staff, events.NewMessage(incoming=True, pattern=r"\+cтафф")
    )
    client.add_event_handler(
        add_staff, events.NewMessage(incoming=True, pattern=r"\+staff")
    )
    client.add_event_handler(
        del_staff, events.NewMessage(incoming=True, pattern=r"\-стафф")
    )
    client.add_event_handler(
        del_staff, events.NewMessage(incoming=True, pattern=r".\-staff")
    )

    'Крокодил'
    client.add_event_handler(
        crocodile, events.NewMessage(incoming=True, pattern="/крокодил")
    )
    client.add_event_handler(
        crocodile, events.NewMessage(incoming=True, pattern="/crocodile")
    )
    client.add_event_handler(
        crocodile_bet, events.NewMessage(incoming=True, pattern="/ставка")
    )

    if setting("current_game") != 0:
        client.add_event_handler(
            crocodile_handler,
            events.NewMessage(incoming=True, chats=tokens.bot.chat)
        )
        client.add_event_handler(
            crocodile_hint,
            events.NewMessage(incoming=True, pattern="/подсказка")
        )

    await client.run_until_disconnected()


async def setup_ip(check_set=True):
    '''
    Обновляет динамику.
    Параметр check_set отвечает за принудительность
    '''

    error_text = ''
    try:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "https://v4.ident.me", timeout=3
                ) as v4_ident:
                    v4 = await v4_ident.text()
            except Exception:
                v4 = False
                error_text += 'Не могу получить IPv4.\n'
            try:
                async with session.get(
                    "https://v6.ident.me", timeout=3
                ) as v6_ident:
                    v6 = await v6_ident.text()
            except Exception:
                v6 = False
                error_text += 'Не могу получить IPv6.\n'
            if not v4 and not v6:
                return logger.error('Ошибка при получении IP.'
                                    'Сервер может быть недоступен')
            elif v4 == setting('ipv4') and v6 == setting('ipv6') and check_set:
                return logger.warning("IPv4 и IPv6 не изменились")
            if check_set:
                logger.warning("IPv4 или IPv6 изменились")
            else:
                logger.warning('Принудительно выставляю IP')
            setting('ipv4', v4)
            setting('ipv6', v6)

            "NOIP синхронизация"
            async with session.get(
                f'http://{tokens.noip.name}:{tokens.noip.password}'
                '@dynupdate.no-ip.com/'
                f'nic/update?hostname={setting("noip_host")}&myip={v4},{v6}',
                headers={
                    "User-Agent": "Trassert MinecraftServer' \
                        '/Windows 11-22000 s3pple@yandex.ru"
                },
            ) as noip:
                logger.info(f"Ответ NOIP: {await noip.text()}")
                noip = await noip.text()

            "REGru синхронизация"
            input_data = {
                "username": tokens.reg.email,
                "password": tokens.reg.password,
                "output_content_type": "plain",
                "domain_name": setting('host')
            }
            post = await session.post(
                'https://api.reg.ru/api/regru2/zone/clear',
                data=input_data
            )
            out = await post.json(content_type='text/plain')
            logger.warning(out)

            input_data = {
                "username": tokens.reg.email,
                "password": tokens.reg.password,
                "subdomain": "@",
                "ipaddr": v4,
                "output_content_type": "plain",
                "domain_name": setting('host')
            }
            post = await session.post(
                'https://api.reg.ru/api/regru2/zone/add_alias',
                data=input_data
            )
            out = await post.json(content_type='text/plain')
            logger.warning(out)

            input_data = {
                "username": tokens.reg.email,
                "password": tokens.reg.password,
                "subdomain": "@",
                "ipaddr": v6,
                "output_content_type": "plain",
                "domain_name": setting('host')
            }
            post = await session.post(
                'https://api.reg.ru/api/regru2/zone/add_aaaa',
                data=input_data
            )
            out = await post.json(content_type='text/plain')
            logger.warning(out)

            input_data = {
                "username": tokens.reg.email,
                "password": tokens.reg.password,
                "subdomain": "v6",
                "ipaddr": v6,
                "output_content_type": "plain",
                "domain_name": setting('host')
            }
            post = await session.post(
                'https://api.reg.ru/api/regru2/zone/add_aaaa',
                data=input_data
            )
            out = await post.json(content_type='text/plain')
            logger.warning(out)
    except Exception:
        error_text += format_exc()
        logger.error(error_text)
    return error_text if error_text != '' else noip


async def time_to_check_ip():
    while True:
        await asyncio.sleep(coofs.IPSleepTime)
        await setup_ip()


async def web_server():
    async def hotmc(request):
        load = await request.post()
        nick = load['nick']
        sign = load['sign']
        time = load['time']
        logger.warning(f'{nick} проголосовал в {time} с хешем {sign}')
        hash = sha1(
            f'{nick}{time}{tokens.hotmc}'.encode()
        ).hexdigest()
        if sign != hash:
            logger.warning('Хеш не совпал!')
            logger.warning(f'Должен быть: {sign}')
            logger.warning(f'Имеется: {hash}')
            return aiohttp.web.Response(
                text='Переданные данные не прошли проверку.'
            )
        tg_id = nicks(nick=nick).get()
        if tg_id is not None:
            add_money(tg_id, 10)
            give = phrase.hotmc_money.format(
                decline_number(10, 'изумруд')
            )
        else:
            give = ''
        await client.send_message(
            tokens.bot.chat,
            phrase.hotmc.format(nick=nick, money=give),
            link_preview=False
        )
        return aiohttp.web.Response(text='ok')

    async def servers(request):
        load = await request.post()
        username = load['username']
        sign = load['sign']
        time = load['time']
        logger.warning(f'{username} проголосовал в {time} с хешем {sign}')
        hash = md5(
            f'{username}|{time}|{tokens.mcservers}'.encode()
        ).hexdigest()
        if sign != hash:
            logger.warning('Хеш не совпал!')
            logger.warning(f'Должен быть: {sign}')
            logger.warning(f'Имеется: {hash}')
            return aiohttp.web.Response(
                text='Переданные данные не прошли проверку.'
            )
        tg_id = nicks(nick=username).get()
        if tg_id is not None:
            add_money(tg_id, 10)
            give = phrase.servers_money.format(
                decline_number(10, 'изумруд')
            )
        else:
            give = ''
        await client.send_message(
            tokens.bot.chat,
            phrase.servers.format(nick=username, money=give),
            link_preview=False
        )
        return aiohttp.web.Response(text='ok')

    async def version(request):
        q = request.query.get('q')
        try:
            client_version = int(request.query.get("version"))
        except (ValueError, TypeError):
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

    async def github(request):
        'Вебхук для гитхаба'
        load = await request.json()
        head = load['head_commit']
        await client.send_message(
            tokens.bot.chat,
            phrase.github.format(
                author=head["author"]["name"],
                message=head["message"],
                url=head["url"]
            ),
            link_preview=False
        )
        return aiohttp.web.Response(text='ok')

    app = aiohttp.web.Application()
    app.add_routes(
        [
            aiohttp.web.post('/hotmc', hotmc),
            aiohttp.web.post('/servers', servers),
            aiohttp.web.post('/github', github),
            aiohttp.web.get('/version', version)
        ]
    )
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    ipv4 = aiohttp.web.TCPSite(runner, '0.0.0.0', 5000)
    ipv6 = aiohttp.web.TCPSite(runner, setting('ipv6'), 5000)
    await ipv4.start()
    await ipv6.start()


async def main():
    while True:
        try:
            await setup_ip()
            await web_server()
            await asyncio.gather(
                bot(),
                time_to_update_shop(),
                time_to_check_ip()
            )
        except ConnectionError:
            logger.error('Жду 20 секунд (нет подключения к интернету)')
            await asyncio.sleep(20)
        except KeyboardInterrupt:
            logger.warning('Закрываю бота!')
            break


if __name__ == "__main__":
    if sum(setting('shop_weight').values()) != 100:
        logger.error('Сумма процентов в магазине не равна 100!')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning('Закрываю бота!')
