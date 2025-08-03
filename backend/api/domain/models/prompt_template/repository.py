from abc import ABC, abstractmethod

from ..tenant import Id as TenantId
from .id import Id
from .prompt_template import PromptTemplate, PromptTemplateForCreate


class IPromptTemplateRepository(ABC):
    @abstractmethod
    def find_by_tenant_id(self, tenant_id: TenantId) -> list[PromptTemplate]:
        pass

    @abstractmethod
    def find_by_id_and_tenant_id(
        self,
        id: Id,
        tenant_id: TenantId,
    ) -> PromptTemplate:
        pass

    @abstractmethod
    def bulk_create(
        self,
        tenant_id: TenantId,
        prompt_templates: list[PromptTemplateForCreate],
    ) -> list[PromptTemplate]:
        pass

    @abstractmethod
    def update(self, prompt_template: PromptTemplate) -> None:
        pass

    @abstractmethod
    def delete_by_ids_and_tenant_id(
        self,
        ids: list[Id],
        tenant_id: TenantId,
    ) -> None:
        pass

    @abstractmethod
    def delete_by_tenant_id(self, tenant_id: TenantId) -> None:
        pass

    @abstractmethod
    def hard_delete_by_tenant_id(self, tenant_id: TenantId) -> None:
        pass
