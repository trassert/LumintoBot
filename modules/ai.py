from google import genai
from google.genai import types, chats

from . import config, phrase
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")

model = config.vars.ai_model

soc_client = genai.Client(
    api_key=config.tokens.ai.social,
    http_options=types.HttpOptions(
        async_client_args={"proxy": config.tokens.proxy},
    ),
)
mc_client = genai.Client(
    api_key=config.tokens.ai.minecraft,
    http_options=types.HttpOptions(
        async_client_args={"proxy": config.tokens.proxy},
    ),
)

chat = soc_client.aio.chats.create(model=model)
crocodile = soc_client.aio.chats.create(model=model)
staff = soc_client.aio.chats.create(model=model)

players = {}


async def get_player_chat(player: str) -> chats.AsyncChat:
    if player in players:
        return players[player]
    players[player] = mc_client.aio.chats.create(model=model)
    await players[player].send_message(
        phrase.ai.minecraft_prompt.format(player)
    )
    return players[player]
