from abc import ABC, abstractmethod

from injector import inject
from pydantic import BaseModel

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    tenant as tenant_domain,
)
from api.domain.models.api_key import ApiKeyForCreate
from api.libs.logging import get_logger


class ApiKeyWithBot(BaseModel):
    id: api_key_domain.Id
    bot: bot_domain.Bot
    name: api_key_domain.Name
    api_key: api_key_domain.DecryptedApiKey
    expires_at: api_key_domain.ExpiresAt | None
    endpoint_id: bot_domain.EndpointId


class GetApiKeysOutput(BaseModel):
    api_keys: list[ApiKeyWithBot]


class CreateApiKeyOutput(ApiKeyWithBot):
    pass


class IApiKeyUseCase(ABC):
    @abstractmethod
    def get_api_keys(self, tenant_id: tenant_domain.Id) -> GetApiKeysOutput:
        pass

    @abstractmethod
    def create_api_key(self, tenant_id: tenant_domain.Id, api_key: ApiKeyForCreate) -> CreateApiKeyOutput:
        pass

    @abstractmethod
    def delete_api_keys(self, tenant_id: tenant_domain.Id, api_key_ids: list[api_key_domain.Id]) -> None:
        pass


class ApiKeyUseCase(IApiKeyUseCase):
    @inject
    def __init__(self, bot_repo: bot_domain.IBotRepository, api_key_repo: api_key_domain.IApiKeyRepository) -> None:
        self.logger = get_logger()
        self.bot_repo = bot_repo
        self.api_key_repo = api_key_repo

    def get_api_keys(self, tenant_id: tenant_domain.Id) -> GetApiKeysOutput:
        api_keys = self.api_key_repo.find_all(tenant_id)

        bot_ids = [api_key.bot_id for api_key in api_keys]

        bots = self.bot_repo.find_by_ids_and_tenant_id(bot_ids, tenant_id)
        bot_id_to_bot = {bot.id.value: bot for bot in bots}

        return_api_keys: list[ApiKeyWithBot] = []
        for api_key in api_keys:
            bot = bot_id_to_bot.get(api_key.bot_id.value)
            if bot is None:
                self.logger.warning(f"Bot not found for api_key_id={api_key.id}")
                continue
            return_api_keys.append(
                ApiKeyWithBot(
                    id=api_key.id,
                    bot=bot,
                    name=api_key.name,
                    api_key=api_key.decrypted_api_key,
                    expires_at=api_key.expires_at,
                    endpoint_id=api_key.endpoint_id,
                )
            )
        return GetApiKeysOutput(api_keys=return_api_keys)

    def create_api_key(self, tenant_id: tenant_domain.Id, api_key: ApiKeyForCreate) -> CreateApiKeyOutput:
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_domain.Id(value=api_key.bot_id.value), tenant_id)
        created_api_key = self.api_key_repo.create(api_key)

        return CreateApiKeyOutput(
            id=created_api_key.id,
            bot=bot,
            name=created_api_key.name,
            api_key=created_api_key.decrypted_api_key,
            expires_at=created_api_key.expires_at,
            endpoint_id=created_api_key.endpoint_id,
        )

    def delete_api_keys(self, tenant_id: tenant_domain.Id, api_key_ids: list[api_key_domain.Id]) -> None:
        return self.api_key_repo.delete_by_ids_and_tenant_id(api_key_ids, tenant_id)
