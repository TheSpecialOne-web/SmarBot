from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    tenant as tenant_domain,
)
from api.infrastructures.postgres.models.api_key import ApiKey as ApiKeyModel
from api.infrastructures.postgres.models.bot import Bot as BotModel
from api.infrastructures.postgres.models.tenant import Tenant as TenantModel
from api.libs.exceptions import NotFound


class ApiKeyRepository(api_key_domain.IApiKeyRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_all(self, tenant_id: tenant_domain.Id) -> list[api_key_domain.ApiKey]:
        api_keys = (
            self.session.execute(
                select(ApiKeyModel)
                .join(BotModel, BotModel.id == ApiKeyModel.bot_id)
                .join(TenantModel, TenantModel.id == BotModel.tenant_id)
                .where(TenantModel.id == tenant_id.value)
                .options(joinedload(ApiKeyModel.bot))  # Eager load the associated Bot
            )
            .scalars()
            .all()
        )
        return [api_key.to_domain() for api_key in api_keys]

    def find_by_id_and_endpoint_id(
        self, id: api_key_domain.Id, endpoint_id: bot_domain.EndpointId
    ) -> api_key_domain.ApiKey:
        api_key = (
            self.session.execute(
                select(ApiKeyModel)
                .join(BotModel, BotModel.id == ApiKeyModel.bot_id)
                .where(ApiKeyModel.id == id.root, BotModel.endpoint_id == endpoint_id.root)
                .options(joinedload(ApiKeyModel.bot))  # Eager load the associated Bot
            )
            .scalars()
            .first()
        )
        if api_key is None:
            raise NotFound("ApiKey not found")
        return api_key.to_domain()

    def find_by_endpoint_id_and_decrypted_api_key(
        self,
        endpoint_id: bot_domain.EndpointId,
        decrypted_api_key: api_key_domain.DecryptedApiKey,
    ) -> api_key_domain.ApiKey:
        stmt = (
            select(ApiKeyModel)
            .join(BotModel, BotModel.id == ApiKeyModel.bot_id)
            .where(BotModel.endpoint_id == endpoint_id.root)
            .options(joinedload(ApiKeyModel.bot))  # Eager load the associated Bot
        )
        raw_api_keys = self.session.execute(stmt).scalars().all()
        api_keys = [raw_api_key.to_domain() for raw_api_key in raw_api_keys]
        api_key = next(
            (api_key for api_key in api_keys if api_key.decrypted_api_key.root == decrypted_api_key.root),
            None,
        )
        if api_key is None:
            raise NotFound("ApiKey not found")
        return api_key

    def create(self, api_key: api_key_domain.ApiKeyForCreate) -> api_key_domain.ApiKey:
        new_api_key = ApiKeyModel.from_domain(api_key)

        try:
            self.session.add(new_api_key)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return new_api_key.to_domain()

    def delete_by_bot_id(self, bot_id: bot_domain.Id) -> None:
        api_keys = self.session.execute(select(ApiKeyModel).where(ApiKeyModel.bot_id == bot_id.value)).scalars().all()

        for api_key in api_keys:
            api_key.deleted_at = datetime.now()

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_ids_and_tenant_id(self, ids: list[api_key_domain.Id], tenant_id: tenant_domain.Id) -> None:
        stmt = (
            select(ApiKeyModel)
            .join(BotModel, BotModel.id == ApiKeyModel.bot_id)
            .where(ApiKeyModel.id.in_([id.root for id in ids]), BotModel.tenant_id == tenant_id.value)
        )
        api_keys = self.session.execute(stmt).scalars().all()

        for api_key in api_keys:
            api_key.deleted_at = datetime.now()

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_bot_ids(self, bot_ids: list[bot_domain.Id]) -> None:
        bot_id_values = [bot_id.value for bot_id in bot_ids]
        try:
            self.session.execute(
                delete(ApiKeyModel)
                .where(ApiKeyModel.bot_id.in_(bot_id_values))
                .where(ApiKeyModel.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_by_bot_ids(
        self, bot_ids: list[bot_domain.Id], include_deleted: bool = False
    ) -> list[api_key_domain.ApiKey]:
        bot_id_values = [bot_id.value for bot_id in bot_ids]

        api_keys = (
            self.session.execute(
                select(ApiKeyModel)
                .where(ApiKeyModel.bot_id.in_(bot_id_values))
                .execution_options(include_deleted=include_deleted)
                .options(joinedload(ApiKeyModel.bot))  # Eager load the associated Bot
            )
            .scalars()
            .all()
        )
        return [api_key.to_domain() for api_key in api_keys]

    def find_by_id_and_bot_id(
        self, id: api_key_domain.Id, bot_id: bot_domain.Id, include_deleted: bool = False
    ) -> api_key_domain.ApiKey:
        api_key = (
            self.session.execute(
                select(ApiKeyModel)
                .where(ApiKeyModel.id == id.root, ApiKeyModel.bot_id == bot_id.value)
                .execution_options(include_deleted=include_deleted)
                .options(joinedload(ApiKeyModel.bot))  # Eager load the associated Bot
            )
            .scalars()
            .first()
        )
        if api_key is None:
            raise NotFound("api_key not found")
        return api_key.to_domain()
