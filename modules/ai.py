import aiohttp
# import genai_proxy as genai

from requests import codes
from loguru import logger

from .formatter import formatter
from . import config


# local_client = genai.Client(api_key="AIzaSyD3eUj98s6DvR7iusI8ncDTATRWNNXwoFE", proxy_string="proxy")
ai_servers = ["trassert0reserve.pythonanywhere.com", "trassert.pythonanywhere.com"]
local_model = "gemini-2.0-flash-001"


async def response(message):
    "Запрос к Google Gemini"
    async with aiohttp.ClientSession() as session:
        for server in ai_servers:
            (
                logger.info(f"Выполняю запрос к AI: {message}")
                if len(message) < 100
                else logger.info(f"Выполняю запрос к AI: {message[:100]}...")
            )
            try:
                async with session.get(
                    url=f"https://{server}/gemini?q={message}&token={config.tokens.google}"
                ) as request:
                    if request.status == codes.ok:
                        return formatter(await request.text())
            except Exception:
                pass
    return None


# async def asyncio_local_generator(message):
#     async for chunk in await local_client.aio.models.generate_content_stream(
#         model=local_model, contents=message
#     ):
#         yield chunk.text