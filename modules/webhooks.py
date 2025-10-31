import asyncio
from hashlib import md5, sha1

import aiohttp
import aiohttp.web
from loguru import logger

from . import ai, config, db, formatter, phrase
from .telegram import func
from .telegram.client import client

logger.info(f"Загружен модуль {__name__}!")


async def server():
    async def status(request: aiohttp.web.Request):
        return aiohttp.web.Response(text="ok")

    async def hotmc(request: aiohttp.web.Request):
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
                text="Переданные данные не прошли проверку.", status=401,
            )
        tg_id = db.nicks(nick=nick).get()
        if tg_id is not None:
            db.add_money(tg_id, 10)
            give = phrase.vote_money.format(
                formatter.value_to_str(10, "изумруд"),
            )
        else:
            give = ""
        await client.send_message(
            config.chats.chat,
            phrase.hotmc.format(nick=nick, money=give),
            link_preview=False,
        )
        return aiohttp.web.Response(text="ok")

    async def mcservers(request: aiohttp.web.Request):
        load = await request.post()
        username = load["username"]
        sign = load["sign"]
        time = load["time"]
        logger.warning(f"{username} проголосовал в {time} с хешем {sign}")
        hash = md5(
            f"{username}|{time}|{config.tokens.mcservers}".encode(),
        ).hexdigest()
        if sign != hash:
            logger.warning("Хеш не совпал!")
            logger.warning(f"Должен быть: {sign}")
            logger.warning(f"Имеется: {hash}")
            return aiohttp.web.Response(
                text="Переданные данные не прошли проверку.", status=401,
            )
        tg_id = db.nicks(nick=username).get()
        if tg_id is not None:
            db.add_money(tg_id, 10)
            give = phrase.vote_money.format(
                formatter.value_to_str(10, "изумруд"),
            )
        else:
            give = ""
        await client.send_message(
            config.chats.chat,
            phrase.servers.format(nick=username, money=give),
            link_preview=False,
        )
        return aiohttp.web.Response(text="ok")

    async def minecraft(request: aiohttp.web.Request):
        if request.query.get("password") != config.tokens.chattohttp:
            logger.info("Неверный пароль (C2HTTP)")
            return aiohttp.web.Response(text="Неверный пароль.", status=401)
        nick = request.query.get("nick")
        # message = request.query.get('message') Для будущих нужд
        db.statistic.add(nick=nick)
        logger.debug(f"+ соо. от {nick}")
        return aiohttp.web.Response(text="ok")

    async def bank(request: aiohttp.web.Request):
        if request.query.get("key") != config.tokens.bankplugin:
            logger.warning("Неверный пароль (BankPlugin)")
            return aiohttp.web.Response(text="Неверный пароль.", status=401)
        playerid = db.nicks(nick=request.query.get("player")).get()
        if playerid is None:
            logger.warning("Неверный игрок (BankPlugin)")
            return aiohttp.web.Response(text="Неверный игрок.", status=401)
        amount = int(request.query.get("amount"))
        if not amount > 0 and not amount < 67:
            logger.warning("Неверное количество (BankPlugin)")
            return aiohttp.web.Response(text="Неверное количество.", status=401)
        await client.send_message(
            config.chats.chat,
            phrase.mcadd_money.format(
                player=await func.get_name(playerid, minecraft=True),
                amount=formatter.value_to_str(amount, "изумруд"),
            ),
        )
        db.add_money(playerid, amount)
        logger.info(f"[Bank] Переведено {amount} изумрудов на счет {playerid}")
        return aiohttp.web.Response(text="ok")

    async def genai(request: aiohttp.web.Request):
        player = request.query.get("player")
        text = request.query.get("text")
        logger.info(f"[AI] {player} > {text}")
        chat = await ai.get_player_chat(player)
        return aiohttp.web.Response(text=(await chat.send_message(text)).text)

    async def github(request: aiohttp.web.Request):
        load: dict = await request.json()
        commits = load.get("commits")
        if commits is None:
            return aiohttp.web.Response(text="Неверный запрос", status=400)
        for head in commits:
            logger.info(f"Обновление! Репо {load['repository']['name']}")
            await client.send_message(
                config.chats.chat,
                phrase.github.update.format(
                    author=f"[{head['author']['name']}](https://github.com/{head['author']['name']})",
                    message=head["message"],
                    link=head["url"],
                    repo=f"[{load['repository']['name']}](https://github.com/{load['repository']['full_name']})",
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
            aiohttp.web.get("/bank", bank),
            aiohttp.web.get("/genai", genai),
            aiohttp.web.get("/", status),
        ],
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
