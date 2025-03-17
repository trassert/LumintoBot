import aiohttp
import asyncio

from traceback import format_exc
from loguru import logger

from .db import setting
from . import config


ident_v4 = 'https://v4.ident.me'
ident_v6 = 'https://v6.ident.me'

async def setup_ip(check_set=True):
    '''
    Обновляет динамику.
    Параметр check_set отвечает за принудительность
    '''

    error_text = ''
    try:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(ident_v4, timeout=5) as v4_ident:
                    v4 = await v4_ident.text()
            except Exception:
                v4 = False
                error_text += 'Не могу получить IPv4.\n'
            try:
                async with session.get(
                    "https://v6.ident.me", timeout=5
                ) as v6_ident:
                    v6 = await v6_ident.text()
            except Exception:
                v6 = False
                error_text += 'Не могу получить IPv6.\n'
            if not v4 and not v6:
                return logger.error('Ошибка при получении IP.'
                                    'Сервер может быть недоступен')
            elif v4 == setting('ipv4') and v6 == setting('ipv6') and check_set:
                return logger.warning("IPv4 и IPv6 не изменились")
            if check_set:
                logger.warning("IPv4 или IPv6 изменились")
            else:
                logger.warning('Принудительно выставляю IP')
            setting('ipv4', v4)
            setting('ipv6', v6)

            "NOIP синхронизация"
            async with session.get(
                f'http://{config.tokens.noip.name}:{config.tokens.noip.password}'
                '@dynupdate.no-ip.com/'
                f'nic/update?hostname={setting("noip_host")}&myip={v4},{v6}',
                headers={
                    "User-Agent": "Trassert MinecraftServer' \
                        '/Windows 11-22000 s3pple@yandex.ru"
                },
            ) as noip:
                noip = await noip.text()
                logger.info(noip)

            "REGru синхронизация"
            input_data = {
                "username": config.tokens.reg.email,
                "password": config.tokens.reg.password,
                "output_content_type": "plain",
                "domain_name": setting('host')
            }
            post = await session.post(
                'https://api.reg.ru/api/regru2/zone/clear',
                data=input_data
            )
            out = await post.json(content_type='text/plain')
            logger.warning(out)

            input_data = {
                "username": config.tokens.reg.email,
                "password": config.tokens.reg.password,
                "subdomain": "@",
                "ipaddr": v4,
                "output_content_type": "plain",
                "domain_name": setting('host')
            }
            post = await session.post(
                'https://api.reg.ru/api/regru2/zone/add_alias',
                data=input_data
            )
            out = await post.json(content_type='text/plain')
            logger.warning(out)

            input_data = {
                "username": config.tokens.reg.email,
                "password": config.tokens.reg.password,
                "subdomain": "@",
                "ipaddr": v6,
                "output_content_type": "plain",
                "domain_name": setting('host')
            }
            post = await session.post(
                'https://api.reg.ru/api/regru2/zone/add_aaaa',
                data=input_data
            )
            out = await post.json(content_type='text/plain')
            logger.warning(out)

            input_data = {
                "username": config.tokens.reg.email,
                "password": config.tokens.reg.password,
                "subdomain": "v6",
                "ipaddr": v6,
                "output_content_type": "plain",
                "domain_name": setting('host')
            }
            post = await session.post(
                'https://api.reg.ru/api/regru2/zone/add_aaaa',
                data=input_data
            )
            out = await post.json(content_type='text/plain')
            logger.warning(out)
    except Exception:
        error_text += format_exc()
        logger.error(error_text)
    return error_text if error_text != '' else noip


async def setup(forced=False):
    async with aiohttp.ClientSession() as session:
        async def change_ip(ipv4, ipv6):

            message = ''
            'NOIP синхронизация'
            try:
                async with session.get(
                    f'http://{config.tokens.noip.name}:{config.tokens.noip.password}'
                    '@dynupdate.no-ip.com/'
                    f'nic/update?hostname={setting("noip_host")}&myip={ipv4},{ipv6}',
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
                    "domain_name": setting('host')
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
                    "domain_name": setting('host')
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
                    "domain_name": setting('host')
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
                    "domain_name": setting('host')
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
                logger.info(f'Новый IPv4 {v4}')
        except Exception:
            v4 = setting('ipv4')
            logger.error('Не могу получить IPv4')
        try:
            async with session.get(ident_v6, timeout=5) as response:
                v6 = await response.text()
                logger.info(f'Новый IPv4 {v6}')
        except Exception:
            v6 = setting('ipv6')
            logger.error('Не могу получить IPv4')
        if setting('ipv4') != v4 or setting('ipv6') != v6 or forced:
            setting('ipv4', v4)
            setting('ipv6', v6)
            return await change_ip(v4, v6)


async def observe():
    while True:
        await setup()
        await asyncio.sleep(config.coofs.IPSleepTime)