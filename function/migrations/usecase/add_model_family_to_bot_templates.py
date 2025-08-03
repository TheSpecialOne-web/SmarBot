from libs.logging import get_logger
from migrations.infrastructure.postgres.postgres import (
    get_bot_templates,
    update_bot_template_response_generator_model_family,
)
from migrations.types import ModelName

logger = get_logger(__name__)
logger.setLevel("INFO")


def migrate_bot_templates_model_family():
    bot_templates = get_bot_templates()
    for bot_template in bot_templates:
        response_generator_model = ModelName(bot_template.response_generator_model)
        model_family = response_generator_model.to_model_family()
        update_bot_template_response_generator_model_family(bot_template.id, model_family)
        logger.info(f"updated bot_id: {bot_template.id}, model_family: {model_family}")

    logger.info("bot_templates migration completed")
