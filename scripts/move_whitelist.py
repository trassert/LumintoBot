import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from modules import mcrcon

players = []


async def main():
    async with mcrcon.MinecraftClient(
        host="127.0.0.1",
        port="25575",
        password="1234",
    ):
        for _player in players:
            pass


asyncio.run(main())
