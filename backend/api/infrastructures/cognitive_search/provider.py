from azure.identity import DefaultAzureCredential
from injector import Module, provider

from api.domain.services.cognitive_search import ICognitiveSearchService

from .cognitive_search import CognitiveSearchService


class CognitiveSearchModule(Module):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.azure_credential = azure_credential

    @provider
    def cognitive_search_service(self) -> ICognitiveSearchService:
        return CognitiveSearchService(self.azure_credential)
