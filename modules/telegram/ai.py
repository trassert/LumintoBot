from telethon.tl.custom import Message
from telethon import events

from .client import client
from .global_checks import *

from .. import (
    phrase,
    db,
    ai
)

@client.on(events.NewMessage(pattern=r"(?i)^/ии\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ai\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^ии\s(.+)", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/бот\s(.+)", func=checks))
async def gemini(event: Message):
    arg = event.pattern_match.group(1).strip()
    response = await ai.response(arg)
    if response is None:
        return await event.reply(phrase.server.overload)
    if len(response) > 4096:
        for x in range(0, len(response), 4096):
            await event.reply(response[x : x + 4096])
    else:
        return await event.reply(response)

@client.on(events.NewMessage(pattern=r"(?i)^/ии$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/ai$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^ии$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/бот$", func=checks))
async def gemini_empty(event: Message):
    return await event.reply(phrase.no.response)

@client.on(events.NewMessage(pattern=r"(?i)^/лаи\s(.+)", func=checks))
async def local_ai(event: Message):
    text = event.pattern_match.group(1).strip()
    roles = db.roles()
    if roles.get(event.sender_id) < roles.ADMIN:
        return await event.reply(
            phrase.roles.no_perms.format(
                level=roles.ADMIN,
                name=phrase.roles.admin
            )
        )
    message_for_edit = await event.reply(phrase.ai.response)
    response = ""
    async for chunk in ai.asyncio_local_generator(text):
        response += chunk
    await event.reply(f":{response}:")
    await event.reply(f"id of response {message_for_edit.id}")