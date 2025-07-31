import folium
import aiohttp
import random
import aiomysql

from .ip import get_loc, ident_v4, ident_v6, dns_servers
from .ai import ai_servers
from .db import MapSQL
from .config import tokens


"Модуль, созданный для отображения карты подключений"
"Необходима база Authy"


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
        self.pool = await aiomysql.create_pool(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.database,
            autocommit=True,
        )

    async def get(self):
        query = f"SELECT * FROM {self.table}"
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                result = await cursor.fetchall()
                return result


def randomize_coordinates(data, max_offset=0.02):
    """
    Добавляет небольшое случайное смещение к координатам
    max_offset - максимальное смещение в градусах (по умолчанию до 2 км)
    """
    randomized_data = {}
    for key in data:
        lat, lon = data[key]
        randomized_lat = lat + random.uniform(-max_offset / 2, max_offset / 2)
        randomized_lon = lon + random.uniform(-max_offset / 2, max_offset / 2)
        randomized_data[key] = [randomized_lat, randomized_lon]
    return randomized_data


async def get_full_map():
    for server in ai_servers:
        servers[server] = await get_loc(server)
    for server in dns_servers:
        servers[server] = await get_loc(server)
    authy = MapSQL(
        host=tokens.mysql_map.host,
        user=tokens.mysql_map.user,
        password=tokens.mysql_map.password,
        database=tokens.mysql_map.database,
        table=tokens.mysql_map.table,
    )
    await authy.connect()
    for player in await authy.get():
        if not (player[2].startswith("192") or player[2].startswith("127")):
            players[player[1]] = await get_loc(player[2])
    async with aiohttp.ClientSession() as session:
        async with session.get(ident_v6, timeout=5) as response:
            me_ip = await response.text()
            me_loc = await get_loc(me_ip)
            me.append(me_loc[0])
            me.append(me_loc[1])
    map = folium.Map(location=me, zoom_start=5)
    folium.Marker(
        location=me, popup="Сервер", icon=folium.Icon(color="red", icon="server")
    ).add_to(map)
    for nick in randomize_coordinates(players):
        if players[nick] is not None:
            folium.Marker(
                location=players[nick],
                popup=nick,
                icon=folium.Icon(color="blue", icon="user"),
            ).add_to(map)
            folium.PolyLine(
                locations=[players[nick], me], color="green", weight=2.5, opacity=0.8
            ).add_to(map)
    for server in servers:
        if servers[server] is not None:
            folium.Marker(
                location=servers[server],
                popup=server,
                icon=folium.Icon(color="red", icon="server"),
            ).add_to(map)
            folium.PolyLine(
                locations=[servers[server], me], color="green", weight=2.5, opacity=0.8
            ).add_to(map)
    map.save("map.html")
