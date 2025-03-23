import aiohttp

from requests import codes
from loguru import logger

from .formatter import formatter
from . import config


ai_servers = [
    'trassert0reserve.pythonanywhere.com',
    'trassert.pythonanywhere.com'
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
                    'https://' +
                    server +
                    '/gemini?q={message}&token={token}'.format(
                        message=message,
                        token=config.tokens.google
                    )
                ) as request:
                    if request.status == codes.ok:
                        return formatter(await request.text())
            except TimeoutError:
                return None
