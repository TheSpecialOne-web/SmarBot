from azure.identity import DefaultAzureCredential
from injector import Module, provider

from api.domain.services.ai_vision import IAiVisionService

from .ai_vision import AiVisionService


class AiVisionModule(Module):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.azure_credential = azure_credential

    @provider
    def ai_vision_service(self) -> IAiVisionService:
        return AiVisionService(self.azure_credential)
