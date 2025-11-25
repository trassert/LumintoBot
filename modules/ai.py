import numpy as np
import orjson
import pandas as pd
from google import genai
from typing import List
from google.genai import chats, types
from loguru import logger
from . import config, pathes, phrase

logger.info(f"Загружен модуль {__name__}!")

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

chat = soc_client.aio.chats.create(model=config.vars.AiModel)
crocodile = soc_client.aio.chats.create(model=config.vars.AiModel)
staff = soc_client.aio.chats.create(model=config.vars.AiModel)
players = {}


def get_embeddings() -> list:
    with open(pathes.embeddings, "rb") as f:
        return orjson.loads(f.read())


def create_embeddings_dataframe() -> pd.DataFrame:
    """Создает DataFrame с эмбеддингами документов."""
    df = pd.DataFrame(get_embeddings(), columns=["title", "contents"])
    if df.empty:
        raise ValueError("Embeddings data is empty")
    missing_contents = df["contents"].isna().sum()
    if missing_contents > 0:
        logger.warning(
            f"Found {missing_contents} documents with missing content"
        )
        df = df.dropna(subset=["contents"])
    return df


def compute_document_embeddings(
    df: pd.DataFrame, batch_size: int = 50
) -> pd.DataFrame:
    """Вычисляет эмбеддинги для документов с батчингом для оптимизации."""
    embeddings_list = []
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i : i + batch_size]
        batch_contents = batch["contents"].tolist()
        try:
            batch_response = soc_client.models.embed_content(
                model=config.vars.AiEmbeddings,
                contents=batch_contents,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                ),
            )
            batch_embeddings = [
                embedding.values for embedding in batch_response.embeddings
            ]
            embeddings_list.extend(batch_embeddings)
            logger.debug(
                f"Processed batch {i // batch_size + 1}/{(len(df) - 1) // batch_size + 1}"
            )
        except Exception as e:
            logger.error(f"Error processing batch starting at index {i}: {e}")
            embeddings_list.extend([None] * len(batch_contents))
    df = df.copy()
    df["embeddings"] = embeddings_list
    failed_embeddings = df["embeddings"].isna().sum()
    if failed_embeddings > 0:
        logger.warning(
            f"Failed to compute embeddings for {failed_embeddings} documents"
        )
        df = df.dropna(subset=["embeddings"])
    return df


def get_query_embedding(query: str, model: str) -> np.ndarray:
    """Вычисляет эмбеддинг для запроса."""
    try:
        query_response = soc_client.models.embed_content(
            model=model,
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
            ),
        )
        return np.array(query_response.embeddings[0].values)
    except Exception as e:
        logger.error(f"Error computing query embedding: {e}")
        raise


def find_most_similar_content(
    query_embedding: np.ndarray, document_embeddings: List[np.ndarray]
) -> int:
    """Находит индекс наиболее похожего документа."""
    if not document_embeddings:
        raise ValueError("No document embeddings available")
    doc_embeddings_array = np.array(document_embeddings)
    query_norm = query_embedding / np.linalg.norm(query_embedding)
    doc_norms = np.linalg.norm(doc_embeddings_array, axis=1, keepdims=True)
    doc_embeddings_norm = doc_embeddings_array / doc_norms
    similarities = np.dot(doc_embeddings_norm, query_norm)
    return np.argmax(similarities)


def get_content(
    query: str,
    dataframe: pd.DataFrame,
    model: str,
    similarity_threshold: float = config.coofs.AI.ContentSim,
) -> str:
    """
    Находит наиболее релевантный контент для запроса.
    Args:
        query: Поисковый запрос
        dataframe: DataFrame с документами и эмбеддингами
        model: Модель для эмбеддингов
    Returns:
        Наиболее релевантный контент
    """
    if dataframe.empty:
        raise ValueError("DataFrame is empty")
    if "embeddings" not in dataframe.columns:
        raise ValueError("DataFrame must contain 'embeddings' column")
    query_embedding = get_query_embedding(query, model)
    document_embeddings = dataframe["embeddings"].tolist()
    doc_embeddings_array = np.array(document_embeddings)

    query_norm = query_embedding / np.linalg.norm(query_embedding)
    doc_norms = np.linalg.norm(doc_embeddings_array, axis=1, keepdims=True)
    doc_embeddings_norm = doc_embeddings_array / doc_norms

    similarities = np.dot(doc_embeddings_norm, query_norm)
    best_match_idx = np.argmax(similarities)
    best_similarity = similarities[best_match_idx]

    if best_similarity >= similarity_threshold:
        return f"Контекст: {dataframe['contents'].iloc[best_match_idx]}"
    return ""


async def get_player_chat(player: str) -> chats.AsyncChat:
    if player in players:
        return players[player]
    players[player] = mc_client.aio.chats.create(model=config.vars.AiModel)
    await players[player].send_message(
        phrase.ai.minecraft_prompt.format(player=player),
    )
    return players[player]


embedding_df = compute_document_embeddings(create_embeddings_dataframe())


async def embedding_request(text: str, user: str | int, chat=chat) -> str:
    context = get_content(text, embedding_df, embedding_model)
    logger.info(f"Embedding request: {text}\n{context}")
    return (
        await chat.send_message(
            f"{user}: {text}\n{context}",
            config=types.GenerateContentConfig(
                max_output_tokens=config.coofs.AI.MaxTokens,
            ),
        )
    ).text
