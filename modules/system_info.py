import psutil
import platform
import WinTmp
from time import time
from asyncio import sleep



async def get_current_speed():
    start_counters = psutil.net_io_counters()
    await sleep(0.1)
    end_counters = psutil.net_io_counters()
    delta_bytes_sent = end_counters.bytes_sent - start_counters.bytes_sent
    delta_bytes_recv = end_counters.bytes_recv - start_counters.bytes_recv
    upload_speed_mbps = (delta_bytes_sent / 0.1 * 8) / (1000 * 1000)
    download_speed_mbps = (delta_bytes_recv / 0.1 * 8) / (1000 * 1000)
    return [download_speed_mbps, upload_speed_mbps]


async def get_system_info():
    boot_time = psutil.boot_time()
    current_time = time()
    uptime_seconds = current_time - boot_time
    days = int(uptime_seconds / (24 * 3600))
    hours = int((uptime_seconds % (24 * 3600)) / 3600)
    minutes = int((uptime_seconds % 3600) / 60)
    result = ""
    if days > 0:
        result += f"{days} дн. "
    if hours > 0:
        result += f"{hours:02} ч. "
    result += f"{minutes} мин."
    mem = psutil.virtual_memory()
    mem_total = mem.total / (1024 * 1024 * 1024)
    mem_avail = mem.available / (1024 * 1024 * 1024)
    mem_used = mem.used / (1024 * 1024 * 1024)
    temp = WinTmp.CPU_Temps()
    network = await get_current_speed()
    return f"""⚙️ : Информация о хостинге:
    Время работы: {result}
    ОС: {platform.system()} {platform.release()}
    Процессор:
        Частота: {int(psutil.cpu_freq().current)} МГц
        Ядра/Потоки: {psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}
        Загрузка: {psutil.cpu_percent(0.5)} %
        Температура ↑|≈|↓: {round(max(temp))} | {round(sum(temp)/len(temp))} | {round(min(temp))} 
    Память:
        Объём: {mem_total:.1f} ГБ
        Доступно: {mem_avail:.1f} ГБ
        Используется: {mem_used:.1f} ГБ
        Загрузка: {mem.percent} %
    Сеть:
        Загрузка: {network[0]} Мбит/с
        Выгрузка: {network[1]} Мбит/с
    """

if __name__ == "__main__":
    async def main():
        print(await get_system_info())
    asyncio.run(main())