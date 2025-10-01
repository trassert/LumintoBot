import aiohttp
import asyncio


def check_nodes_status(data):
    try:
        return any("address" in item for node in data.values() for item in node)
    except TypeError:
        return True


async def check_port(ip: str, port: int) -> bool:
    """Проверяет открыт ли порт через API check-host.net"""
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={"Accept": "application/json"},
    ) as session:
        async with session.get(
            f"https://check-host.net/check-tcp?host={ip}:{port}&max_nodes=2"
        ) as response:
            if response.status == 200:
                data = await response.json()
        await asyncio.sleep(5)
        async with session.get(
            f"https://check-host.net/check-result/{data['request_id']}"
        ) as response:
            return check_nodes_status(await response.json())
