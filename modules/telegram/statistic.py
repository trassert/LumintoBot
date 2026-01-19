from loguru import logger
from telethon.tl.custom import Message

from .. import chart, config, db, formatter, mcrcon, pathes, phrase
from .client import client
from . import func


logger.info(f"Загружен модуль {__name__}!")


@func.new_command(r"/топ соо(.*)")
@func.new_command(r"/топ сообщений(.*)")
@func.new_command(r"/топ в чате(.*)")
@func.new_command(r"/актив сервера(.*)")
@func.new_command(r"/мчат(.*)")
@func.new_command(r"/мстат(.*)")
async def active_check(event: Message):
    arg: str = event.pattern_match.group(1).strip()

    if arg in phrase.all_arg:
        all_data = db.statistic().get_all(all_days=True)
        chart.create_plot(db.statistic().get_raw())
        n = 1
        players = ""
        for data in all_data:
            if n > config.cfg.MaxStatPlayers:
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
                if n > config.cfg.MaxStatPlayers:
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
        if n > config.cfg.MaxStatPlayers:
            break
        players += f"{n}. {data[0]} - {data[1]}\n"
        n += 1

    return await event.respond(
        phrase.stat.chat.format(time="день", text=players), parse_mode="html"
    )


@func.new_command(r"/топ крокодил$")
@func.new_command(r"/топ слова$")
@func.new_command(r"/стат крокодил$")
@func.new_command(r"/стат слова$")
@func.new_command(r"топ крокодила$")
async def crocodile_wins(event: Message):
    all = db.crocodile_stat.get_all()
    text = ""
    n = 1
    for id in all:
        if n > config.cfg.MaxStatPlayers:
            break
        text += f"{n}. **{await func.get_name(id)}**: {all[id]} побед\n"
        n += 1
    return await event.reply(phrase.crocodile.stat.format(text), silent=True)


@func.new_command(r"/банк$")
async def all_money(event: Message):
    return await event.reply(
        phrase.money.all_money.format(
            formatter.value_to_str(await db.get_all_money(), phrase.currency),
        ),
    )


@func.new_command(r"/топ игроков(.*)")
@func.new_command(r"/топигроков(.*)")
@func.new_command(r"/topplayers(.*)")
@func.new_command(r"/playtimetop(.*)")
@func.new_command(r"/bestplayers(.*)")
@func.new_command(r"/toppt(.*)")
async def server_top_list(event: Message):
    arg: str = event.pattern_match.group(1).strip()
    n = config.cfg.MaxStatPlayers
    if arg.isdigit():
        n = max(3, min(30, int(arg)))

    try:
        text = [phrase.stat.server]
        async with mcrcon.Vanilla as rcon:
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
