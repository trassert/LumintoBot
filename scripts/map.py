import asyncio
import json
import os
import random
import socket
import sys

import aiohttp
import asyncmy
import folium  # type: ignore
from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format="<blue>{time:HH:mm:ss}</blue>"
    " <bold>|</bold> <level>{level}</level>"
    " <bold>|</bold> <green>{file}:{function}</green>"
    " <cyan><bold>></bold></cyan> {message}",
    level="INFO",
    colorize=True,
)
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from modules.config import tokens  # noqa: E402

ipinfo = "https://ipinfo.io/{}/json"
ip_api = "http://ip-api.com/json/{}"
ident_v4 = "https://v4.ident.me"
ident_v6 = "https://v6.ident.me"

players = {}

servers = {}

me = []


class MapSQL:
    def __init__(self, host, user, password, database, table):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.table = table
        self.pool = None

    async def connect(self):
        self.pool = await asyncmy.create_pool(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.database,
            autocommit=True,
        )

    async def get(self):
        query = f"SELECT * FROM {self.table}"
        async with self.pool.acquire() as conn, conn.cursor() as cursor:
            await cursor.execute(query)
            result = await cursor.fetchall()
            return result


def randomize_coordinates(data, max_offset=0.02):
    """
    Добавляет небольшое случайное смещение к координатам
    max_offset - максимальное смещение в градусах (по умолчанию до 2 км)
    """
    randomized_lat = data[0] + random.uniform(-max_offset / 2, max_offset / 2)
    randomized_lon = data[1] + random.uniform(-max_offset / 2, max_offset / 2)

    return [randomized_lat, randomized_lon]


async def get_loc(ip_address: str):
    async with aiohttp.ClientSession() as session:

        async def get(ip):
            if "%" in ip:
                ip = ip.split("%")[0]
            try:
                await asyncio.sleep(1)
                async with session.get(ip_api.format(ip)) as response:
                    if response.status == 429:
                        await asyncio.sleep(2)
                        return await get(ip)
                    info = await response.json()
                    logger.info(info)
                    if info["status"] == "success":
                        return [float(info["lat"]), float(info["lon"])]
                    else:
                        raise ValueError
            except Exception:
                await asyncio.sleep(1)
                async with session.get(ipinfo.format(ip)) as response:
                    info = await response.json()
                    logger.info(info)
                    if "status" in info and info["status"] == 404:
                        raise ValueError
                    location = info.get("loc")
                    latitude, longitude = location.split(",")
                    return [float(latitude), float(longitude)]

        try:
            data = await get(ip_address)
        except (
            json.decoder.JSONDecodeError,
            ValueError,
            aiohttp.client_exceptions.ContentTypeError,
        ):
            data = await get(socket.gethostbyname(ip_address))
    return randomize_coordinates(data)


async def main():
    db = MapSQL(
        host=tokens.mysql_map.host,
        user=tokens.mysql_map.user,
        password=tokens.mysql_map.password,
        database=tokens.mysql_map.database,
        table=tokens.mysql_map.table,
    )
    await db.connect()
    for player in await db.get():
        logger.info(f"Info: {player[0]}")
        if not (player[3].startswith("192") or player[3].startswith("127")):
            players[player[1]] = await get_loc(player[3])
    async with aiohttp.ClientSession() as session:
        async with session.get(ident_v6, timeout=5) as response:
            me_ip = await response.text()
            me_loc = await get_loc(me_ip)
            me.append(me_loc[0])
            me.append(me_loc[1])
    map = folium.Map(location=me, zoom_start=5)
    folium.Marker(
        location=me,
        popup="Сервер",
        icon=folium.Icon(color="red", icon="server"),
    ).add_to(map)
    for nick in players:
        if players[nick] is not None:
            folium.Marker(
                location=players[nick],
                popup=nick,
                icon=folium.Icon(color="blue", icon="user"),
            ).add_to(map)
            folium.PolyLine(
                locations=[players[nick], me],
                color="green",
                weight=2.5,
                opacity=0.8,
            ).add_to(map)
    for server in servers:
        if servers[server] is not None:
            folium.Marker(
                location=servers[server],
                popup=server,
                icon=folium.Icon(color="red", icon="server"),
            ).add_to(map)
            folium.PolyLine(
                locations=[servers[server], me],
                color="green",
                weight=2.5,
                opacity=0.8,
            ).add_to(map)
    map.save("map.html")


if __name__ == "__main__":
    try:
        import uvloop

        uvloop.run(main())
    except ModuleNotFoundError:
        logger.warning("Uvloop не установлен!")
        asyncio.run(main())
