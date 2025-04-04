from pymorphy3 import MorphAnalyzer
import re

morph = MorphAnalyzer()


def decline_number(number, noun):
    """Склоняет существительное в соответствии с числом.

    Аргументы:
        number: Число.
        noun: Существительное в именительном падеже единственного числа.

    Возвращает:
        Строка с числом и склоненным существительным.
    """

    p = morph.parse(noun)[0]

    if number == 1:
        word = p.inflect({"nomn", "sing"}).word
    elif 2 <= number <= 4:
        word = p.inflect({"gent", "sing"}).word
    else:
        word = p.inflect({"gent", "plur"}).word
    return f"{number} {word}"


def formatter(text):
    text = re.sub(r"\\boxed\{.*?\}", "", text)
    return text.replace("$", "**").replace("\\cdot", "×")  # ! Экранизация необходима


def remove_section_marks(text):
    'Удаляет из текста все вхождения "§n", где n - цифра или буква.'
    pattern = r"§[a-zA-Z0-9]"
    return re.sub(pattern, "", text)
