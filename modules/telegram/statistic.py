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
        text = phrase.stat.chat.format("всё время")
        all_data = db.statistic().get_all(all_days=True)
        chart.create_plot(db.statistic().get_raw())
    else:
        try:
            days = int(arg)
            text = phrase.stat.chat.format(formatter.value_to_str(days, "день"))
            all_data = db.statistic(days=days).get_all()
        except ValueError:
            text = phrase.stat.chat.format("день")
            all_data = db.statistic().get_all()

    if not all_data:
        return await event.reply(phrase.stat.empty)

    if (arg in phrase.all_arg) or (arg.isdigit() and int(arg) >= 7):
        chart.create_plot(
            db.statistic(days=days if arg.isdigit() else None).get_raw()
        )

    result_text = text + "\n".join(
        f"{n}. {data[0]} - {data[1]}"
        for n, data in enumerate(all_data[: config.coofs.MaxStatPlayers], 1)
    )

    if (arg in phrase.all_arg) or (arg.isdigit() and int(arg) >= 7):
        return await client.send_file(
            event.chat_id, pathes.chart, caption=result_text
        )

    return await event.reply(result_text)


@client.on(events.NewMessage(pattern=r"(?i)^/топ крокодил$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топ слова$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/стат крокодил$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/стат слова$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^топ крокодила$", func=checks))
async def crocodile_wins(event: Message):
    all_stats = db.crocodile_stat.get_all()
    top_10 = list(all_stats.items())[:10]

    text = "\n".join(
        f"{n}. **{await get_name(id)}**: {wins} побед"
        for n, (id, wins) in enumerate(top_10, 1)
    )

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
