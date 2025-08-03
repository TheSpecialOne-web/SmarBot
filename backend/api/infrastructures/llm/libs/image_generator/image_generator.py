import os

import openai

from api.domain.models.conversation.image_url import ImageUrl
from api.domain.models.text_2_image_model import Text2ImageModelName
from api.infrastructures.llm.libs.constants import CONTENT_FILTER_NOTION
from api.libs.exceptions import BadRequest

AZURE_ENGINE_DALLE3 = os.environ.get("AZURE_ENGINE_DALLE3")

model_to_engine = {
    Text2ImageModelName.DALL_E_3: AZURE_ENGINE_DALLE3,
}


class ImageGenerator:
    def __init__(self, client: openai.AzureOpenAI, model: Text2ImageModelName):
        engine = model_to_engine[model]
        if not engine:
            raise ValueError("engine is not set")
        self.engine = engine
        self.client = client

    def generate_image(self, prompt: str) -> ImageUrl:
        try:
            response = self.client.images.generate(
                model=self.engine,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            url = response.data[0].url
            if not url:
                return ImageUrl(root="")
            return ImageUrl(root=url)
        except openai.BadRequestError as e:
            if e.code == "content_policy_violation":
                raise BadRequest(CONTENT_FILTER_NOTION)
            raise e
