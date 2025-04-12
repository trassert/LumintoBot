import psutil
import platform
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
    cpu_freq = int(psutil.cpu_freq().current)
    cpu_cores_phys = psutil.cpu_count(logical=False)
    cpu_cores_log = psutil.cpu_count(logical=True)
    cpu_percent = psutil.cpu_percent()
    mem_total = psutil.virtual_memory().total / (1024 * 1024 * 1024)
    mem_avail = psutil.virtual_memory().available / (1024 * 1024 * 1024)
    mem_used = psutil.virtual_memory().used / (1024 * 1024 * 1024)
    mem_percent = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage("/")
    disk_total = disk_usage.total / (1024 * 1024 * 1024)
    disk_used = disk_usage.used / (1024 * 1024 * 1024)
    disk_free = disk_usage.free / (1024 * 1024 * 1024)
    disk_percent = disk_usage.percent
    os = platform.system()
    return f"""⚙️ : Информация о хостинге:
    Время работы: {result}
    ОС: {platform.system()} {platform.release()}
    Процессор:
        Частота: {cpu_freq} МГц
        Ядра/Потоки: {cpu_cores_phys}/{cpu_cores_log}
        Загрузка: {cpu_percent} %
    Память:
        Общий объем: {mem_total:.1f} ГБ
        Доступно: {mem_avail:.1f} ГБ
        Используется: {mem_used:.1f} ГБ
        Загрузка: {mem_percent} %
    Диск:
        Всего: {disk_total:.1f} ГБ
        Используется: {disk_used:.1f} ГБ
        Свободно: {disk_free:.1f} ГБ
        Загрузка: {disk_percent} %
    """
