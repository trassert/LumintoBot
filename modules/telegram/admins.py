from telethon.tl.custom import Message
from telethon import events
from telethon.tl.functions.users import GetFullUserRequest

from .client import client
from .global_checks import checks
from . import func

from .. import phrase, formatter, db, mcrcon
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")


@client.on(events.NewMessage(pattern=r"(?i)^/изменить баланс(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/change balance(.*)", func=checks))
async def add_balance(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN, name=phrase.roles.admin
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
    old = await db.get_money(user.full_user.id)
    db.add_money(user.full_user.id, new)
    await event.reply(
        phrase.money.add_money.format(name=tag, old=old, new=old + new)
    )


@client.on(events.NewMessage(pattern=r"(?i)^\+стафф(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\+staff(.*)", func=checks))
async def add_staff(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.OWNER:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.OWNER, name=phrase.roles.owner
            )
        )
    arg = event.pattern_match.group(1).strip()
    try:
        user = await client(GetFullUserRequest(arg))
        user = user.full_user.id
        tag = await func.get_name(user)
    except (IndexError, ValueError):
        reply_to_msg = event.reply_to_msg_id
        if reply_to_msg:
            reply_message = await event.get_reply_message()
            user = reply_message.sender_id
            tag = await func.get_name(user)
        else:
            return await event.reply(phrase.money.no_people)
    new_role = roles.get(user) + 1
    roles.set(user, new_role)
    return await event.reply(
        phrase.perms.upgrade.format(nick=tag, staff=new_role)
    )


@client.on(events.NewMessage(pattern=r"(?i)^\-staff(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^\-стафф(.*)", func=checks))
async def del_staff(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.OWNER:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.OWNER, name=phrase.roles.owner
            )
        )
    arg = event.pattern_match.group(1).strip()
    try:
        user = await client(GetFullUserRequest(arg))
        user = user.full_user.id
        tag = await func.get_name(user)
    except (IndexError, ValueError):
        reply_to_msg = event.reply_to_msg_id
        if reply_to_msg:
            reply_message = await event.get_reply_message()
            user = reply_message.sender_id
            tag = await func.get_name(user)
        else:
            return await event.reply(phrase.money.no_people)
    new_role = roles.get(user) - 1
    roles.set(user, new_role)
    return await event.reply(
        phrase.perms.downgrade.format(nick=tag, staff=new_role)
    )


@client.on(events.NewMessage(pattern=r"o/(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"v/(.+)", func=checks))
async def vanilla_mcrcon(event: Message):
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN, name=phrase.roles.admin
            )
        )
    command = event.pattern_match.group(1).strip()
    if event.text[0] == "o":
        mode = mcrcon.Oneblock
    else:
        mode = mcrcon.Vanilla
    try:
        async with mode as rcon:
            resp = formatter.rm_colors(await rcon.send(command))
            if len(resp) == 0:
                logger.info("Пустой ответ")
                return await event.reply(phrase.rcon.empty)
            logger.info(f"Ответ команды:\n{resp}")
            if len(resp) > 4096:
                for x in range(0, len(resp), 4096):
                    await event.reply(f"```{resp[x : x + 4096]}```")
                return
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
            phrase.roles.no_perms.format(level=roles.VIP, name=phrase.roles.vip)
        )
    if event.text[0] == "-":
        command = f"nwl remove name {event.pattern_match.group(1).strip()}"
    else:
        command = f"nwl add name {event.pattern_match.group(1).strip()}"
    logger.info(f"Выполняется команда: {command}")
    try:
        async with mcrcon.Vanilla as rcon:
            resp = formatter.rm_colors(await rcon.send(command)).strip()
            logger.info(f"Ответ команды:\n{resp}")
            return await event.reply(
                f"‼️ Команда скоро будет выведена!\n✍🏻 : {resp}"
            )
    except TimeoutError:
        return await event.reply(phrase.server.stopped)
