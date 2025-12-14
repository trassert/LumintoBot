import asyncio

from . import config

sessions = {}  # {user_id: {"gems": int, "death_chance": float, "step": int}}


async def cleanup_session(user_id: int, delay: int = None):
    delay = delay or config.coofs.Mining.Timeout
    await asyncio.sleep(delay)
    sessions.pop(user_id, None)
