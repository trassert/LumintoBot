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


async def _check_and_update_tier(state, players_len: int, name_cap: str) -> None:
    """Обновляет статус (Княжество/Государство/Империя) при изменении состава."""
    new_type = None
    label = ""

    if state.type == 0 and players_len >= config.cfg.Type1Players:
        new_type, label = 1, "Государство"
    elif state.type == 1 and players_len >= config.cfg.Type2Players:
        new_type, label = 2, "Империя"
    elif state.type == 2 and players_len < config.cfg.Type2Players:
        new_type, label = 1, "Государство"
    elif state.type == 1 and players_len < config.cfg.Type1Players:
        new_type, label = 0, "Княжество"

    if new_type is not None:
        state.change("type", new_type)
        msg_template = phrase.state.up if new_type > state.type else phrase.state.down
        await client.send_message(
            entity=config.chats.chat,
            message=msg_template.format(name=name_cap, type=label),
            reply_to=config.chats.topics.rp,
        )


@func.new_command(r"/states$")
@func.new_command(r"/states@")
@func.new_command(r"/госва$")
@func.new_command(r"/государства$")
@func.new_command(r"государства$")
@func.new_command(r"список госв$")
async def states_all(event: Message) -> Message:
    data = db.states.get_all()
    if not data:
        return await event.reply(phrase.state.empty_list)

    lines = [phrase.state.all]
    for n, (name, info) in enumerate(data.items(), 1):
        lines.append(f"{n}. **{name}** - {len(info['players']) + 1} чел.")
    return await event.reply("\n".join(lines))


@func.new_command(r"/toptreasury$")
@func.new_command(r"/topstate@")
@func.new_command(r"/топказна$")
@func.new_command(r"/топ казна$")
@func.new_command(r"/казна топ$")
@func.new_command(r"/казтоп$")
@func.new_command(r"/ктоп$")
@func.new_command(r"казна топ$")
@func.new_command(r"казтоп$")
async def states_all_top(event: Message) -> Message:
    data = db.states.get_all(sortedby="money")
    if not data:
        return await event.reply(phrase.state.empty_list)

    lines = [phrase.state.toptreasury]
    n = 1
    for name, info in data.items():
        if info["money"] > 0:
            lines.append(f"{n}. **{name}** - {info['money']} амт.")
            n += 1
    return await event.reply("\n".join(lines))


@func.new_command(r"/создать госво\s(.+)")
@func.new_command(r"\+госво\s(.+)")
@func.new_command(r"\+государство\s(.+)")
async def state_make(event: Message) -> Message:
    arg: str = event.pattern_match.group(1).strip().capitalize()

    if len(arg) > 28:
        return await event.reply(phrase.state.too_long)
    if not re.fullmatch(r"^[а-яА-ЯёЁa-zA-Z\- ]+$", arg) or re.fullmatch(
        r"^[\- ]+$", arg
    ):
        return await event.reply(phrase.state.not_valid)

    if db.nicks(id=event.sender_id).get() is None:
        return await event.reply(phrase.state.not_connected)
    if db.states.if_author(event.sender_id):
        return await event.reply(phrase.state.already_author)
    if db.states.if_player(event.sender_id):
        return await event.reply(phrase.state.already_player)
    if db.states.check(arg):
        return await event.reply(phrase.state.already_here)

    if await db.get_money(event.sender_id) < config.cfg.PriceForNewState:
        return await event.reply(phrase.state.require_emerald)

    try:
        button = [
            KeyboardButtonCallback(
                text="🏰 Создать государство",
                data=f"state.m.{event.sender_id}.{arg}".encode(),
            )
        ]
        return await event.reply(phrase.state.warn_make.format(arg), buttons=[button])
    except tgerrors.ButtonDataInvalidError:
        return await event.reply(phrase.state.too_long)


@func.new_command(r"/создать госво$")
@func.new_command(r"\+госво$")
@func.new_command(r"\+государство$")
async def state_make_empty(event: Message) -> Message:
    return await event.reply(phrase.state.no_name)


