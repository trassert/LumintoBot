from google import genai
from google.genai import types, chats

from . import config
from loguru import logger

logger.info(f"Загружен модуль {__name__}!")
model = "gemini-2.5-flash-lite"

tgclient = genai.Client(
    api_key=config.tokens.gemini,
    http_options=types.HttpOptions(
        async_client_args={"proxy": config.tokens.proxy},
    ),
)

chat = tgclient.aio.chats.create(model=model)
crocodile = tgclient.aio.chats.create(model=model)
staff = tgclient.aio.chats.create(model=model)

mcclient = genai.Client(
    api_key=config.tokens.gemini_staff,
    http_options=types.HttpOptions(
        async_client_args={"proxy": config.tokens.proxy},
    ),
)
players = {}


async def get_player_chat(player) -> chats.AsyncChat:
    if player in players:
        return players[player]
    players[player] = mcclient.aio.chats.create(model=model)
    await players[player].send_message(f"Ты — Люма, ИИ бот-помощник в Майнкрафте. Ты общаешься с игроком {player}. Общайся вежливо и с заботой. Твои ответы должны быть короткие, но не односложные, и не стоит упоминать ник каждый раз. Пиши ОК, если всё поняла.")
    return players[player]
