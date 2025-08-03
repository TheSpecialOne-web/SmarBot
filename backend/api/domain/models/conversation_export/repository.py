from abc import ABC, abstractmethod

from ..tenant import Id as TenantId
from .conversation_export import (
    ConversationExport,
    ConversationExportForCreate,
    ConversationExportWithUser,
    Id,
)


class IConversationExportRepository(ABC):
    @abstractmethod
    def create(self, conversation_export: ConversationExportForCreate) -> ConversationExport:
        pass

    @abstractmethod
    def find_by_id(self, tenant_id: TenantId, id: Id) -> ConversationExport:
        pass

    @abstractmethod
    def find_by_ids_and_tenant_id(self, tenant_id: TenantId, ids: list[Id]) -> list[ConversationExport]:
        pass

    @abstractmethod
    def update(self, conversation_export: ConversationExport) -> None:
        pass

    @abstractmethod
    def find_with_user_by_tenant_id(self, tenant_id: TenantId) -> list[ConversationExportWithUser]:
        pass

    @abstractmethod
    def delete_by_ids_and_tenant_id(self, tenant_id: TenantId, conversation_export_ids: list[Id]) -> None:
        pass
