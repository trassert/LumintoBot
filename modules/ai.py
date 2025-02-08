import logging
import aiohttp

from bestconfig import Config
from requests import codes
from os import path
from .formatter import formatter

logger = logging.getLogger(__name__)

tokens = Config(path.join('configs', 'tokens.yml'))

servers = [
    'https://'
    '8f00b559-ee6f-4441-88f8-768ff444297d-00-t3sgt8jrx79r.'
    'pike.replit.dev'
    '/gemini?q={message}&token={token}',

    'https://'
    'trassert0reserve.pythonanywhere.com'
    '/gemini?q={message}&token={token}',

    'https://'
    'trassert.pythonanywhere.com'
    '/gemini?q={message}&token={token}'
]


async def ai_response(message):
    "Запрос к Google Gemini"
    logger.info(
        f"Выполняю запрос к AI: {message}"
    ) if len(message) < 100 else logger.info(
        f"Выполняю запрос к AI: {message[:100]}..."
    )
    async with aiohttp.ClientSession() as session:
        for server in servers:
            try:
                async with session.get(
                    server.format(message=message, token=tokens.google)
                ) as request:
                    if request.status == codes.ok:
                        return await formatter(request.text())
            except TimeoutError:
                return None