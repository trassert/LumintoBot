from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

import re
import asyncio

from telethon.tl.custom import Message
from telethon import events
from telethon.tl.types import (
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonCallback,
)

from .client import client
from .global_checks import *
from .func import get_name

from .. import config, phrase, formatter


@client.on(events.NewMessage(pattern=r"(?i)^/states$", func=checks))
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
        text += f'{n}. **{state}** - {len(data[state]["players"])+1} чел.\n'
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
    state_name = event.pattern_match.group(1).strip()
    if state_name == "":
        check = db.states.if_player(event.sender_id) or db.states.if_author(
            event.sender_id
        )
        if check is False:
            return await event.reply(phrase.state.no_name)
        state_name = check
    if db.states.find(state_name) is False:
        return await event.reply(phrase.state.not_find)
    state = db.state(state_name)
    enter = "Свободный" if state.enter else "Закрыт"
    if state.price > 0:
        enter = formatter.value_to_str(state.price, "изумруд")
    tasks = [get_name(player, minecraft=True) for player in state.players]
    idented_players = await asyncio.gather(*tasks)
    return await event.reply(
        phrase.state.get.format(
            type=phrase.state_types[state.type],
            name=state.name.capitalize(),
            money=formatter.value_to_str(int(state.money), "изумруд"),
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
                        text=phrase.state.rem_button,
                        data=f"state.remove.{state_name}".encode(),
                    )
                ]
            )
        ]
    )
    return await event.reply(
        phrase.state.rem_message.format(name=state_name), buttons=keyboard
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
            phrase.state.enter_price.format(formatter.value_to_str(arg, "изумруд"))
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
            phrase.money.not_enough.format(formatter.value_to_str(balance, "изумруд"))
        )
    db.add_money(event.sender_id, -arg)
    state = db.state(state_name)
    state.change("money", state.money + arg)
    logger.info(f"Казна {state_name} пополнена на {arg}")
    return await event.reply(
        phrase.state.add_treasury.format(formatter.value_to_str(arg, "изумруд"))
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
        phrase.state.rem_treasury.format(formatter.value_to_str(arg, "изумруд"))
    )


@client.on(events.NewMessage(pattern=r"(?i)^/забрать из казны$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/г снять$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-казна$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^г снять$", func=checks))
async def state_rem_money_empty(event: Message):
    return await event.reply(phrase.state.howto_rem_balance)
