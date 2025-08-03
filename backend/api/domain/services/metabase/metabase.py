from abc import ABC, abstractmethod

from ...models.tenant import Id as TenantId


class IMetabaseService(ABC):
    @abstractmethod
    def find_tenant_usage_dashboard(self, tenant_id: TenantId, year_month: str, type: str) -> str:
        pass
