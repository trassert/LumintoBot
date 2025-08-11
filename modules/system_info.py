import psutil
import platform
import WinTmp
from time import time


def get_system_info():
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
    disk_usage = psutil.disk_usage("/")
    disk_total = disk_usage.total / (1024 * 1024 * 1024)
    disk_used = disk_usage.used / (1024 * 1024 * 1024)
    disk_free = disk_usage.free / (1024 * 1024 * 1024)
    temp = WinTmp.CPU_Temps()
    return f"""⚙️ : Информация о хостинге:
    Время работы: {result}
    ОС: {platform.system()} {platform.release()}
    Процессор:
        Частота: {int(psutil.cpu_freq().current)} МГц
        Ядра/Потоки: {psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}
        Загрузка: {psutil.cpu_percent(0.5)} %
        Температура ↑|≈|↓: {round(max(temp))} | {round(sum(temp)/len(temp))} | {round(min(temp))} 
    Память:
        Общий объем: {mem_total:.1f} ГБ
        Доступно: {mem_avail:.1f} ГБ
        Используется: {mem_used:.1f} ГБ
        Загрузка: {mem.percent} %
    Диск:
        Всего: {disk_total:.1f} ГБ
        Используется: {disk_used:.1f} ГБ
        Свободно: {disk_free:.1f} ГБ
        Загрузка: {disk_usage.percent} %
    """

if __name__ == "__main__":
    print(get_system_info())