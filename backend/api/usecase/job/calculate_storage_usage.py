from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    tenant as tenant_domain,
)
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.libs.logging import get_logger


class ICalculateStorageUsageUseCase(ABC):
    @abstractmethod
    def calculate_storage_usage(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_id: document_domain.Id
    ) -> None:
        pass


class CalculateStorageUsageUseCase(ICalculateStorageUsageUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        document_repo: document_domain.IDocumentRepository,
        cognitive_search_service: ICognitiveSearchService,
    ):
        self.logger = get_logger()
        self.bot_repo = bot_repo
        self.tenant_repo = tenant_repo
        self.document_repo = document_repo
        self.cognitive_search_service = cognitive_search_service

    def calculate_storage_usage(
        self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, document_id: document_domain.Id
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)

        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)

        document = self.document_repo.find_by_id_and_bot_id(document_id, bot_id)

        if bot.search_method in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]:
            self.logger.info("skip calculate storage usage for URSA bot")
            return

        index_documents = self.cognitive_search_service.find_index_documents_by_bot_id_and_document_id(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            bot_id=bot.id,
            document_id=document.id,
        )

        # storage_usageの計算
        storage_usage = 0
        for index_document in index_documents:
            storage_usage += index_document.storage_usage
        self.logger.info(f"storage_usage: {storage_usage}")

        document.update_storage_usage(document_domain.StorageUsage(root=storage_usage))
        self.document_repo.update(document)
