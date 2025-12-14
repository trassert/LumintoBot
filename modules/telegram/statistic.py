from loguru import logger
from telethon import events
from telethon.tl.custom import Message

from .. import chart, config, db, formatter, mcrcon, pathes, phrase
from .client import client
from .func import get_name
from .global_checks import checks

logger.info(f"Загружен модуль {__name__}!")


@client.on(events.NewMessage(pattern=r"(?i)^/топ соо(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ сообщений(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ в чате(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/актив сервера(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мчат(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мстат(.*)", func=checks))
async def active_check(event: Message):
    arg: str = event.pattern_match.group(1).strip()

    if arg in phrase.all_arg:
        all_data = db.statistic().get_all(all_days=True)
        chart.create_plot(db.statistic().get_raw())
        n = 1
        players = ""
        for data in all_data:
            if n > config.coofs.MaxStatPlayers:
                break
            players += f"{n}. {data[0]} - {data[1]}\n"
            n += 1
        text = phrase.stat.chat.format(time="всё время", text=players)
        return await client.send_file(
            event.chat_id, pathes.chart, caption=text, parse_mode="html"
        )

    try:
        days = int(arg)
        all_data = db.statistic(days=days).get_all()
        if days >= 7:
            chart.create_plot(db.statistic(days=days).get_raw())
            n = 1
            players = ""
            for data in all_data:
                if n > config.coofs.MaxStatPlayers:
                    break
                players += f"{n}. {data[0]} - {data[1]}\n"
                n += 1
            text = phrase.stat.chat.format(
                time=formatter.value_to_str(days, "день"), text=players
            )
            return await client.send_file(
                event.chat_id, pathes.chart, caption=text, parse_mode="html"
            )
    except ValueError:
        all_data = db.statistic().get_all()

    if all_data == []:
        return await event.reply(phrase.stat.empty)

    n = 1
    players = ""
    for data in all_data:
        if n > config.coofs.MaxStatPlayers:
            break
        players += f"{n}. {data[0]} - {data[1]}\n"
        n += 1

    return await event.respond(
        phrase.stat.chat.format(time="день", text=players), parse_mode="html"
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
    for id in all:
        if n > 10:
            break
        text += f"{n}. **{await get_name(id)}**: {all[id]} побед\n"
        n += 1
    return await event.reply(phrase.crocodile.stat.format(text), silent=True)


@client.on(events.NewMessage(pattern=r"(?i)^/банк$", func=checks))
async def all_money(event: Message):
    return await event.reply(
        phrase.money.all_money.format(
            formatter.value_to_str(db.get_all_money(), "изумруд"),
        ),
    )


@client.on(events.NewMessage(pattern=r"(?i)^/топ игроков(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топигроков(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/topplayers(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/playtimetop(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/bestplayers(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/toppt(.*)", func=checks))
async def server_top_list(event: Message):
    arg: str = event.pattern_match.group(1).strip()
    n = 10
    if arg.isdigit():
        n = max(3, min(30, int(arg)))

    try:
        text = [phrase.stat.server]
        async with mcrcon.MinecraftClient(
            host=config.tokens.rcon.host,
            port=config.tokens.rcon.port,
            password=config.tokens.rcon.password,
        ) as rcon:
            for number in range(1, n + 1):
                nickname = (
                    await rcon.send(
                        f"papi parse --null %PTM_nickname_top_{number}%"
                    )
                ).strip()
                playtime = (
                    await rcon.send(
                        f"papi parse --null %PTM_playtime_top_{number}:luminto%"
                    )
                ).strip()
                text.append(f"{number}. {nickname} - {playtime}")

        return await event.reply("\n".join(text))
    except TimeoutError:
        return await event.reply(phrase.server.stopped)