@func.new_command(r"/вступить(.*)")
@func.new_command(r"вступить(.*)")
@func.new_command(r"/г вступить(.*)")
@func.new_command(r"/г войти(.*)")
async def state_enter(event: Message) -> Message:
    arg: str = event.pattern_match.group(1).strip().capitalize()
    if not arg:
        return await event.reply(phrase.state.no_name)

    if not db.states.find(arg):
        return await event.reply(phrase.state.not_find)

    nick = db.nicks(id=event.sender_id).get()
    if not nick:
        return await event.reply(phrase.state.not_connected)

    if db.states.if_player(event.sender_id) or db.states.if_author(event.sender_id):
        return await event.reply(phrase.state.already_player)

    state = db.state(arg)
    if not state.enter:
        return await event.reply(phrase.state.enter_exit)

    if state.price != 0:
        btn = [
            KeyboardButtonCallback(
                text=f"✅ Оплатить вход ({state.price})",
                data=f"state.pay.{state.name}".encode(),
            )
        ]
        return await event.reply(
            phrase.state.pay_to_enter,
            buttons=ReplyInlineMarkup([KeyboardButtonRow(btn)]),
        )

    players = state.players
    players.append(event.sender_id)
    state.change("players", players)

    await client.send_message(
        entity=config.chats.chat,
        message=phrase.state.new_player.format(state=state.name, player=nick),
        reply_to=config.chats.topics.rp,
    )

    await _check_and_update_tier(state, len(players), state.name)
    return await event.reply(phrase.state.admit.format(state.name))


@func.new_command(r"/state$")
@func.new_command(r"/state@")
@func.new_command(r"/госво(.*)")
@func.new_command(r"/государство(.*)")
async def state_get(event: Message) -> Message:
    arg: str = event.pattern_match.group(1).strip().capitalize()

    if not arg:
        state_name = db.states.if_player(event.sender_id) or db.states.if_author(
            event.sender_id
        )
        if not state_name:
            return await event.reply(phrase.state.no_name)
    else:
        state_name = arg

    if not db.states.find(state_name):
        return await event.reply(phrase.state.not_find)

    state = db.state(state_name)
    enter_val = "Свободный" if state.enter else "Закрыт"
    if state.price > 0:
        enter_val = formatter.value_to_str(state.price, phrase.currency)

    names = await asyncio.gather(
        *[func.get_name(p, minecraft=True) for p in state.players]
    )
    pic_path = pathes.states_pic / f"{state_name}.png"

    return await client.send_message(
        event.chat_id,
        phrase.state.get.format(
            type=phrase.state_types[state.type],
            name=state.name,
            money=formatter.value_to_str(int(state.money), phrase.currency),
            author=db.nicks(id=state.author).get(),
            enter=enter_val,
            desc=state.desc,
            date=state.date,
            players=len(state.players),
            list_players=", ".join(names),
            xyz=state.coordinates,
        ),
        reply_to=event.id,
        link_preview=False,
        file=pic_path if pic_path.exists() else None,
    )


@func.new_command(r"/ливнуть")
@func.new_command(r"/покинуть госво")
@func.new_command(r"/покинуть государство")
@func.new_command(r"выйти из государства")
@func.new_command(r"выйти из госва")
@func.new_command(r"/г покинуть")
@func.new_command(r"/г выйти")
async def state_leave(event: Message) -> Message:
    state_name = db.states.if_player(event.sender_id)
    if not state_name:
        return await event.reply(phrase.state.not_a_member)

    state = db.state(state_name)
    state.players.remove(event.sender_id)
    state.change("players", state.players)

    name_cap = state.name.capitalize()
    await client.send_message(
        entity=config.chats.chat,
        message=phrase.state.leave_player.format(
            state=name_cap, player=db.nicks(id=event.sender_id).get()
        ),
        reply_to=config.chats.topics.rp,
    )

    await _check_and_update_tier(state, len(state.players), name_cap)
    return await event.reply(phrase.state.leave)


