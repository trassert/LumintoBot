import aiohttp

from time import time

from . import phrase
from .ai import ai_servers


async def ping(arg, timestamp, vk=False) -> str:
    ping = round(time() - timestamp, 2)
    if ping < 0:
        ping = phrase.ping.min
    else:
        ping = f"за {str(ping)} сек."
    all_servers_ping = []
    if arg in [
        "all",
        "подробно",
        "подробный",
        "полн",
        "полный",
        "весь",
        "ии",
        "фулл",
        "full",
    ]:
        async with aiohttp.ClientSession() as session:
            n = 1
            for server in ai_servers:
                timestamp = time()
                async with session.get("https://" + server + "/") as request:
                    try:
                        if await request.text() == "ok":
                            server_ping = round(time() - timestamp, 2)
                            if server_ping > 0:
                                server_ping = f"за {server_ping} сек."
                            else:
                                server_ping = phrase.ping.min
                            all_servers_ping.append(
                                f"\n🌐 : Сервер {n} ответил {server_ping}"
                            )
                        else:
                            all_servers_ping.append(f"\n❌ : Сервер {n} - Ошибка!")
                    except TimeoutError:
                        all_servers_ping.append(f"❌ : Сервер {n} - Нет подключения!")
                n += 1
    elif arg != "":
        return
    text = phrase.ping.set.format(ping) + "".join(all_servers_ping)
    if vk:
        text = text.replace("**", "")
    return text
