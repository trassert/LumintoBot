import asyncio
from datetime import datetime, timedelta

from loguru import logger

from . import config, db, formatter, phrase, ports
from .telegram.client import client

logger.info(f"Загружен модуль {__name__}!")


async def update_shop():
    logger.info("Обновление магазина..")
    theme = db.update_shop()
    logger.info("Изменена тема магазина")
    return await client.send_message(
        config.chats.chat,
        phrase.shop.update.format(
            emo=phrase.shop_quotes[theme]["emo"],
            theme=phrase.shop_quotes[theme]["translate"],
        ),
    )


async def rewards():
    logger.info("Начисление подарков за активность..")
    day_stat = db.statistic().get_all()
    for top in day_stat:
        tg_id = db.nicks(nick=top[0]).get()
        if tg_id is not None:
            db.add_money(tg_id, config.coofs.ActiveGift)
            logger.info(f"Начислен подарок за активность {top[0]}")
            return await client.send_message(
                config.chats.chat,
                phrase.stat.gift.format(
                    user=top[0],
                    gift=formatter.value_to_str(
                        config.coofs.ActiveGift, "изумруд",
                    ),
                ),
            )


async def remove_states():
    logger.info("Проверяем пустые государства..")
    states = db.states.get_all()
    today = datetime.now()
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


async def port_checks():
    await asyncio.sleep(500)  # Ждать включения сервера
    ip = db.database("host")
    while True:
        try:
            if await ports.check_port(ip, 25565) is False:
                logger.warning("Все ноды ответили о закрытом порту!")
                await client.send_message(
                    entity=config.chats.staff,
                    message=phrase.port.false,
                )
                await asyncio.sleep(900)
            else:
                logger.info("Сервер работает стабильно.")
                await asyncio.sleep(1800)
        except Exception as e:
            logger.error(f"Ошибка при проверке порта: {e}")
            await client.send_message(
                entity=config.chats.staff, message=phrase.port.false,
            )
            await asyncio.sleep(60)
