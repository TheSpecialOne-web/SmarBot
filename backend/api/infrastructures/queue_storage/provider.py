from azure.identity import DefaultAzureCredential
from injector import Module, provider

from api.domain.services.queue_storage import IQueueStorageService

from .queue_storage import QueueStorageService


class QueueStorageModule(Module):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.azure_credential = azure_credential

    @provider
    def queue_storage_service(self) -> IQueueStorageService:
        return QueueStorageService(self.azure_credential)
