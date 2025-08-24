from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

from google import genai
from google.genai import types

from . import config

model = "gemini-2.5-flash-lite-preview-06-17"

client = genai.Client(
    api_key=config.tokens.gemini,
    http_options=types.HttpOptions(
        async_client_args={"proxy": config.tokens.proxy},
    ),
)

chat = client.aio.chats.create(model=model)
crocodile = client.aio.chats.create(model=model)

staff_client = genai.Client(
    api_key=config.tokens.gemini_staff,
    http_options=types.HttpOptions(
        async_client_args={"proxy": config.tokens.proxy},
    ),
)
staff = staff_client.aio.chats.create(model=model)