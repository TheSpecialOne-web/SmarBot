from abc import ABC, abstractmethod

from api.domain.models.bot import bot as bot_domain
from api.domain.models.tenant import tenant as tenant_domain

from .api_key import ApiKey, ApiKeyForCreate, DecryptedApiKey, Id


class IApiKeyRepository(ABC):
    @abstractmethod
    def find_all(self, tenant_id: tenant_domain.Id) -> list[ApiKey]:
        pass

    @abstractmethod
    def find_by_endpoint_id_and_decrypted_api_key(
        self,
        endpoint_id: bot_domain.EndpointId,
        decrypted_api_key: DecryptedApiKey,
    ) -> ApiKey:
        pass

    @abstractmethod
    def create(self, api_key: ApiKeyForCreate) -> ApiKey:
        pass

    @abstractmethod
    def delete_by_bot_id(self, bot_id: bot_domain.Id) -> None:
        pass

    @abstractmethod
    def delete_by_ids_and_tenant_id(self, ids: list[Id], tenant_id: tenant_domain.Id) -> None:
        pass

    @abstractmethod
    def hard_delete_by_bot_ids(self, bot_ids: list[bot_domain.Id]) -> None:
        pass

    @abstractmethod
    def find_by_bot_ids(self, bot_ids: list[bot_domain.Id], include_deleted: bool = False) -> list[ApiKey]:
        pass

    @abstractmethod
    def find_by_id_and_bot_id(self, id: Id, bot_id: bot_domain.Id, include_deleted: bool = False) -> ApiKey:
        pass
