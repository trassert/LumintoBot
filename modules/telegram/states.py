import asyncio
import re
from random import choice

from loguru import logger
from telethon import errors as tgerrors
from telethon.tl.custom import Message
from telethon.tl.types import (
    KeyboardButtonCallback,
    KeyboardButtonRow,
    ReplyInlineMarkup,
)

from .. import config, db, formatter, pathes, phrase
from . import func
from .client import client

logger.info(f"Загружен модуль {__name__}!")


@func.new_command(r"/states$")
@func.new_command(r"/states@")
@func.new_command(r"/госва$")
@func.new_command(r"/государства$")
@func.new_command(r"государства$")
@func.new_command(r"список госв$")
async def states_all(event: Message):
    data = db.states.get_all()
    if data == {}:
        return await event.reply(phrase.state.empty_list)
    text = phrase.state.all
    n = 1
    for state in data:
        text += f"{n}. **{state}** - {len(data[state]['players']) + 1} чел.\n"
        n += 1
    return await event.reply(text)


@func.new_command(r"/toptreasury$")
@func.new_command(r"/topstate@")
@func.new_command(r"/топказна$")
@func.new_command(r"/топ казна$")
@func.new_command(r"/казна топ$")
@func.new_command(r"/казтоп$")
@func.new_command(r"/ктоп$")
@func.new_command(r"казна топ$")
@func.new_command(r"казтоп$")
async def states_all_top(event: Message):
    data = db.states.get_all(sortedby="money")
    if data == {}:
        return await event.reply(phrase.state.empty_list)
    text = phrase.state.toptreasury
    n = 1
    for state in data:
        if data[state]["money"] > 0:
            text += f"{n}. **{state}** - {data[state]['money']} амт.\n"
            n += 1
    return await event.reply(text)


@func.new_command(r"/создать госво\s(.+)")
@func.new_command(r"\+госво\s(.+)")
@func.new_command(r"\+государство\s(.+)")
async def state_make(event: Message):
    arg: str = event.pattern_match.group(1).strip().lower()
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
    if db.states.check(arg.capitalize()) is True:
        return await event.reply(phrase.state.already_here)
    if await db.get_money(event.sender_id) < config.cfg.PriceForNewState:
        return await event.reply(phrase.state.require_emerald)
    try:
        return await event.reply(
            phrase.state.warn_make.format(arg),
            buttons=[
                [
                    KeyboardButtonCallback(
                        text="🏰 Создать государство",
                        data=f"state.m.{event.sender_id}.{arg.capitalize()}".encode(),
                    ),
                ],
            ],
        )
    except tgerrors.ButtonDataInvalidError:
        return await event.reply(phrase.state.too_long)


@func.new_command(r"/создать госво$")
@func.new_command(r"\+госво$")
@func.new_command(r"\+государство$")
async def state_make_empty(event: Message):
    return await event.reply(phrase.state.no_name)


@func.new_command(r"/вступить(.*)")
@func.new_command(r"вступить(.*)")
@func.new_command(r"/г вступить(.*)")
@func.new_command(r"/г войти(.*)")
async def state_enter(event: Message):
    arg: str = event.pattern_match.group(1).strip()
    if not arg:
        return await event.reply(phrase.state.no_name)

    if not db.states.find(arg):
        return await event.reply(phrase.state.not_find)

    nick = db.nicks(id=event.sender_id).get()
    if nick is None:
        return await event.reply(phrase.state.not_connected)

    if db.states.if_player(event.sender_id) is not False:
        return await event.reply(phrase.state.already_player)

    if db.states.if_author(event.sender_id) is not False:
        return await event.reply(phrase.state.already_author)

    state = db.state(arg)
    if not state.enter:
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
                            ),
                        ]
                    ),
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

    if state.type == 0 and len(players) >= config.cfg.Type1Players:
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.up.format(name=state_name, type="Государство"),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 1)
    elif state.type == 1 and len(players) >= config.cfg.Type2Players:
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.up.format(name=state_name, type="Империя"),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 2)

    return await event.reply(phrase.state.admit.format(state_name))


