import nest_asyncio
import asyncio
import aiohttp
import aiohttp.web

from hashlib import sha1, md5
from datetime import timedelta, datetime
from loguru import logger
from sys import stderr

from modules import vk
from modules import telegram
from modules import db
from modules import ip
from modules import config
from modules import phrase

from modules.formatter import decline_number

nest_asyncio.apply()
logger.remove()
logger.add(
    stderr,
    format='<blue>{time:HH:mm:ss}</blue>'
    ' | <level>{level}</level>'
    ' | <green>{function}</green>'
    ' <cyan>></cyan> {message}',
    level="INFO",
    colorize=True,
)


async def time_to_update_shop():
    def get_last_update():
        last = db.database('shop_update_time')
        if last is not None:
            last = last.replace(
                ':', '-'
            ).replace(
                '.', '-'
            ).replace(
                ' ', '-'
            ).split('-')
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
            db.database('shop_update_time', str(datetime.now()))
            return get_last_update()
    await asyncio.sleep(3)  # ! Для предотвращения блокировки
    while True:
        today = datetime.now()
        last = get_last_update()
        seconds = (
            timedelta(hours=2) - (today - last)
        ).total_seconds()
        'Если время прошло'
        if today - last > timedelta(hours=2):
            theme = db.update_shop()
            logger.info('Изменена тема магазина')
            await telegram.client.send_message(
                config.tokens.bot.chat,
                phrase.shop.update.format(
                    theme=phrase.shop_quotes[theme]['translate']
                )
            )
            db.database('shop_version', db.database('shop_version') + 1)
            db.database(
                'shop_update_time', str(today).split(':')[0]+':00:00.000000'
            )
        logger.info(f'Жду следующий ивент... ({abs(seconds)})')
        await asyncio.sleep(abs(seconds))


async def time_to_rewards():
    def get_last_update():
        last = db.database('stat_update_time')
        if last is not None:
            last = last.replace(
                ':', '-'
            ).replace(
                '.', '-'
            ).replace(
                ' ', '-'
            ).split('-')
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
            db.database('stat_update_time', str(datetime.now()))
            return get_last_update()
    await asyncio.sleep(3)  # ! Для предотвращения блокировки
    while True:
        today = datetime.now()
        last = get_last_update()
        seconds = (
            timedelta(hours=24) - (today - last)
        ).total_seconds()
        'Если время прошло'
        if today - last > timedelta(hours=24):
            day_stat = db.statistic().get_all()
            for top in day_stat:
                tg_id = db.nicks(nick=top[0]).get()
                if tg_id is not None:
                    db.add_money(
                        tg_id,
                        config.coofs.ActiveGift
                    )
                    await telegram.client.send_message(
                        config.tokens.bot.chat,
                        phrase.stat.gift.format(
                            user=top[0],
                            gift=decline_number(config.coofs.ActiveGift, 'изумруд')
                        )
                    )
                    logger.info('Начислен подарок за активность!')
                    break
            db.database(
                'stat_update_time', str(today).split(':')[0]+':00:00.000000'
            )
        logger.info('Жду до следующей награды...')
        await asyncio.sleep(abs(seconds))


async def web_server():
    async def hotmc(request):
        load = await request.post()
        nick = load['nick']
        sign = load['sign']
        time = load['time']
        logger.warning(f'{nick} проголосовал в {time} с хешем {sign}')
        hash = sha1(
            f'{nick}{time}{config.tokens.hotmc}'.encode()
        ).hexdigest()
        if sign != hash:
            logger.warning('Хеш не совпал!')
            logger.warning(f'Должен быть: {sign}')
            logger.warning(f'Имеется: {hash}')
            return aiohttp.web.Response(
                text='Переданные данные не прошли проверку.',
                status=401
            )
        tg_id = db.nicks(nick=nick).get()
        if tg_id is not None:
            db.add_money(tg_id, 10)
            give = phrase.vote_money.format(
                decline_number(10, 'изумруд')
            )
        else:
            give = ''
        await telegram.client.send_message(
            config.tokens.bot.chat,
            phrase.hotmc.format(nick=nick, money=give),
            link_preview=False
        )
        return aiohttp.web.Response(text='ok')

    async def mcservers(request):
        load = await request.post()
        username = load['username']
        sign = load['sign']
        time = load['time']
        logger.warning(f'{username} проголосовал в {time} с хешем {sign}')
        hash = md5(
            f'{username}|{time}|{config.tokens.mcservers}'.encode()
        ).hexdigest()
        if sign != hash:
            logger.warning('Хеш не совпал!')
            logger.warning(f'Должен быть: {sign}')
            logger.warning(f'Имеется: {hash}')
            return aiohttp.web.Response(
                text='Переданные данные не прошли проверку.',
                status=401
            )
        tg_id = db.nicks(nick=username).get()
        if tg_id is not None:
            db.add_money(tg_id, 10)
            give = phrase.vote_money.format(
                decline_number(10, 'изумруд')
            )
        else:
            give = ''
        await telegram.client.send_message(
            config.tokens.bot.chat,
            phrase.servers.format(nick=username, money=give),
            link_preview=False
        )
        return aiohttp.web.Response(text='ok')

    async def minecraft(request):
        if request.query.get('password') != config.tokens.chattohttp:
            logger.info('Неверный пароль (C2HTTP)')
            return aiohttp.web.Response(
                text='Неверный пароль.',
                status=401
            )
        nick = request.query.get('nick')
        # ! message = request.query.get('message') Для будущих нужд
        db.statistic.add(nick=nick)
        logger.info(f'+ соо. от {nick}')
        return aiohttp.web.Response(text='ok')

    async def github(request):
        'Вебхук для гитхаба'
        load = await request.json()
        head = load['head_commit']
        await telegram.client.send_message(
            config.tokens.bot.chat,
            phrase.github.format(
                author=head["author"]["name"],
                message=head["message"],
                url=head["url"]
            ),
            link_preview=False,
            reply_to=config.tokens.topics.updates
        )
        return aiohttp.web.Response(text='ok')

    app = aiohttp.web.Application()
    app.add_routes(
        [
            aiohttp.web.post('/hotmc', hotmc),
            aiohttp.web.post('/servers', mcservers),
            aiohttp.web.post('/github', github),
            aiohttp.web.get('/minecraft', minecraft)
        ]
    )
    runner = aiohttp.web.AppRunner(app)
    try:
        await runner.setup()
        ipv4 = aiohttp.web.TCPSite(runner, '0.0.0.0', 5000)
        ipv6 = aiohttp.web.TCPSite(runner, '::1', 5000)
        await ipv4.start()
        await ipv6.start()
    except asyncio.CancelledError:
        return logger.warning('Веб сервер остановлен')


async def main():
    while True:
        try:
            await web_server()
            await asyncio.gather(
                telegram.client.start(bot_token=config.tokens.bot.token),
                vk.vk.run_polling(),
                time_to_update_shop(),
                ip.observe(),
                time_to_rewards()
            )
        except ConnectionError:
            logger.error('Жду 20 секунд (нет подключения к интернету)')
            await asyncio.sleep(20)


if __name__ == "__main__":
    if sum(db.database('shop_weight').values()) != 100:
        logger.error('Сумма процентов в магазине не равна 100!')
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError, asyncio.CancelledError):
        logger.warning('Закрываю бота!')
