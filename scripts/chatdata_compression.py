import glob
import os

import orjson


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi"):
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Ti{suffix}"


total_saved = 0

for path in glob.glob("/media/server/LumintoBot/db/chat_stats/*.json"):
    orig_size = os.path.getsize(path)
    with open(path, "rb") as f:
        data = orjson.loads(f.read())
    compact = orjson.dumps(data)
    new_size = len(compact)
    saved = orig_size - new_size
    total_saved += saved
    with open(path, "wb") as f:
        f.write(compact)