@func.new_command(r"/уничтожить госво")
@func.new_command(r"/удалить госво")
@func.new_command(r"/удалить государство")
@func.new_command(r"уничтожить государство")
@func.new_command(r"удалить государство")
@func.new_command(r"/г уничтожить")
@func.new_command(r"/г удалить")
async def state_rem(event: Message) -> Message:
    state_name = db.states.if_author(event.sender_id)
    if not state_name:
        return await event.reply(phrase.state.not_a_author)

    btn = [
        KeyboardButtonCallback(
            text=phrase.state.rem_button,
            data=f"state.remove.{state_name}".encode(),
        )
    ]
    return await event.reply(
        phrase.state.rem_message.format(name=state_name),
        buttons=ReplyInlineMarkup([KeyboardButtonRow(btn)]),
    )


@func.new_command(r"/г описание\s([\s\S]+)")
@func.new_command(r"/о госве\s([\s\S]+)")
@func.new_command(r"/г о госве\s([\s\S]+)")
async def state_desc(event: Message) -> Message:
    state_name = db.states.if_author(event.sender_id)
    if not state_name:
        return await event.reply(phrase.state.not_a_author)

    new_desc: str = event.pattern_match.group(1).strip()
    if len(new_desc) > config.cfg.DescriptionsMaxLen:
        return await event.reply(
            phrase.state.max_len.format(config.cfg.DescriptionsMaxLen)
        )

    db.state(state_name).change("desc", new_desc)
    return await event.reply(phrase.state.change_desc)


@func.new_command(r"/г корды\s(.+)")
@func.new_command(r"/г координаты\s(.+)")
async def state_coords(event: Message) -> Message:
    state_name = db.states.if_author(event.sender_id)
    if not state_name:
        return await event.reply(phrase.state.not_a_author)

    arg: str = event.pattern_match.group(1).strip()
    try:
        coords = [str(int(x)) for x in arg.split()]
        if len(coords) != 3:
            raise ValueError
    except ValueError:
        return await event.reply(phrase.state.howto_change_coords)

    db.state(state_name).change("coordinates", ", ".join(coords))
    return await event.reply(phrase.state.change_coords)


@func.new_command(r"/г входы\s(.+)")
@func.new_command(r"/г вступления\s(.+)")
async def state_enter_arg(event: Message) -> Message:
    state_name = db.states.if_author(event.sender_id)
    if not state_name:
        return await event.reply(phrase.state.not_a_author)

    state = db.state(state_name)
    arg: str = event.pattern_match.group(1).strip().lower()

    if arg in ("да", "+", "разрешить", "открыть", "true", "ok", "ок", "можно"):
        state.change("price", 0)
        state.change("enter", True)
        return await event.reply(phrase.state.enter_open)

    if arg in (
        "нет",
        "-",
        "запретить",
        "закрыть",
        "false",
        "no",
        "нельзя",
        "закрыто",
    ):
        state.change("enter", False)
        return await event.reply(phrase.state.enter_close)

    if arg.isdigit():
        price = int(arg)
        state.change("price", price)
        state.change("enter", True)
        return await event.reply(
            phrase.state.enter_price.format(
                formatter.value_to_str(price, phrase.currency)
            )
        )

    return await event.reply(phrase.state.howto_enter)


@func.new_command(r"/пополнить казну (.+)")
@func.new_command(r"/г пополнить (.+)")
@func.new_command(r"\+казна (.+)")
@func.new_command(r"г пополнить (.+)")
async def state_add_money(event: Message) -> Message:
    state_name = db.states.if_player(event.sender_id) or db.states.if_author(
        event.sender_id
    )
    if not state_name:
        return await event.reply(phrase.state.not_a_member)

    arg: str = event.pattern_match.group(1).strip().lower()
    balance = await db.get_money(event.sender_id)

    if arg in ("все", "всё", "все деньги", "на все"):
        amount = balance
    elif arg.isdigit():
        amount = int(arg)
    else:
        return await event.reply(phrase.state.howto_add_balance)

    if amount < 1:
        return await event.reply(phrase.money.negative_count)
    if amount > balance:
        return await event.reply(
            phrase.money.not_enough.format(
                formatter.value_to_str(balance, phrase.currency)
            )
        )

    db.add_money(event.sender_id, -amount)
    state = db.state(state_name)
    state.change("money", state.money + amount)
    return await event.reply(
        phrase.state.add_treasury.format(
            formatter.value_to_str(amount, phrase.currency)
        )
    )


