from datetime import datetime, timezone

from api.database import SessionFactory
from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    chat_completion_export as chat_completion_export_domain,
    tenant as tenant_domain,
)
from api.infrastructures.postgres.chat_completion_export import (
    ChatCompletionExportRepository,
)
from tests.conftest import BotsSeed, UserSeed

TenantSeed = tenant_domain.Tenant
ApiKeySeed = tuple[api_key_domain.ApiKey, bot_domain.Bot]
ChatCompletionExportsSeed = list[chat_completion_export_domain.ChatCompletionExport]


class TestChatCompletionExportRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.chat_completion_export_repo = ChatCompletionExportRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_create(self, tenant_seed: TenantSeed, user_seed: UserSeed, bots_seed: BotsSeed, api_key_seed: ApiKeySeed):
        # Given
        tenant = tenant_seed
        user_id, _, _, _, _ = user_seed
        bots, _, _, _ = bots_seed
        target_bot_id = bots[0].id
        api_key, _ = api_key_seed
        chat_completion_export_create = chat_completion_export_domain.ChatCompletionExportForCreate(
            creator_id=user_id,
            start_date_time=chat_completion_export_domain.StartDateTime(root=datetime.now(timezone.utc)),
            end_date_time=chat_completion_export_domain.EndDateTime(root=datetime.now(timezone.utc)),
            target_api_key_id=api_key.id,
            target_bot_id=target_bot_id,
        )

        # Call the method
        new_chat_completion_export = self.chat_completion_export_repo.create(chat_completion_export_create)

        # Assertions
        found_chat_completion_export = self.chat_completion_export_repo.find_by_id(
            tenant.id, new_chat_completion_export.id
        )
        assert new_chat_completion_export.id.root == found_chat_completion_export.id.root

    def test_find_by_id(self, tenant_seed: TenantSeed, chat_completion_exports_seed: ChatCompletionExportsSeed):
        # Given
        tenant = tenant_seed
        chat_completion_exports = chat_completion_exports_seed
        chat_completion_export = chat_completion_exports[0]

        # Call the method
        found_chat_completion_export = self.chat_completion_export_repo.find_by_id(
            tenant.id, chat_completion_export.id
        )

        # Assertions
        assert chat_completion_export.id.root == found_chat_completion_export.id.root

    def test_find_by_ids_and_tenant_id(
        self, tenant_seed: TenantSeed, chat_completion_exports_seed: ChatCompletionExportsSeed
    ):
        # Given
        tenant = tenant_seed
        chat_completion_exports = chat_completion_exports_seed

        # Call the method
        found_chat_completion_export = self.chat_completion_export_repo.find_by_ids_and_tenant_id(
            tenant.id, [chat_completion_export.id for chat_completion_export in chat_completion_exports]
        )

        # Assertions
        assert len(found_chat_completion_export) > 0

    def test_update(self, tenant_seed: TenantSeed, chat_completion_exports_seed: ChatCompletionExportsSeed):
        # Given
        tenant = tenant_seed
        chat_completion_exports = chat_completion_exports_seed
        chat_completion_export = chat_completion_exports[0]
        chat_completion_export.update_status_to_active()

        # Call the method
        self.chat_completion_export_repo.update(chat_completion_export)

        # Assertions
        found_chat_completion_export = self.chat_completion_export_repo.find_by_id(
            tenant.id, chat_completion_export.id
        )
        assert found_chat_completion_export.status == chat_completion_export.status

    def test_find_with_user_by_tenant_id(
        self, tenant_seed: TenantSeed, chat_completion_exports_seed: ChatCompletionExportsSeed
    ):
        # Given
        tenant = tenant_seed
        chat_completion_exports = chat_completion_exports_seed
        chat_completion_export = chat_completion_exports[0]

        # Call the method
        results = self.chat_completion_export_repo.find_with_user_by_tenant_id(tenant.id)

        # Assertions
        assert chat_completion_export.id.root in [result.id.root for result in results]

    def test_delete_by_ids_and_tenant_id(
        self, tenant_seed: TenantSeed, chat_completion_exports_seed: ChatCompletionExportsSeed
    ):
        # Given
        tenant = tenant_seed
        chat_completion_exports = chat_completion_exports_seed
        chat_completion_export_ids = [
            chat_completion_export_id.id for chat_completion_export_id in chat_completion_exports
        ]

        # Call the method
        self.chat_completion_export_repo.delete_by_ids_and_tenant_id(tenant.id, chat_completion_export_ids)

        # Assertions
        results = self.chat_completion_export_repo.find_with_user_by_tenant_id(tenant.id)
        assert len(results) == 0
