import nest_asyncio
import asyncio

from datetime import timedelta, datetime
from loguru import logger
from sys import stderr

from modules import vk
from modules import telegram
from modules import db
from modules import ip
from modules import config
from modules import phrase
from modules import web

from modules.formatter import decline_number

nest_asyncio.apply()
logger.remove()
logger.add(
    stderr,
    format="<blue>{time:HH:mm:ss}</blue>"
    " | <level>{level}</level>"
    " | <green>{function}</green>"
    " <cyan>></cyan> {message}",
    level="INFO",
    colorize=True,
)


async def time_to_update_shop():
    def get_last_update():
        last = db.database("shop_update_time")
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
            db.database("shop_update_time", str(datetime.now()))
            return get_last_update()

    await asyncio.sleep(3)  # ! Для предотвращения блокировки
    while True:
        today = datetime.now()
        last = get_last_update()
        seconds = (timedelta(hours=2) - (today - last)).total_seconds()
        "Если время прошло"
        if today - last > timedelta(hours=2):
            theme = db.update_shop()
            logger.info("Изменена тема магазина")
            await telegram.client.send_message(
                config.chats.chat,
                phrase.shop.update.format(theme=phrase.shop_quotes[theme]["translate"]),
            )
            db.database("shop_version", db.database("shop_version") + 1)
            db.database("shop_update_time", str(today).split(":")[0] + ":00:00.000000")
        logger.info(f"Жду следующий ивент... ({abs(seconds)})")
        await asyncio.sleep(abs(seconds))


async def time_to_rewards():
    def get_last_update():
        last = db.database("stat_update_time")
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
            db.database("stat_update_time", str(datetime.now()))
            return get_last_update()

    await asyncio.sleep(3)  # ! Для предотвращения блокировки
    while True:
        today = datetime.now()
        last = get_last_update()
        seconds = (timedelta(hours=24) - (today - last)).total_seconds()
        "Если время прошло"
        if today - last > timedelta(hours=24):
            day_stat = db.statistic().get_all()
            for top in day_stat:
                tg_id = db.nicks(nick=top[0]).get()
                if tg_id is not None:
                    db.add_money(tg_id, config.coofs.ActiveGift)
                    await telegram.client.send_message(
                        config.chats.chat,
                        phrase.stat.gift.format(
                            user=top[0],
                            gift=decline_number(config.coofs.ActiveGift, "изумруд"),
                        ),
                    )
                    logger.info("Начислен подарок за активность!")
                    break
            db.database("stat_update_time", str(today).split(":")[0] + ":00:00.000000")
        logger.info("Жду до следующей награды...")
        await asyncio.sleep(abs(seconds))


async def main():
    while True:
        try:
            await web.server()
            await asyncio.gather(
                telegram.client.start(bot_token=config.tokens.bot.token),
                vk.client.run_polling(),
                time_to_update_shop(),
                ip.observe(),
                time_to_rewards(),
            )
        except ConnectionError:
            logger.error("Жду 20 секунд (нет подключения к интернету)")
            await asyncio.sleep(20)


if __name__ == "__main__":
    if sum(db.database("shop_weight").values()) != 100:
        logger.error("Сумма процентов в магазине не равна 100!")
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError, asyncio.CancelledError):
        logger.warning("Закрываю бота!")
