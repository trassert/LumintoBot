# @client.on(events.CallbackQuery(func=func.checks, pattern=r"^word"))
# async def word_callback(event: events.CallbackQuery.Event):
#     data = event.data.decode("utf-8").split(".")
#     logger.info(f"КБ кнопка (Word), дата: {data}")
#     return await _handle_suggestion(
#         event,
#         word=data[2],
#         accept_file=pathes.crocoall,
#         reject_file=pathes.crocobl,
#         exists_phrase=phrase.word.exists,
#         success_phrase=phrase.word.success,
#         reject_phrase=phrase.word.no,
#         add_phrase=phrase.word.add,
#         reject_add_phrase=phrase.word.noadd,
#     )
