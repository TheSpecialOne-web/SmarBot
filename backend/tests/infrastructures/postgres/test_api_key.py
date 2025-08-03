from datetime import datetime

from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
)
from api.infrastructures.postgres.api_key import ApiKeyRepository
from api.infrastructures.postgres.models.api_key import ApiKey as ApiKeyModel
from tests.conftest import BotsSeed

ApiKeySeed = tuple[api_key_domain.ApiKey, bot_domain.Bot]
ApiKeysSeed = tuple[list[api_key_domain.ApiKey], bot_domain.Id]


class TestApiKeyRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.api_key_repo = ApiKeyRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_find_all(self, bots_seed: BotsSeed, test_app):
        bots, _, tenant, _ = bots_seed
        bot_id = bots[0].id
        api_key = api_key_domain.ApiKeyForCreate(
            bot_id=bot_id,
            name=api_key_domain.Name(root="test_find_all_api_key_name"),
            expires_at=api_key_domain.ExpiresAt(root=datetime(2060, 1, 1, 0, 0, 0)),
        )
        self.api_key_repo.create(api_key)

        api_keys = self.api_key_repo.find_all(tenant_id=tenant.id)

        assert api_keys == [
            api_key_domain.ApiKey(
                id=api_key.id,
                bot_id=api_key.bot_id,
                name=api_key.name,
                expires_at=api_key.expires_at,
                decrypted_api_key=api_key.encrypted_api_key.decrypt(),
                endpoint_id=bots[0].endpoint_id,
            )
        ]

    def test_find_by_id_and_endpoint_id(self, api_key_seed: ApiKeySeed):
        api_key, bot = api_key_seed

        found_api_key = self.api_key_repo.find_by_id_and_endpoint_id(
            id=api_key.id,
            endpoint_id=bot.endpoint_id,
        )

        assert found_api_key == api_key

    def test_find_by_endpoint_id_and_decrypted_api_key(self, api_key_seed: ApiKeySeed):
        api_key, bot = api_key_seed

        found_api_key = self.api_key_repo.find_by_endpoint_id_and_decrypted_api_key(
            endpoint_id=bot.endpoint_id,
            decrypted_api_key=api_key.decrypted_api_key,
        )

        assert found_api_key == api_key

    def test_create(self, bots_seed: BotsSeed):
        bots, _, _, _ = bots_seed
        bot_id = bots[0].id
        endpoint_id = bots[0].endpoint_id
        api_key_for_create = api_key_domain.ApiKeyForCreate(
            bot_id=bot_id,
            name=api_key_domain.Name(root="test_create_api_key_name"),
            expires_at=api_key_domain.ExpiresAt(root=datetime(2060, 1, 1, 0, 0, 0)),
        )

        self.api_key_repo.create(api_key_for_create)

        created_api_key = (
            self.session.execute(select(ApiKeyModel).where(ApiKeyModel.id == api_key_for_create.id.root))
            .scalars()
            .first()
        )

        want = api_key_domain.ApiKey(
            id=api_key_for_create.id,
            bot_id=api_key_for_create.bot_id,
            name=api_key_for_create.name,
            expires_at=api_key_for_create.expires_at,
            decrypted_api_key=api_key_for_create.encrypted_api_key.decrypt(),
            endpoint_id=endpoint_id,
        )

        assert created_api_key is not None
        assert created_api_key.id == want.id.root
        assert created_api_key.bot_id == want.bot_id.value
        assert created_api_key.name == want.name.root
        if want.expires_at is None:
            assert created_api_key.expires_at is None
        else:
            assert created_api_key.expires_at is not None
            assert created_api_key.expires_at == want.expires_at.root
        assert (
            api_key_domain.EncryptedApiKey(root=created_api_key.encrypted_api_key).decrypt().root
            == want.decrypted_api_key.root
        )

    def test_delete_by_bot_id(self, bots_seed: BotsSeed):
        bots, _, _, _ = bots_seed
        bot_id = bots[0].id
        api_key_for_create1 = api_key_domain.ApiKeyForCreate(
            bot_id=bot_id,
            name=api_key_domain.Name(root="test_delete_by_bot_id_api_key_name_1"),
            expires_at=None,
        )
        api_key_for_create2 = api_key_domain.ApiKeyForCreate(
            bot_id=bot_id,
            name=api_key_domain.Name(root="test_delete_by_bot_id_api_key_name_2"),
            expires_at=None,
        )
        created_api_key = self.api_key_repo.create(api_key_for_create1)
        created_api_key = self.api_key_repo.create(api_key_for_create2)

        self.api_key_repo.delete_by_bot_id(bot_id)

        deleted_api_key1 = (
            self.session.execute(select(ApiKeyModel).where(ApiKeyModel.id == created_api_key.id.root))
            .scalars()
            .first()
        )
        deleted_api_key2 = (
            self.session.execute(select(ApiKeyModel).where(ApiKeyModel.id == created_api_key.id.root))
            .scalars()
            .first()
        )

        assert deleted_api_key1 is None
        assert deleted_api_key2 is None

    def test_delete_by_ids_and_tenant_id(self, bots_seed: BotsSeed):
        bots, _, tenant, _ = bots_seed

        bot_id = bots[0].id
        api_key_for_create1 = api_key_domain.ApiKeyForCreate(
            bot_id=bot_id,
            name=api_key_domain.Name(root="test_delete_by_ids_and_tenant_id_api_key_name_1"),
            expires_at=None,
        )
        api_key_for_create2 = api_key_domain.ApiKeyForCreate(
            bot_id=bot_id,
            name=api_key_domain.Name(root="test_delete_by_ids_and_tenant_id_api_key_name_2"),
            expires_at=None,
        )
        created_api_key1 = self.api_key_repo.create(api_key_for_create1)
        created_api_key2 = self.api_key_repo.create(api_key_for_create2)

        self.api_key_repo.delete_by_ids_and_tenant_id([created_api_key1.id, created_api_key2.id], tenant.id)

        deleted_api_key1 = (
            self.session.execute(select(ApiKeyModel).where(ApiKeyModel.id == created_api_key1.id.root))
            .scalars()
            .first()
        )
        deleted_api_key2 = (
            self.session.execute(select(ApiKeyModel).where(ApiKeyModel.id == created_api_key2.id.root))
            .scalars()
            .first()
        )

        assert deleted_api_key1 is None
        assert deleted_api_key2 is None

    def test_hard_delete_by_bot_ids(self, api_keys_seed: ApiKeysSeed):
        _, bot_id = api_keys_seed

        self.api_key_repo.delete_by_bot_id(bot_id)
        self.api_key_repo.hard_delete_by_bot_ids([bot_id])

        found_api_keys = (
            self.session.execute(
                select(ApiKeyModel).where(ApiKeyModel.bot_id == bot_id.value).execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )

        assert len(found_api_keys) == 0

    def test_find_by_bot_ids(self, api_keys_seed: ApiKeysSeed):
        new_api_keys, bot_id = api_keys_seed

        api_keys = self.api_key_repo.find_by_bot_ids([bot_id])

        assert api_keys == new_api_keys
