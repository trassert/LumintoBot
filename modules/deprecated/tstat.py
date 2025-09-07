@client.on(events.NewMessage(pattern=r"(?i)^/топ игроков$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/топигроков$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/topplayers$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/playtimetop$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/bestplayers$", func=checks))
@client.on(events.NewMessage(pattern=r"(?i)^/toppt", func=checks))
async def server_top_list(event: Message):
    try:
        async with MinecraftClient(
            host=config.tokens.rcon.host,
            port=config.tokens.rcon.port,
            password=config.tokens.rcon.password,
        ) as rcon:
            await event.reply(
                await rcon.send('playtimetop')
            )
    except TimeoutError:
        return await event.reply(phrase.server.stopped)
