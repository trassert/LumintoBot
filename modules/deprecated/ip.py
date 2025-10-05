import aiohttp
import asyncio
import json
import socket

from loguru import logger

from . import config, db




dns_servers = ["ns1.reg.ru", "ns2.reg.ru"]



async def get_ip(v6=False):
    async with aiohttp.ClientSession() as session:
        if v6:
            for ident in ident_v6:
                try:
                    logger.info("Получаю IPv6...")
                    async with session.get(ident, timeout=5) as response:
                        response = await response.text()
                        logger.info(f"Получено - {response}")
                        return response
                except Exception:
                    logger.error("Не получается найти IPv6")
                    return db.database("ipv6")
        for ident in ident_v4:
            try:
                logger.info("Получаю IPv4...")
                async with session.get(ident, timeout=5) as response:
                    response = await response.text()
                    logger.info(f"Получено - {response}")
                    return response
            except Exception:
                logger.error("Не получается найти IPv4")
                return db.database("ipv4")


async def change_ip(ipv4, ipv6):
    message = ""
    async with aiohttp.ClientSession() as session:
        "REGru синхронизация"
        try:
            input_data = {
                "username": config.tokens.reg.email,
                "password": config.tokens.reg.password,
                "output_content_type": "plain",
                "domain_name": db.database("host"),
            }
            post = await session.post(
                "https://api.reg.ru/api/regru2/zone/clear", data=input_data
            )
            logger.info(
                json.dumps(
                    await post.json(content_type="text/plain"),
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )
            )
            message += "Связь с REGru выполнена. (1)\n"
        except Exception:
            logger.error("Не удалось связаться с REGru (1)")
            message += "Не удалось связаться с REGru (1)\n"

        try:
            input_data = {
                "username": config.tokens.reg.email,
                "password": config.tokens.reg.password,
                "subdomain": "@",
                "ipaddr": ipv4,
                "output_content_type": "plain",
                "domain_name": db.database("host"),
            }
            post = await session.post(
                "https://api.reg.ru/api/regru2/zone/add_alias", data=input_data
            )
            logger.info(
                json.dumps(
                    await post.json(content_type="text/plain"),
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )
            )
            message += "Связь с REGru выполнена. (2)\n"
        except Exception:
            logger.error("Не удалось связаться с REGru (2)")
            message += "Не удалось связаться с REGru (2)\n"

        try:
            input_data = {
                "username": config.tokens.reg.email,
                "password": config.tokens.reg.password,
                "subdomain": "@",
                "ipaddr": ipv6,
                "output_content_type": "plain",
                "domain_name": db.database("host"),
            }
            post = await session.post(
                "https://api.reg.ru/api/regru2/zone/add_aaaa", data=input_data
            )
            logger.info(
                json.dumps(
                    await post.json(content_type="text/plain"),
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )
            )
            message += "Связь с REGru выполнена. (3)\n"
        except Exception:
            logger.error("Не удалось связаться с REGru (3)")
            message += "Не удалось связаться с REGru (3)\n"

        try:
            input_data = {
                "username": config.tokens.reg.email,
                "password": config.tokens.reg.password,
                "subdomain": db.database("ipv6_subdomain"),
                "ipaddr": ipv6,
                "output_content_type": "plain",
                "domain_name": db.database("host"),
            }
            post = await session.post(
                "https://api.reg.ru/api/regru2/zone/add_aaaa", data=input_data
            )
            logger.info(
                json.dumps(
                    await post.json(content_type="text/plain"),
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )
            )
            message += "Связь с REGru выполнена. (4)\n"
        except Exception:
            logger.error("Не удалось связаться с REGru (4)")
            message += "Не удалось связаться с REGru (4)\n"
        message += f"IP: {ipv4}, V6: {ipv6}"
        return message


async def setup(forced=False):
    v4 = await get_ip()
    v6 = await get_ip(v6=True)
    if (db.database("ipv4") != v4) or (db.database("ipv6") != v6) or forced:
        db.database("ipv4", v4)
        db.database("ipv6", v6)
        return await change_ip(v4, v6)





async def observe():
    logger.info("Жду стабильного подключения..")
    await asyncio.sleep(10)
    while True:
        logger.info("Запуск синхронизации..")
        await setup()
        await asyncio.sleep(config.coofs.IPSleepTime)


# @client.on(events.NewMessage(pattern=r"(?i)^/dns$", func=checks))
# @client.on(events.NewMessage(pattern=r"(?i)^/днс$", func=checks))
# async def tg_dns(event: Message):
#     roles = db.roles()
#     if roles.get(event.sender_id) < roles.ADMIN:
#         return await event.reply(
#             phrase.roles.no_perms.format(level=roles.ADMIN, name=phrase.roles.admin)
#         )
#     return await event.reply(phrase.dns.format(await ip.setup(True)), parse_mode="html")
