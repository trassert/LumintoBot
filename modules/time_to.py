import asyncio

from datetime import timedelta, datetime

from .telegram.client import client
from . import config, phrase, formatter, db
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

def get_last_update(name):
    last = db.database(name)
    if last is not None:
        last = last.replace(":", "-").replace(".", "-").replace(" ", "-").split("-")
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
        db.database(name, str(datetime.now()))
        return get_last_update(name)


async def update_shop():
    await asyncio.sleep(2)  # ! Для предотвращения блокировки
    while True:
        today = datetime.now()
        last = get_last_update("shop_update_time")
        seconds = (timedelta(hours=2) - (today - last)).total_seconds()
        "Если время прошло"
        if today - last > timedelta(hours=2):
            theme = db.update_shop()
            logger.info("Изменена тема магазина")
            await client.send_message(
                config.chats.chat,
                phrase.shop.update.format(
                    emo=phrase.shop_quotes[theme]["emo"],
                    theme=phrase.shop_quotes[theme]["translate"]
                ),
            )
            db.database("shop_version", db.database("shop_version") + 1)
            db.database("shop_update_time", str(today).split(":")[0] + ":00:00.000000")
        logger.info(f"Жду следующий ивент... ({abs(seconds)})")
        await asyncio.sleep(abs(seconds))


async def rewards():
    await asyncio.sleep(2)  # ! Для предотвращения блокировки
    while True:
        today = datetime.now()
        last = get_last_update("stat_update_time")
        seconds = (timedelta(hours=24) - (today - last)).total_seconds()
        "Если время прошло"
        if today - last > timedelta(hours=24):
            day_stat = db.statistic().get_all()
            for top in day_stat:
                tg_id = db.nicks(nick=top[0]).get()
                if tg_id is not None:
                    db.add_money(tg_id, config.coofs.ActiveGift)
                    await client.send_message(
                        config.chats.chat,
                        phrase.stat.gift.format(
                            user=top[0],
                            gift=formatter.value_to_str(
                                config.coofs.ActiveGift, "изумруд"
                            ),
                        ),
                    )
                    logger.info("Начислен подарок за активность!")
                    break
            db.database("stat_update_time", str(today).split(":")[0] + ":00:00.000000")
        logger.info("Жду до следующей награды...")
        await asyncio.sleep(abs(seconds))


async def remove_states():
    await asyncio.sleep(2)  # ! Для предотвращения блокировки
    while True:
        today = datetime.now()
        last = get_last_update("states_update_time")
        seconds = (timedelta(hours=24) - (today - last)).total_seconds()
        "Если время прошло"
        if today - last > timedelta(hours=24):
            states = db.states.get_all()
            for state in states:
                state_info = states[state]
                state_date = list(map(int, state_info["date"].split(".")))
                if (len(state_info["players"]) == 0) and (
                    today - datetime(state_date[0], state_date[1], state_date[2])
                    > timedelta(days=config.coofs.DaysToStatesRemove)
                ):
                    db.add_money(state_info["author"], state_info["money"])
                    db.states.remove(state)
                    logger.warning(f"Государство {state} распалось")
                    await client.send_message(
                        entity=config.chats.chat,
                        message=phrase.state.end.format(state),
                        reply_to=config.chats.topics.rp,
                    )
            db.database(
                "states_update_time", str(today).split(":")[0] + ":00:00.000000"
            )
        logger.info("Жду до следующей проверки государств...")
        await asyncio.sleep(abs(seconds))
