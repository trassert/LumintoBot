import aiohttp
import asyncio
import json
import socket

from loguru import logger

from .db import database
from . import config


ident_v4 = 'https://v4.ident.me'
ident_v6 = 'https://v6.ident.me'
ipinfo = 'https://ipinfo.io/{}/json'


async def setup(forced=False):
    async with aiohttp.ClientSession() as session:
        async def change_ip(ipv4, ipv6):

            message = ''
            'NOIP синхронизация'
            try:
                async with session.get(
                    f'http://{config.tokens.noip.name}:{config.tokens.noip.password}'
                    '@dynupdate.no-ip.com/'
                    f'nic/update?hostname={database("noip_host")}&myip={ipv4},{ipv6}',
                    headers={
                        "User-Agent": "Trassert MinecraftServer' \
                            '/Windows 11-22000 s3pple@yandex.ru"
                    },
                ) as response:
                    logger.info(await response.text())
                    message += 'Связь с NOIP выполнена.\n'
            except Exception:
                logger.error('Не удалось связаться с NOIP')
                message += 'Не удалось связаться с NOIP\n'

            'REGru синхронизация'
            try:
                input_data = {
                    "username": config.tokens.reg.email,
                    "password": config.tokens.reg.password,
                    "output_content_type": "plain",
                    "domain_name": database('host')
                }
                post = await session.post(
                    'https://api.reg.ru/api/regru2/zone/clear',
                    data=input_data
                )
                logger.info(await post.json(content_type='text/plain'))
                message += 'Связь с REGru выполнена. (1)\n'
            except Exception:
                logger.error('Не удалось связаться с REGru (1)')
                message += 'Не удалось связаться с REGru (1)\n'

            try:
                input_data = {
                    "username": config.tokens.reg.email,
                    "password": config.tokens.reg.password,
                    "subdomain": "@",
                    "ipaddr": v4,
                    "output_content_type": "plain",
                    "domain_name": database('host')
                }
                post = await session.post(
                    'https://api.reg.ru/api/regru2/zone/add_alias',
                    data=input_data
                )
                logger.info(await post.json(content_type='text/plain'))
                message += 'Связь с REGru выполнена. (2)\n'
            except Exception:
                logger.error('Не удалось связаться с REGru (2)')
                message += 'Не удалось связаться с REGru (2)\n'

            try:
                input_data = {
                    "username": config.tokens.reg.email,
                    "password": config.tokens.reg.password,
                    "subdomain": "@",
                    "ipaddr": v6,
                    "output_content_type": "plain",
                    "domain_name": database('host')
                }
                post = await session.post(
                    'https://api.reg.ru/api/regru2/zone/add_aaaa',
                    data=input_data
                )
                logger.info(await post.json(content_type='text/plain'))
                message += 'Связь с REGru выполнена. (3)\n'
            except Exception:
                logger.error('Не удалось связаться с REGru (3)')
                message += 'Не удалось связаться с REGru (3)\n'

            try:
                input_data = {
                    "username": config.tokens.reg.email,
                    "password": config.tokens.reg.password,
                    "subdomain": "v6",
                    "ipaddr": v6,
                    "output_content_type": "plain",
                    "domain_name": database('host')
                }
                post = await session.post(
                    'https://api.reg.ru/api/regru2/zone/add_aaaa',
                    data=input_data
                )
                logger.info(await post.json(content_type='text/plain'))
                message += 'Связь с REGru выполнена. (4)\n'
            except Exception:
                logger.error('Не удалось связаться с REGru (4)')
                message += 'Не удалось связаться с REGru (4)\n'
            message += f'IP: {ipv4}, V6: {ipv6}'
            return message

        try:
            async with session.get(ident_v4, timeout=5) as response:
                v4 = await response.text()
                logger.info(f'Получен IPv4 {v4}')
        except Exception:
            v4 = database('ipv4')
            logger.error('Не могу получить IPv4')
        try:
            async with session.get(ident_v6, timeout=5) as response:
                v6 = await response.text()
                logger.info(f'Получен IPv6 {v6}')
        except Exception:
            v6 = database('ipv6')
            logger.error('Не могу получить IPv4')
        if database('ipv4') != v4 or database('ipv6') != v6 or forced:
            database('ipv4', v4)
            database('ipv6', v6)
            return await change_ip(v4, v6)


async def get_loc(ip_address: str):
    async with aiohttp.ClientSession() as session:
        async def get(ip):
            async with session.get(ipinfo.format(ip)) as response:
                info = await response.json()
                if 'status' in info:
                    if info['status'] == 404:
                        raise ValueError
                return info
        try:
            data = await get(ip_address)
        except (
            json.decoder.JSONDecodeError,
            ValueError,
            aiohttp.client_exceptions.ContentTypeError
        ):
            try:
                data = await get(socket.gethostbyname(ip_address))
            except (
                json.decoder.JSONDecodeError,
                ValueError,
                aiohttp.client_exceptions.ContentTypeError
            ):
                logger.error('Получен невалидный IP')
                return None
    try:
        location = data.get('loc')
        latitude, longitude = location.split(',')
        logger.info(
            '{} > Ш-{}, Д-{}'.format(ip_address, latitude, longitude)
        )
        return [float(latitude), float(longitude)]
    except AttributeError:
        return None


async def observe():
    while True:
        await setup()
        await asyncio.sleep(config.coofs.IPSleepTime)