@func.new_command(r"/state$")
@func.new_command(r"/state@")
@func.new_command(r"/госво(.*)")
@func.new_command(r"/государство(.*)")
async def state_get(event: Message):
    try:
        state_name = event.pattern_match.group(1).strip()
    except IndexError:
        state_name = ""
    if state_name == "":
        check = db.states.if_player(event.sender_id) or db.states.if_author(
            event.sender_id,
        )
        if check is False:
            return await event.reply(phrase.state.no_name)
        state_name = check
    if db.states.find(state_name) is False:
        return await event.reply(phrase.state.not_find)
    state = db.state(state_name)
    enter = "Свободный" if state.enter else "Закрыт"
    if state.price > 0:
        enter = formatter.value_to_str(state.price, phrase.currency)
    tasks = [func.get_name(player, minecraft=True) for player in state.players]
    idented_players = await asyncio.gather(*tasks)
    pic_path = pathes.states_pic / f"{state_name}.png"
    return await client.send_message(
        event.chat_id,
        phrase.state.get.format(
            type=phrase.state_types[state.type],
            name=state.name.capitalize(),
            money=formatter.value_to_str(int(state.money), phrase.currency),
            author=db.nicks(id=state.author).get(),
            enter=enter,
            desc=state.desc,
            date=state.date,
            players=len(state.players),
            list_players=", ".join(idented_players),
            xyz=state.coordinates,
        ),
        reply_to=event.id,
        link_preview=False,
        silent=True,
        file=pic_path if pic_path.exists() else None,
    )


@func.new_command(r"/ливнуть")
@func.new_command(r"/покинуть госво")
@func.new_command(r"/покинуть государство")
@func.new_command(r"выйти из государства")
@func.new_command(r"выйти из госва")
@func.new_command(r"/г покинуть")
@func.new_command(r"/г выйти")
async def state_leave(event: Message):
    state_name = db.states.if_player(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_member)
    state = db.state(state_name)
    state.players.remove(event.sender_id)
    state.change("players", state.players)
    state_name: str = state.name.capitalize()
    await client.send_message(
        entity=config.chats.chat,
        message=phrase.state.leave_player.format(
            state=state_name,
            player=db.nicks(id=event.sender_id).get(),
        ),
        reply_to=config.chats.topics.rp,
    )
    if (state.type == 2) and (len(state.players) < config.cfg.Type2Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.down.format(
                name=state.name,
                type="Государство",
            ),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 1)
    if (state.type == 1) and (len(state.players) < config.cfg.Type1Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.down.format(name=state_name, type="Княжество"),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 0)
    return await event.reply(phrase.state.leave)


@func.new_command(r"/уничтожить госво")
@func.new_command(r"/удалить госво")
@func.new_command(r"/удалить государство")
@func.new_command(r"уничтожить государство")
@func.new_command(r"удалить государство")
@func.new_command(r"/г уничтожить")
@func.new_command(r"/г удалить")
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
                    ),
                ],
            ),
        ],
    )
    return await event.reply(
        phrase.state.rem_message.format(name=state_name),
        buttons=keyboard,
    )


@func.new_command(r"/г описание$")
@func.new_command(r"/о госве$")
@func.new_command(r"/г о госве$")
async def state_desc_empty(event: Message):
    return await event.reply(phrase.state.no_desc)


