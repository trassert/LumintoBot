from loguru import logger

from vkbottle.dispatch.rules import ABCRule
from vkbottle.bot import Bot, Message

from . import config
from . import db
from . import phrase
from . import telegram
from . import crosssocial


client = Bot(token=config.tokens.vk.token)


class CaseRule(ABCRule[Message]):
    def __init__(self, command: str):
        self.command = command.lower()

    async def check(self, message: Message) -> bool:
        return message.text.lower() == self.command


@client.on.message(CaseRule("/ip"))
@client.on.message(CaseRule("/айпи"))
@client.on.message(CaseRule("/хост"))
@client.on.message(CaseRule("/host"))
async def host(message: Message):
    logger.info("Запрошен IP в ВК")
    await message.reply(phrase.server.host.format(db.database("host")))


@client.on.message(regex=r"(?i)^/пинг(.*)")
async def ping(message: Message, match: tuple):
    return await message.reply(
        await crosssocial.ping(
            message.date,
            match[0].strip(),
            vk=True
        )
    )


@client.on.chat_message()
async def tg_chat(message: Message):
    try:
        user_info = await client.api.users.get(user_ids=message.from_id)
        name = "{} {}".format(user_info[0].first_name, user_info[0].last_name)
    except IndexError:
        return logger.info("Юзер не найден, пропускаем")
    logger.info(f"ВК>ТГ: {name} > {message.text}")
    return await telegram.client.send_message(
        config.chats.chat,
        reply_to=config.chats.topics.vk,
        message=f"**{name}**\n{message.text}",
    )
