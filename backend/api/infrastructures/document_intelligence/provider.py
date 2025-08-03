from azure.identity import DefaultAzureCredential
from injector import Module, provider

from api.domain.services.document_intelligence import IDocumentIntelligenceService

from .document_intelligence import DocumentIntelligenceService


class DocumentIntelligenceModule(Module):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.azure_credential = azure_credential

    @provider
    def document_intelligence_module(self) -> IDocumentIntelligenceService:
        return DocumentIntelligenceService(self.azure_credential)