@func.new_command(r"/г описание\s([\s\S]+)")
@func.new_command(r"/о госве\s([\s\S]+)")
@func.new_command(r"/г о госве\s([\s\S]+)")
async def state_desc(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    new_desc = event.pattern_match.group(1).strip()
    if len(new_desc) > config.cfg.DescriptionsMaxLen:
        return await event.reply(
            phrase.state.max_len.format(config.cfg.DescriptionsMaxLen),
        )
    db.state(state_name).change("desc", new_desc)
    return await event.reply(phrase.state.change_desc)


@func.new_command(r"/г корды$")
@func.new_command(r"/г координаты$")
async def state_coords_empty(event: Message):
    return await event.reply(phrase.state.howto_change_coords)


@func.new_command(r"/г корды\s(.+)")
@func.new_command(r"/г координаты\s(.+)")
async def state_coords(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    arg: str = event.pattern_match.group(1).strip()
    try:
        arg = list(map(int, arg.split()))
    except ValueError:
        return await event.reply(phrase.state.howto_change_coords)
    if len(arg) != 3:
        return await event.reply(phrase.state.howto_change_coords)
    db.state(state_name).change("coordinates", ", ".join(list(map(str, arg))))
    return await event.reply(phrase.state.change_coords)


@func.new_command(r"/г входы\s(.+)")
@func.new_command(r"/г вступления\s(.+)")
async def state_enter_arg(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    arg: str = event.pattern_match.group(1).strip()
    state = db.state(state_name)
    if arg in ["да", "+", "разрешить", "открыть", "true", "ok", "ок", "можно"]:
        if state.price != 0:
            state.change("price", 0)
        elif state.enter is True:
            return await event.reply(phrase.state.already_open)
        state.change("enter", True)
        return await event.reply(phrase.state.enter_open)
    if arg in [
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
    if arg.isdigit():
        arg = int(arg)
        state.change("price", arg)
        state.change("enter", True)
        return await event.reply(
            phrase.state.enter_price.format(
                formatter.value_to_str(arg, phrase.currency),
            ),
        )
    return await event.reply(phrase.state.howto_enter)


@func.new_command(r"/г входы$")
@func.new_command(r"/г вступления$")
async def state_enter_empty(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    state = db.state(state_name)
    if state.enter is True:
        if state.price != 0:
            state.change("price", 0)
        state.change("enter", False)
        return await event.reply(phrase.state.enter_close)
    if state.enter is False:
        state.change("enter", True)
        return await event.reply(phrase.state.enter_open)
    return None


@func.new_command(r"/пополнить казну (.+)")
@func.new_command(r"/г пополнить (.+)")
@func.new_command(r"\+казна (.+)")
@func.new_command(r"г пополнить (.+)")
async def state_add_money(event: Message):
    state_name = db.states.if_player(event.sender_id)
    if state_name is False:
        state_name = db.states.if_author(event.sender_id)
        if state_name is False:
            return await event.reply(phrase.state.not_a_member)
    arg: str = event.pattern_match.group(1).strip()
    if arg in ["все", "всё", "все деньги", "на все"]:
        arg = await db.get_money(event.sender_id)
    elif not arg.isdigit():
        return await event.reply(phrase.state.howto_add_balance)
    try:
        arg = int(arg)
    except Exception:
        return await event.reply(phrase.state.howto_add_balance)
    if arg < 1:
        return await event.reply(phrase.money.negative_count)
    balance = await db.get_money(event.sender_id)
    if arg > balance:
        return await event.reply(
            phrase.money.not_enough.format(
                formatter.value_to_str(balance, phrase.currency),
            ),
        )
    db.add_money(event.sender_id, -arg)
    state = db.state(state_name)
    state.change("money", state.money + arg)
    logger.info(f"Казна {state_name} пополнена на {arg}")
    return await event.reply(
        phrase.state.add_treasury.format(formatter.value_to_str(arg, phrase.currency)),
    )


@func.new_command(r"/пополнить казну$")
@func.new_command(r"/г пополнить$")
@func.new_command(r"\+казна$")
@func.new_command(r"г пополнить$")
async def state_add_money_empty(event: Message):
    return await event.reply(phrase.state.howto_add_balance)


@func.new_command(r"/забрать из казны (.+)")
@func.new_command(r"/г снять (.+)")
@func.new_command(r"\-казна (.+)")
@func.new_command(r"г снять (.+)")
async def state_rem_money(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    arg: str = event.pattern_match.group(1).strip()
    state = db.state(state_name)
    if arg in ["все", "всё", "все деньги", "на все"]:
        arg = state.money
    elif not arg.isdigit():
        return await event.reply(phrase.state.howto_rem_balance)
    try:
        arg = int(arg)
    except Exception:
        return await event.reply(phrase.state.howto_rem_balance)
    if arg < 1:
        return await event.reply(phrase.money.negative_count)
    if state.money < arg:
        return await event.reply(phrase.state.too_low)
    state.change("money", state.money - arg)
    db.add_money(event.sender_id, arg)
    return await event.reply(
        phrase.state.rem_treasury.format(formatter.value_to_str(arg, phrase.currency)),
    )


@func.new_command(r"/забрать из казны$")
@func.new_command(r"/г снять$")
@func.new_command(r"\-казна$")
@func.new_command(r"г снять$")
async def state_rem_money_empty(event: Message):
    return await event.reply(phrase.state.howto_rem_balance)


@func.new_command(r"/г кик\s(.+)")
@func.new_command(r"/г кикнуть\s(.+)")
@func.new_command(r"/г выгнать\s(.+)")
@func.new_command(r"/выгнать\s(.+)")
async def state_kick_user(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    user = await func.get_id(event.pattern_match.group(1).strip())
    if user is None:
        return await event.reply(phrase.player_not_in)
    state = db.state(state_name)
    if user not in state.players:
        return await event.reply(phrase.state.player_not_in)
    state.players.remove(user)
    state.change("players", state.players)
    if (state.type == 2) and (len(state.players) < config.cfg.Type2Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.down.format(
                name=state.name,
                type="Государство",
            ),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 1)
    if (state.type == 1) and (len(state.players) < config.cfg.Type1Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.down.format(name=state_name, type="Княжество"),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 0)
    await client.send_message(
        entity=config.chats.chat,
        message=choice(phrase.state.kicked_rp).format(
            state=state_name,
            player=await func.get_name(user, minecraft=True),
        ),
        reply_to=config.chats.topics.rp,
    )
    return await event.reply(
        phrase.state.kicked.format(await func.get_name(user, minecraft=True)),
    )


@func.new_command(r"/г кик$")
@func.new_command(r"/г кикнуть$")
@func.new_command(r"/г выгнать$")
@func.new_command(r"/выгнать$")
async def state_kick_user_empty(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    if not event.reply_to_msg_id:
        return await event.reply(phrase.state.no_player)
    reply_message = await event.get_reply_message()
    user = reply_message.sender_id
    state = db.state(state_name)
    if user not in state.players:
        return await event.reply(phrase.state.player_not_in)
    state.players.remove(user)
    state.change("players", state.players)
    if (state.type == 2) and (len(state.players) < config.cfg.Type2Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.down.format(
                name=state.name,
                type="Государство",
            ),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 1)
    if (state.type == 1) and (len(state.players) < config.cfg.Type1Players):
        await client.send_message(
            entity=config.chats.chat,
            message=phrase.state.down.format(name=state_name, type="Княжество"),
            reply_to=config.chats.topics.rp,
        )
        state.change("type", 0)
    await client.send_message(
        entity=config.chats.chat,
        message=choice(phrase.state.kicked_rp).format(
            state=state_name,
            player=db.nicks(id=event.sender_id).get(),
        ),
        reply_to=config.chats.topics.rp,
    )
    return await event.reply(
        phrase.state.kicked.format(await func.get_name(user, minecraft=True)),
    )


@func.new_command(r"/г название (.+)")
@func.new_command(r"/г нейм (.+)")
@func.new_command(r"/г name (.+)")
@func.new_command(r"/г переназвать (.+)")
@func.new_command(r"/название госва (.+)")
async def state_rename(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    new_name: str = event.pattern_match.group(1).strip()
    if db.states.check(new_name.capitalize()):
        return await event.reply(phrase.state.already_here)
    keyboard = [
        [
            KeyboardButtonCallback(
                text=phrase.state.button_rename,
                data=f"state.rn.{new_name}.{event.sender_id}".encode(),
            ),
        ],
    ]
    return await event.reply(
        phrase.state.rename.format(new_name.capitalize()),
        buttons=keyboard,
        parse_mode="html",
    )


@func.new_command(r"/г pic$")
@func.new_command(r"/г картинка$")
@func.new_command(r"/г фото$")
async def state_pic(event: Message):
    state_name = db.states.if_author(event.sender_id)
    if state_name is False:
        return await event.reply(phrase.state.not_a_author)
    if not event.photo:
        return await event.reply(phrase.state.no_pic)
    await event.download_media(
        file=pathes.states_pic / f"{state_name}.png",
    )
    return await event.reply(phrase.state.pic_set)
