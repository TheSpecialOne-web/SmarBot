from azure.identity import DefaultAzureCredential
from injector import Module, provider

from api.domain.services.blob_storage import IBlobStorageService

from .blob_storage import BlobStorageService


class BlobStorageModule(Module):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.azure_credential = azure_credential

    @provider
    def blob_storage_service(self) -> IBlobStorageService:
        return BlobStorageService(self.azure_credential)
