import aiohttp
import asyncio
import aiohttp.web

from loguru import logger
from hashlib import sha1, md5

from . import config
from . import db
from . import phrase
from .telegram.client import client
from .formatter import decline_number


async def server():
    async def hotmc(request):
        load = await request.post()
        nick = load["nick"]
        sign = load["sign"]
        time = load["time"]
        logger.warning(f"{nick} проголосовал в {time} с хешем {sign}")
        hash = sha1(f"{nick}{time}{config.tokens.hotmc}".encode()).hexdigest()
        if sign != hash:
            logger.warning("Хеш не совпал!")
            logger.warning(f"Должен быть: {sign}")
            logger.warning(f"Имеется: {hash}")
            return aiohttp.web.Response(
                text="Переданные данные не прошли проверку.", status=401
            )
        tg_id = db.nicks(nick=nick).get()
        if tg_id is not None:
            db.add_money(tg_id, 10)
            give = phrase.vote_money.format(decline_number(10, "изумруд"))
        else:
            give = ""
        await client.send_message(
            config.chats.chat,
            phrase.hotmc.format(nick=nick, money=give),
            link_preview=False,
        )
        return aiohttp.web.Response(text="ok")

    async def mcservers(request):
        load = await request.post()
        username = load["username"]
        sign = load["sign"]
        time = load["time"]
        logger.warning(f"{username} проголосовал в {time} с хешем {sign}")
        hash = md5(f"{username}|{time}|{config.tokens.mcservers}".encode()).hexdigest()
        if sign != hash:
            logger.warning("Хеш не совпал!")
            logger.warning(f"Должен быть: {sign}")
            logger.warning(f"Имеется: {hash}")
            return aiohttp.web.Response(
                text="Переданные данные не прошли проверку.", status=401
            )
        tg_id = db.nicks(nick=username).get()
        if tg_id is not None:
            db.add_money(tg_id, 10)
            give = phrase.vote_money.format(decline_number(10, "изумруд"))
        else:
            give = ""
        await client.send_message(
            config.chats.chat,
            phrase.servers.format(nick=username, money=give),
            link_preview=False,
        )
        return aiohttp.web.Response(text="ok")

    async def minecraft(request):
        if request.query.get("password") != config.tokens.chattohttp:
            logger.info("Неверный пароль (C2HTTP)")
            return aiohttp.web.Response(text="Неверный пароль.", status=401)
        nick = request.query.get("nick")
        # ! message = request.query.get('message') Для будущих нужд
        db.statistic.add(nick=nick)
        logger.info(f"+ соо. от {nick}")
        return aiohttp.web.Response(text="ok")

    async def github(request):
        "Вебхук для гитхаба"
        load = await request.json()
        head = load["head_commit"]
        await client.send_message(
            config.chats.chat,
            phrase.github.format(
                author=f'[{head["author"]["name"]}](https://github.com/{head["author"]["name"]})',
                message=head["message"]
            ),
            link_preview=False,
            reply_to=config.chats.topics.updates,
        )
        return aiohttp.web.Response(text="ok")

    app = aiohttp.web.Application()
    app.add_routes(
        [
            aiohttp.web.post("/hotmc", hotmc),
            aiohttp.web.post("/servers", mcservers),
            aiohttp.web.post("/github", github),
            aiohttp.web.get("/minecraft", minecraft),
        ]
    )
    runner = aiohttp.web.AppRunner(app)
    try:
        await runner.setup()
        ipv4 = aiohttp.web.TCPSite(runner, "0.0.0.0", 5000)
        ipv6 = aiohttp.web.TCPSite(runner, "::1", 5000)
        await ipv4.start()
        await ipv6.start()
    except asyncio.CancelledError:
        return logger.warning("Вебхуки остановлены")
