import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from modules import mcrcon

players = []


async def main():
    async with mcrcon.MinecraftClient(
        host="127.0.0.1",
        port="25575",
        password="1234",
    ) as rcon:
        for player in players:
            print(f"Ответ команды на игрока {player}:", end=" ")
            print(await rcon.send(f"nwl add name {player}"))


asyncio.run(main())
