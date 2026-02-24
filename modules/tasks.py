from datetime import datetime, timedelta

from loguru import logger

from . import config, db, formatter, phrase
from .telegram.client import client

logger.info(f"Загружен модуль {__name__}!")


async def update_shop():
    logger.info("Обновление магазина..")
    try:
        await db.shop_version(update=True)
        theme = await db.update_shop()

        await client.send_message(
            config.chats.chat,
            phrase.shop.update.format(
                emo=phrase.shop_quotes[theme]["emo"],
                theme=phrase.shop_quotes[theme]["translate"],
            ),
        )
        logger.info("Изменена тема магазина")
    except Exception:
        logger.exception("Ошибка при обновлении шопа")


async def rewards():
    logger.info("Начисление подарков за активность..")
    day_stat = db.statistic().get_all()
    for top in day_stat:
        tg_id = db.nicks(nick=top[0]).get()
        if tg_id is not None:
            await db.add_money(tg_id, config.cfg.ActiveGift)
            logger.info(f"Начислен подарок за активность {top[0]}")
            return await client.send_message(
                config.chats.chat,
                phrase.stat.gift.format(
                    user=top[0],
                    gift=formatter.value_to_str(
                        config.cfg.ActiveGift,
                        phrase.currency,
                    ),
                ),
            )
    return None


async def remove_states() -> None:
    logger.info("Проверяем пустые государства..")
    states = db.states.get_all()
    today = datetime.now()
    for state in states:
        state_info = states[state]
        state_date = list(map(int, state_info["date"].split(".")))
        if (len(state_info["players"]) == 0) and (
            today - datetime(state_date[0], state_date[1], state_date[2])
            > timedelta(days=config.cfg.DaysToStatesRemove)
        ):
            await db.add_money(state_info["author"], state_info["money"])
            db.states.remove(state)
            logger.warning(f"Государство {state} распалось")
            await client.send_message(
                entity=config.chats.chat,
                message=phrase.state.end.format(state),
                reply_to=config.chats.topics.rp,
            )
