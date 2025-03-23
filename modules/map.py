import folium
import aiohttp
import io

from PIL import Image

from .ip import get_loc, ident_v4
from .ai import ai_servers
from .db import AsyncSQLDatabase
from .config import tokens

'Модуль, созданный для отображения карты подключений'
'Необходима база Authy'


players = {}

servers = {}

me = []


async def get_full_map():
    for server in ai_servers:
        servers[server] = await get_loc(server)
    authy = AsyncSQLDatabase(
        host=tokens.mysql.host,
        user=tokens.mysql.user,
        password=tokens.mysql.password,
        database=tokens.mysql.database,
        table=tokens.mysql.table
    )
    await authy.connect()
    for player in await authy.get():
        players[player[1]] = await get_loc(player[2])
    async with aiohttp.ClientSession() as session:
        async with session.get(ident_v4, timeout=5) as response:
            me_ip = await response.text()
            me_loc = await get_loc(me_ip)
            me.append(me_loc[0])
            me.append(me_loc[1])
    map = folium.Map(location=me, zoom_start=5)
    folium.Marker(
        location=me,
        popup="Сервер",
        icon=folium.Icon(color="red", icon="server")
    ).add_to(map)
    for nick in players:
        if players[nick] is not None:
            folium.Marker(
                location=players[nick],
                popup=nick,
                icon=folium.Icon(color="blue", icon="user")
            ).add_to(map)
            folium.PolyLine(
                locations=[players[nick], me],
                color="green",
                weight=2.5,
                opacity=0.8
            ).add_to(map)
    for server in servers:
        if servers[server] is not None:
            folium.Marker(
                location=servers[server],
                popup=server,
                icon=folium.Icon(color="red", icon="server")
            ).add_to(map)
            folium.PolyLine(
                locations=[servers[server], me],
                color="green",
                weight=2.5,
                opacity=0.8
            ).add_to(map)
    # ! TODO
