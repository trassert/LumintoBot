import aiohttp

from bestconfig import Config
from requests import codes
from os import path
from .formatter import formatter
from loguru import logger

tokens = Config(path.join('configs', 'tokens.yml'))

ai_servers = [
    'https://'
    'trassert0reserve.pythonanywhere.com/',

    'https://'
    'trassert.pythonanywhere.com/'
]


async def ai_response(message):
    "Запрос к Google Gemini"
    logger.info(
        f"Выполняю запрос к AI: {message}"
    ) if len(message) < 100 else logger.info(
        f"Выполняю запрос к AI: {message[:100]}..."
    )
    async with aiohttp.ClientSession() as session:
        for server in ai_servers:
            try:
                async with session.get(
                    server+'gemini?q={message}&token={token}'.format(message=message, token=tokens.google)
                ) as request:
                    if request.status == codes.ok:
                        return formatter(await request.text())
            except TimeoutError:
                return None