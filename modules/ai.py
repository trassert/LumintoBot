import aiohttp

from google import genai
from google.genai import types

from requests import codes
from loguru import logger

from . import config, formatter


ai_servers = ["trassert0reserve.pythonanywhere.com", "trassert.pythonanywhere.com"]
model = "gemini-2.0-flash-001"
client = genai.Client(
    api_key=config.tokens.gemini,
    http_options=types.HttpOptions(
        async_client_args={"proxy": config.tokens.proxy},
    ),
)
chat = client.aio.chats.create(model=model)
crocodile = client.aio.chats.create(model=model)
logger.info("ИИ инициализирован")


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
                        return formatter.rm_badtext(await request.text())
            except Exception:
                pass
    return None


# async def get_stream(id: int, message: str):
#     async for chunk in await chat.send_message_stream(f"{id} написал: {message}"):
#         logger.warning(chunk)
#         if chunk.text:
#             yield chunk.text
