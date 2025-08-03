from libs.logging import get_logger
from migrations.infrastructure.postgres.postgres import (
    update_bots_image_generator_model_family,
    update_bots_response_generator_model_family,
)
from migrations.types import ModelName, Text2ImageModel

logger = get_logger(__name__)
logger.setLevel("INFO")


def migrate_model_to_model_family():
    for response_generator_model in ModelName:
        model_family = response_generator_model.to_model_family()
        update_bots_response_generator_model_family(response_generator_model, model_family)

    for image_generator_model in Text2ImageModel:
        model_family = image_generator_model.to_model_family()
        update_bots_image_generator_model_family(image_generator_model, model_family)
    logger.info("model to model_family migration completed")
