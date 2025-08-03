from azure.identity import DefaultAzureCredential
from injector import Module, provider

from api.domain.services.llm import ILLMService

from .llm import LLMService


class LLMModule(Module):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.azure_credential = azure_credential

    @provider
    def llm_service(self) -> ILLMService:
        return LLMService(self.azure_credential)
