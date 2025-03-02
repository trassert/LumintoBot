import difflib
import json

from os import path

def similar(word, list):
    max_ratio = 0
    max_simular = ''
    for n in list:
        diff = difflib.SequenceMatcher(a=word.lower(), b=n.lower()).ratio()
        if diff > 0.5 and diff > max_ratio:
            max_ratio = diff
            max_simular = n
    return max_simular

def get_enchant_desc(string):
    with open(path.join('db', 'enchants', 'ru.json'), encoding='utf-8') as f:
        ru = json.load(f)
    with open(path.join('db', 'enchants', 'en.json'), encoding='utf-8') as f:
        en = json.load(f)
    data = {**ru, **en}
    enchant = similar(string, list(data.keys()))
    if enchant != '':
        return data[enchant]
    return None
