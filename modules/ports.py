import aiohttp
import asyncio

async def check_port(ip: str, port: int) -> bool:
    """Проверяет открыт ли порт через API check-host.net"""
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5), headers={"Accept": "application/json"}
    ) as session:
        async with session.get(
            f"https://check-host.net/check-tcp?host={ip}:{port}&max_nodes=1"
        ) as response:
            if response.status == 200:
                data = await response.json()
        await asyncio.sleep(5)
        async with session.get(
            f"https://check-host.net/check-result/{data['request_id']}"
        ) as response:
            answer = await response.json()
            for node in answer:
                if answer[node] is None:
                    pass
                elif "error" in answer[node][0]:
                    return False
                elif "address" in answer[node]:
                    return True
