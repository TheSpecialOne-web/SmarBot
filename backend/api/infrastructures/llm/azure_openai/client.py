import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from neollm.types import ClientSettings
import openai

from api.domain.models.llm import ModelName, Platform

AZURE_OPENAI_API_VERSION = "2024-02-01"
AZURE_OPENAI_ENDPOINT_JAPAN_EAST = os.environ.get("AZURE_OPENAI_ENDPOINT_JAPAN_EAST")
AZURE_OPENAI_ENDPOINT_EAST_US = os.environ.get("AZURE_OPENAI_ENDPOINT_EAST_US")
AZURE_OPENAI_ENDPOINT_EAST_US_2 = os.environ.get("AZURE_OPENAI_ENDPOINT_EAST_US_2")


_model_name_to_azure_endpoint = {
    ModelName.GPT_35_TURBO: AZURE_OPENAI_ENDPOINT_JAPAN_EAST,
    ModelName.GPT_35_TURBO_16K: AZURE_OPENAI_ENDPOINT_JAPAN_EAST,
    ModelName.GPT_4: AZURE_OPENAI_ENDPOINT_JAPAN_EAST,
    ModelName.GPT_4O_MINI_2024_07_18: AZURE_OPENAI_ENDPOINT_EAST_US,
    ModelName.GPT_4_TURBO_2024_04_09: AZURE_OPENAI_ENDPOINT_EAST_US_2,
    ModelName.GPT_4O_2024_05_13: AZURE_OPENAI_ENDPOINT_EAST_US_2,
    ModelName.GPT_4O_2024_08_06: AZURE_OPENAI_ENDPOINT_EAST_US_2,
    ModelName.O1_PREVIEW_20240912: AZURE_OPENAI_ENDPOINT_EAST_US_2,
    ModelName.O1_MINI_20240912: AZURE_OPENAI_ENDPOINT_EAST_US_2,
}


class AOAIClient:
    token_provider: openai.lib.azure.AzureADTokenProvider

    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.token_provider = get_bearer_token_provider(
            azure_credential,
            "https://cognitiveservices.azure.com/.default",
        )
        os.environ["OPENAI_API_VERSION"] = AZURE_OPENAI_API_VERSION

    def get_client_settings(self, model_name: ModelName) -> ClientSettings:
        if model_name.to_platform() != Platform.AZURE:
            raise Exception(f"Model {model_name} is not on Azure")
        try:
            azure_endpoint = _model_name_to_azure_endpoint[model_name]
        except KeyError:
            raise Exception(f"Model {model_name} is not on Azure")
        return {
            "azure_ad_token_provider": self.token_provider,
            "azure_endpoint": azure_endpoint,
        }

    def get_azure_openai_client(self, region: str = "japaneast") -> openai.AzureOpenAI:
        endpoint_region_map = {
            "japaneast": AZURE_OPENAI_ENDPOINT_JAPAN_EAST,
            "eastus2": AZURE_OPENAI_ENDPOINT_EAST_US_2,
        }
        endpoint = endpoint_region_map.get(region)
        if endpoint is None:
            raise Exception("Azure OpenAI endpoint is not set")
        return openai.AzureOpenAI(
            azure_ad_token_provider=self.token_provider,
            azure_endpoint=endpoint,
        )

    def get_azure_openai_client_for_dalle3(self):
        return openai.AzureOpenAI(
            azure_ad_token_provider=self.token_provider,
            azure_endpoint=AZURE_OPENAI_ENDPOINT_EAST_US,
        )
