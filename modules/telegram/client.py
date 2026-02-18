import socks
from loguru import logger
from telethon import TelegramClient, types
from telethon.extensions import markdown

from .. import config, pathes

logger.info(f"Загружен модуль {__name__}!")


class CustomMarkdown:
    """
    Костыль для работы с маркдауном.
    Не работает нормально жирность с цитатами, keep in mind!
    Поддерживает:
    - Цитата >
    - Сокр. цитата >>
    - Спойлер [text] (spoiler)
    - Прем. эмодзи [text] (emoji/123456789)
    """

    @staticmethod
    def parse(text):
        if ("> " not in text) or (
            not any(line.startswith(("> ", ">> ")) for line in text.split("\n"))
        ):
            text, entities = markdown.parse(text)
        else:
            lines = text.split("\n")
            new_lines = []
            blockquotes = []
            offset = 0

            for line in lines:
                if line.startswith(">> "):
                    clean = line[3:]
                    collapsed = True
                elif line.startswith("> "):
                    clean = line[2:]
                    collapsed = False
                else:
                    new_lines.append(line)
                    offset += len(line) + 1
                    continue

                ln = len(clean)
                if ln > 0:
                    blockquotes.append((offset, ln, collapsed))
                new_lines.append(clean)
                offset += ln + 1

            text = "\n".join(new_lines)
            text, entities = markdown.parse(text)

            for off, length, collapsed in reversed(blockquotes):
                entities.append(
                    types.MessageEntityBlockquote(
                        offset=off, length=length, collapsed=collapsed or None
                    )
                )

        for i, e in enumerate(entities):
            if isinstance(e, types.MessageEntityTextUrl):
                if e.url == "spoiler":
                    entities[i] = types.MessageEntitySpoiler(e.offset, e.length)
                elif e.url.startswith("emoji/"):
                    entities[i] = types.MessageEntityCustomEmoji(
                        e.offset, e.length, int(e.url.split("/", 1)[1])
                    )
        return text, entities

    @staticmethod
    def unparse(text, entities):
        filtered = [
            e
            for e in (entities or [])
            if not isinstance(e, types.MessageEntityBlockquote)
        ]
        for i, e in enumerate(filtered):
            if isinstance(e, types.MessageEntityCustomEmoji):
                filtered[i] = types.MessageEntityTextUrl(
                    e.offset, e.length, f"emoji/{e.document_id}"
                )
            elif isinstance(e, types.MessageEntitySpoiler):
                filtered[i] = types.MessageEntityTextUrl(e.offset, e.length, "spoiler")
        return markdown.unparse(text, filtered)


def get_proxy() -> tuple:
    """
    Выдаёт формат прокси.
    1. Тип (SOCKS5 по умолчанию)
    2. Айпишник прокси (str)
    3. Порт прокси (int)
    4. Авторизация (bool)
    5. Логин (str)
    6. Пароль (str)
    В TelegramClient формат прокси неверный,
        если ставить как там - будет ошибка.
    """
    if config.tokens.proxy.enabled is False:
        return None
    return (
        socks.SOCKS5,
        config.tokens.proxy.host,
        config.tokens.proxy.port,
        config.tokens.proxy.auth,
        config.tokens.proxy.login,
        config.tokens.proxy.password,
    )


client = TelegramClient(
    session=pathes.bot,
    api_id=config.tokens.bot.id,
    api_hash=config.tokens.bot.hash,
    device_model="Bot",
    system_version="4.16.30-vxCUSTOM",
    lang_code="ru",
    system_lang_code="ru",
    use_ipv6=config.cfg.UseIPv6,
    connection_retries=-1,
    retry_delay=2,
    proxy=get_proxy(),
)
client.parse_mode = CustomMarkdown()

from . import (  # noqa: E402, F401
    actions,
    admins,
    base,
    callbacks,
    forum,
    func,
    games,
    mailing,
    notes,
    referrals,
    shop,
    states,
    statistic,
    tickets,
    trading,
)
