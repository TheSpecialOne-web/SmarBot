from migrations.infrastructure.postgres import (
    PdfParser,
    get_chat_gpt_bots,
    update_bot_pdf_parser,
)


def set_pdf_parser_to_chat_gpt_default_bots():
    bots = get_chat_gpt_bots()
    for bot in bots:
        if bot.pdf_parser is None:
            try:
                update_bot_pdf_parser(bot.id, PdfParser.PYPDF)
            except Exception as e:
                raise Exception(f"failed to update bot pdf parser. bot_id: {bot.id}, error: {e}")
