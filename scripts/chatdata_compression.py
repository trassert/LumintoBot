from pathlib import Path

import orjson


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi"):
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Ti{suffix}"


total_saved = 0
stats_dir = Path("/media/server/LumintoBot/db/chat_stats")

for path in stats_dir.glob("*.json"):
    orig_size = path.stat().st_size
    data = orjson.loads(path.read_bytes())
    compact = orjson.dumps(data)
    new_size = len(compact)
    saved = orig_size - new_size
    total_saved += saved
    path.write_bytes(compact)