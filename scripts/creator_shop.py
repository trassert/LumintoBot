import json

"Не вызывается. Только для создания json файла"

with open("items.txt", encoding="utf-8") as f:
    r = f.read().split("\n")

list = []
n = 0
for x in r:
    if n % 2 == 0:
        list.append(x)
    else:
        list[-1] = list[-1] + "~" + x
    n += 1

name = "blacksmith"

with open("press_shop.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    data[name] = {}


for x in list:
    data[name][x.split("~")[0]] = {"name": 0, "value": 0, "price": 5}

with open("press_shop.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
