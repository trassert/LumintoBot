import numpy as np
import orjson
import pandas as pd
from google import genai
from google.genai import chats, types
from loguru import logger

from . import config, pathes, phrase

logger.info(f"Загружен модуль {__name__}!")

model = config.vars.ai_model
embedding_model = "gemini-embedding-001"

soc_client = genai.Client(
    api_key=config.tokens.ai.social,
    http_options=types.HttpOptions(
        async_client_args={"proxy": config.tokens.proxy},
        client_args={"proxy": config.tokens.proxy},
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


def get_embeddings() -> list:
    with open(pathes.embeddings, "rb") as f:
        return orjson.loads(f.read())


embeddings_df = pd.DataFrame(get_embeddings())
embeddings_df.columns = ["title", "contents"]
embeddings_df["embeddings"] = embeddings_df.apply(
    lambda x: soc_client.models.embed_content(
        model=embedding_model,
        contents=(x["contents"]),
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
        ),
    )
    .embeddings[0]
    .values,
    axis=1,
)


def get_content(query: str, dataframe: pd.DataFrame, model: str) -> str:
    query_embedding = soc_client.models.embed_content(
        model=model,
        contents=query,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
        ),
    )

    dot_products = np.dot(
        np.stack(dataframe.embeddings), query_embedding.embeddings[0].values,
    )

    best_passage_index = np.argmax(dot_products)

    return dataframe.contents.iloc[best_passage_index]


async def get_player_chat(player: str) -> chats.AsyncChat:
    if player in players:
        return players[player]
    players[player] = mc_client.aio.chats.create(model=model)
    await players[player].send_message(
        phrase.ai.minecraft_prompt.format(player=player),
    )
    return players[player]


async def embedding_request(text: str, user: str | int, chat=chat) -> str:
    return (
        await chat.send_message(
            f"{user}: {text}\nКонтекст: {get_content(text, embeddings_df, embedding_model)}",
        )
    ).text
