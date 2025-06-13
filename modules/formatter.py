from pymorphy3 import MorphAnalyzer
import re

morph = MorphAnalyzer()


def value_to_str(number, noun):
    """Склоняет существительное в соответствии с числом.

    Аргументы:
        number: Число.
        noun: Существительное в именительном падеже единственного числа.

    Возвращает:
        Строка с числом и склоненным существительным.
    """

    p = morph.parse(noun)[0]

    if str(number)[0] == "1" and len(str(number)) == 2:
        word = p.inflect({"gent", "plur"}).word
    else:
        match abs(number) % 10:
            case 1:
                word = p.inflect({"nomn", "sing"}).word
            case 2 | 3 | 4:
                word = p.inflect({"gent", "sing"}).word
            case _:
                word = p.inflect({"gent", "plur"}).word
    return f"{number} {word}"


def rm_badtext(text):
    text = re.sub(r"\\boxed\{.*?\}", "", text)
    return text.replace("$", "**").replace("\\cdot", "×")  # ! Экранизация необходима


def rm_colors(text):
    'Удаляет из текста все вхождения "§n", где n - цифра или буква.'
    pattern = r"§[a-zA-Z0-9]"
    return re.sub(pattern, "", text)
