from abc import ABC, abstractmethod

from ..tenant import Id as TenantId
from .chat_completion_export import (
    ChatCompletionExport,
    ChatCompletionExportForCreate,
    ChatCompletionExportWithUser,
    Id,
)


class IChatCompletionExportRepository(ABC):
    @abstractmethod
    def create(self, chat_completion_export: ChatCompletionExportForCreate) -> ChatCompletionExportWithUser:
        pass

    @abstractmethod
    def find_by_id(self, tenant_id: TenantId, id: Id) -> ChatCompletionExport:
        pass

    @abstractmethod
    def find_by_ids_and_tenant_id(self, tenant_id: TenantId, ids: list[Id]) -> list[ChatCompletionExport]:
        pass

    @abstractmethod
    def update(self, chat_completion_export: ChatCompletionExport) -> None:
        pass

    @abstractmethod
    def find_with_user_by_tenant_id(self, tenant_id: TenantId) -> list[ChatCompletionExportWithUser]:
        pass

    @abstractmethod
    def delete_by_ids_and_tenant_id(self, tenant_id: TenantId, ids: list[Id]) -> None:
        pass
