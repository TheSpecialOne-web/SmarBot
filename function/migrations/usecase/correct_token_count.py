from datetime import datetime

from libs.logging import get_logger
from migrations.infrastructure.postgres.bot import get_bots
from migrations.infrastructure.postgres.conversation import (
    get_conversations_by_bot_id,
    update_conversation_turn_token_count,
)
from migrations.infrastructure.postgres.postgres import ModelName

logger = get_logger(__name__)


model_coefficient = {
    ModelName.GPT_4: 3.0,
    ModelName.GPT_4_TURBO_1106: 1.0,
    ModelName.GPT_4_TURBO_2024_04_09: 1.0,
    ModelName.GPT_4O_2024_05_13: 0.5,
    ModelName.GPT_35_TURBO: 0.2,
    ModelName.GPT_35_TURBO_16K: 0.2,
    ModelName.GPT_35_TURBO_1106: 0.2,
    ModelName.GPT_4_TURBO_2024_04_09_OPENAI: 1.0,
    ModelName.GPT_4O_2024_05_13_OPENAI: 0.5,
    ModelName.CLAUDE_3_OPUS_20240229: 3.0,
    ModelName.CLAUDE_3_SONNET_20240229: 1.0,
    ModelName.CLAUDE_3_HAIKU_20240307: 0.2,
    ModelName.CLAUDE_35_SONNET_20240620: 1.0,
    ModelName.GEMINI_10_PRO: 0.2,
    ModelName.GEMINI_15_PRO_PREVIEW_0409: 0.2,
    ModelName.GEMINI_15_PRO_001: 0.5,
    ModelName.GEMINI_15_FLASH_001: 0.2,
}

QUERY_GENERATOR_TOKEN = 500
RESPONSE_GENERATOR_TOKEN = 200
FOLLOW_UP_QUESTION_TOKEN = 300
RESPONSE_SYSTEM_PROMPT_TOKEN = 240


def correct_token_count(start_date: str, end_date: str):
    start_datetime = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")

    bots = get_bots()
    for bot in bots:
        conversations = get_conversations_by_bot_id(bot.id, start_datetime, end_datetime)
        for conversation in conversations:
            for turn in conversation.turns:
                if turn.token_count is None:
                    continue
                token_count = 0.0

                model_name = ModelName(turn.response_generator_model)
                c = model_coefficient[model_name]

                use_query_generator = turn.query_input_token is not None and turn.query_input_token > 0
                if use_query_generator:
                    # query generator を使うときは、クエリ生成とレスポンス生成の固定値を加算する
                    token_count = (turn.response_input_token + QUERY_GENERATOR_TOKEN + RESPONSE_GENERATOR_TOKEN) * c
                    # follow up questions が有効な場合は、追加で更問生成の固定値を加算する
                    token_follow_up_questions = (
                        FOLLOW_UP_QUESTION_TOKEN if bot.approach == "neollm" and bot.enable_follow_up_questions else 0
                    )
                    token_count += token_follow_up_questions
                else:
                    # query generator を使わないときは、レスポンス生成の固定値のみを加算する
                    if bot.approach == "chat_gpt_default":
                        # chat_gpt_default の場合は、システムプロンプト文を引く
                        token_count = (
                            turn.response_input_token + RESPONSE_GENERATOR_TOKEN - RESPONSE_SYSTEM_PROMPT_TOKEN
                        ) * c
                    else:
                        token_count = (turn.response_input_token + RESPONSE_GENERATOR_TOKEN) * c

                if token_count > turn.token_count:
                    # 再計算したものが元の値より大きくなってしまったら、更新しない
                    continue
                update_conversation_turn_token_count(turn.id, token_count)

        logger.info(f"Corrected token count for bot: {bot.id}")

    logger.info("Token count correction completed")