@func.new_command(r"/забрать из казны (.+)")
@func.new_command(r"/г снять (.+)")
@func.new_command(r"\-казна (.+)")
@func.new_command(r"г снять (.+)")
async def state_rem_money(event: Message) -> Message:
    state_name = db.states.if_author(event.sender_id)
    if not state_name:
        return await event.reply(phrase.state.not_a_author)

    state = db.state(state_name)
    arg: str = event.pattern_match.group(1).strip().lower()

    if arg in ("все", "всё", "все деньги", "на все"):
        amount = state.money
    elif arg.isdigit():
        amount = int(arg)
    else:
        return await event.reply(phrase.state.howto_rem_balance)

    if amount < 1:
        return await event.reply(phrase.money.negative_count)
    if state.money < amount:
        return await event.reply(phrase.state.too_low)

    state.change("money", state.money - amount)
    db.add_money(event.sender_id, amount)
    return await event.reply(
        phrase.state.rem_treasury.format(
            formatter.value_to_str(amount, phrase.currency)
        )
    )


@func.new_command(r"/г кик(.*)")
@func.new_command(r"/г кикнуть(.*)")
@func.new_command(r"/г изгнать(.*)")
@func.new_command(r"/г выгнать(.*)")
@func.new_command(r"/выгнать(.*)")
async def state_kick_user(event: Message) -> Message:
    state_name = db.states.if_author(event.sender_id)
    if not state_name:
        return await event.reply(phrase.state.not_a_author)

    try:
        user_id = await func.get_id(event.pattern_match.group(1).strip())
    except Exception:
        user_id = None
    if user_id is None:
        msg_id = func.get_reply_message_id(event)
        if not msg_id:
            return await event.reply(phrase.player_not_in)
        user_id = await func.get_author_by_msgid(event.chat_id, msg_id)

    state = db.state(state_name)
    if user_id not in state.players:
        return await event.reply(phrase.state.player_not_in)

    state.players.remove(user_id)
    state.change("players", state.players)

    target_name = await func.get_name(user_id, minecraft=True)
    await client.send_message(
        entity=config.chats.chat,
        message=choice(phrase.state.kicked_rp).format(
            state=state_name, player=target_name
        ),
        reply_to=config.chats.topics.rp,
    )

    await _check_and_update_tier(state, len(state.players), state.name.capitalize())
    return await event.reply(phrase.state.kicked.format(target_name))


@func.new_command(r"/г название (.+)")
@func.new_command(r"/г нейм (.+)")
@func.new_command(r"/г name (.+)")
@func.new_command(r"/г переназвать (.+)")
@func.new_command(r"/название госва (.+)")
async def state_rename(event: Message) -> Message:
    state_name = db.states.if_author(event.sender_id)
    if not state_name:
        return await event.reply(phrase.state.not_a_author)

    new_name: str = event.pattern_match.group(1).strip()
    if db.states.check(new_name.capitalize()):
        return await event.reply(phrase.state.already_here)

    btn = [
        KeyboardButtonCallback(
            text=phrase.state.button_rename,
            data=f"state.rn.{new_name}.{event.sender_id}".encode(),
        )
    ]
    return await event.reply(
        phrase.state.rename.format(new_name.capitalize()),
        buttons=[btn],
        parse_mode="html",
    )


@func.new_command(r"/г pic$")
@func.new_command(r"/г картинка$")
@func.new_command(r"/г фото$")
async def state_pic(event: Message) -> Message:
    state_name = db.states.if_author(event.sender_id)
    if not state_name:
        return await event.reply(phrase.state.not_a_author)
    if not event.photo:
        return await event.reply(phrase.state.no_pic)

    await event.download_media(file=pathes.states_pic / f"{state_name}.png")
    return await event.reply(phrase.state.pic_set)
