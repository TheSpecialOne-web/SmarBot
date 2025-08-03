from logging import getLogger

from migrations.infrastructure.postgres import (
    ModelName,
    get_conversation_turns_without_token_count,
    set_token_count_to_conversation_turn,
)

logger = getLogger(__name__)
logger.setLevel("INFO")


def _get_model_coefficient(model_name):
    model_coefficient = {
        ModelName.GPT_4: 3.0,
        ModelName.GPT_4_TURBO_1106: 1.0,
        ModelName.GPT_4_TURBO_2024_04_09: 1.0,
        ModelName.GPT_35_TURBO: 0.2,
        ModelName.GPT_35_TURBO_16K: 0.2,
        ModelName.GPT_35_TURBO_1106: 0.2,
    }[model_name]
    return model_coefficient


def calculate_token_count():
    logger.info("Initiating token count calculation")
    try:
        conversation_turns = get_conversation_turns_without_token_count()
    except Exception as e:
        logger.error(f"Error getting conversation turns without token count: {e}")

    for conversation_turn in conversation_turns:
        model_coeff = _get_model_coefficient(conversation_turn.response_generator_model)
        token_count = (conversation_turn.response_input_token + conversation_turn.response_output_token) * model_coeff

        try:
            set_token_count_to_conversation_turn(conversation_turn.id, token_count)
        except Exception as e:
            logger.error(f"Error setting token count for conversation turn {conversation_turn.id}: {e}")
            raise e

    logger.info("Token count calculation completed")
