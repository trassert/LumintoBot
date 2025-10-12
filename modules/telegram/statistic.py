from telethon.tl.custom import Message
from telethon import events

from .client import client
from .global_checks import checks
from .func import get_name

from .. import config, phrase, db, pathes, formatter, chart, mcrcon
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")


@client.on(events.NewMessage(pattern=r"(?i)^/топ соо(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ сообщений(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ в чате(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/актив сервера(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мчат(.*)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/мстат(.*)", func=checks))
async def active_check(event: Message):
    arg = event.pattern_match.group(1).strip()
    if arg in phrase.all_arg:
        text = phrase.stat.chat.format("всё время")
        all_data = db.statistic().get_all(all_days=True)
        chart.create_plot(db.statistic().get_raw())
        n = 1
        for data in all_data:
            if n > config.coofs.MaxStatPlayers:
                break
            text += f"{n}. {data[0]} - {data[1]}\n"
            n += 1
        return await client.send_file(event.chat_id, pathes.chart, caption=text)
    try:
        days = int(arg)
        text = phrase.stat.chat.format(formatter.value_to_str(days, "день"))
        all_data = db.statistic(days=days).get_all()
        if days >= 7:
            chart.create_plot(db.statistic(days=days).get_raw())
            n = 1
            for data in all_data:
                if n > config.coofs.MaxStatPlayers:
                    break
                text += f"{n}. {data[0]} - {data[1]}\n"
                n += 1
            return await client.send_file(
                event.chat_id, pathes.chart, caption=text
            )
    except ValueError:
        text = phrase.stat.chat.format("день")
        all_data = db.statistic().get_all()
    if all_data == []:
        return await event.reply(phrase.stat.empty)
    n = 1
    for data in all_data:
        if n > config.coofs.MaxStatPlayers:
            break
        text += f"{n}. {data[0]} - {data[1]}\n"
        n += 1
    return await event.reply(text)


@client.on(events.NewMessage(pattern=r"(?i)^/топ крокодил$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ слова$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/стат крокодил$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/стат слова$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^топ крокодила$", func=checks))
async def crocodile_wins(event: Message):
    all = db.crocodile_stat.get_all()
    text = ""
    n = 1
    for id in all.keys():
        if n > 10:
            break
        text += f"{n}. **{await get_name(id)}**: {all[id]} побед\n"
        n += 1
    return await event.reply(phrase.crocodile.stat.format(text), silent=True)


@client.on(events.NewMessage(pattern=r"(?i)^/банк$", func=checks))
async def all_money(event: Message):
    return await event.reply(
        phrase.money.all_money.format(
            formatter.value_to_str(db.get_all_money(), "изумруд")
        )
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
        try:
            n = max(3, min(30, int(arg)))
        except Exception:
            pass
    try:
        text = [phrase.stat.server]
        async with mcrcon.MinecraftClient(
            host=config.tokens.rcon.host,
            port=config.tokens.rcon.port,
            password=config.tokens.rcon.password,
        ) as rcon:
            for number in range(1, n+1):
                text.append(
                    "{number}. {nickname} - {playtime}".format(
                        number=number,
                        nickname=(
                            await rcon.send(
                                f"papi parse --null %PTM_nickname_top_{number}%"
                            )
                        ).strip(),
                        playtime=(
                            await rcon.send(
                                f"papi parse --null %PTM_playtime_top_{number}:luminto%"
                            )
                        ).strip(),
                    )
                )
        return await event.reply("\n".join(text))
    except TimeoutError:
        return await event.reply(phrase.server.stopped)
