from datetime import datetime
from typing import Tuple

from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    conversation_export as conversation_export_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.infrastructures.postgres.conversation_export import (
    ConversationExportRepository,
)
from api.infrastructures.postgres.models.conversation_export import (
    ConversationExport as ConversationExportModel,
)
from tests.conftest import BotsSeed

TenantSeed = tenant_domain.Tenant
UserSeed = Tuple[user_domain.Id, user_domain.UserForCreate, tenant_domain.Id, str, user_domain.Id]

ConversationExportsSeed = list[conversation_export_domain.ConversationExport]


class TestConversationExportRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.conversation_export_repo = ConversationExportRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_create(self, user_seed: UserSeed, bots_seed: BotsSeed):
        # Input
        user_id, _, _, _, _ = user_seed
        bots, _, _, _ = bots_seed
        target_bot_id = bots[0].id
        conversation_export_for_create = conversation_export_domain.ConversationExportForCreate(
            user_id=user_id,
            start_date_time=conversation_export_domain.StartDateTime(root=datetime(2024, 10, 1, 0, 0, 0)),
            end_date_time=conversation_export_domain.EndDateTime(root=datetime(2024, 10, 2, 0, 0, 0)),
            target_bot_id=target_bot_id,
            target_user_id=None,
        )

        # Execute
        output = self.conversation_export_repo.create(conversation_export_for_create)

        # Expected
        expected_output = conversation_export_domain.ConversationExport(
            # created properties
            id=output.id,
            status=output.status,
            # test properties
            user_id=conversation_export_for_create.user_id,
            start_date_time=conversation_export_for_create.start_date_time,
            end_date_time=conversation_export_for_create.end_date_time,
            target_bot_id=conversation_export_for_create.target_bot_id,
            target_user_id=conversation_export_for_create.target_user_id,
        )

        # Test
        assert output == expected_output

        conversation_export_to_delete = (
            self.session.execute(select(ConversationExportModel).where(ConversationExportModel.id == output.id.root))
            .scalars()
            .first()
        )
        self.session.delete(conversation_export_to_delete)
        self.session.commit()

    def test_find_by_id(self, tenant_seed: TenantSeed, conversation_exports_seed: ConversationExportsSeed):
        # Input
        tenant = tenant_seed
        conversation_exports = conversation_exports_seed
        conversation_export = conversation_exports[0]

        # Execute
        found_conversation_export = self.conversation_export_repo.find_by_id(
            tenant_id=tenant.id,
            id=conversation_export.id,
        )

        # Test
        assert found_conversation_export == conversation_export

    def test_find_by_ids_and_tenant_id(
        self, tenant_seed: TenantSeed, conversation_exports_seed: ConversationExportsSeed
    ):
        # Input
        tenant = tenant_seed
        conversation_exports = conversation_exports_seed
        conversation_export_ids = [conversation_export.id for conversation_export in conversation_exports]

        # Execute
        found_conversation_exports = self.conversation_export_repo.find_by_ids_and_tenant_id(
            tenant_id=tenant.id,
            ids=conversation_export_ids,
        )

        # Test
        assert len(found_conversation_exports) > 0

    def test_find_with_user_by_tenant_id(
        self, conversation_exports_seed: ConversationExportsSeed, user_seed: UserSeed
    ):
        user_id, user_for_create, tenant_id, _, _ = user_seed
        conversation_exports = conversation_exports_seed

        conversation_export_to_delete = conversation_exports[4]

        found_conversation_exports = self.conversation_export_repo.find_with_user_by_tenant_id(tenant_id=tenant_id)

        assert conversation_export_to_delete.id not in [export.id for export in found_conversation_exports]

        remaining_exports = [
            export for export in conversation_exports if export.id != conversation_export_to_delete.id
        ]
        assert len(found_conversation_exports) == len(remaining_exports)

        for export, found_export in zip(remaining_exports, found_conversation_exports):
            assert found_export.id == export.id
            assert found_export.user.id == user_id
            assert found_export.user.name == user_for_create.name
            assert found_export.status == export.status

    def test_delete_by_ids_and_tenant_id(
        self, tenant_seed: TenantSeed, conversation_exports_seed: ConversationExportsSeed
    ):
        tenant = tenant_seed
        conversation_exports = conversation_exports_seed
        conversation_export_ids_to_delete = [conversation_exports[0].id, conversation_exports[1].id]
        conversation_export_ids_to_keep = [export.id for export in conversation_exports[2:]]
        conversation_export_id_deleted = conversation_exports[4].id

        for export in conversation_exports:
            if export.id == conversation_export_id_deleted:
                continue
            conversation_export_before = (
                self.session.execute(
                    select(ConversationExportModel).where(ConversationExportModel.id == export.id.root)
                )
                .scalars()
                .first()
            )

            assert conversation_export_before is not None
            assert conversation_export_before.deleted_at is None

        self.conversation_export_repo.delete_by_ids_and_tenant_id(
            tenant_id=tenant.id, ids=conversation_export_ids_to_delete
        )

        for export_id in conversation_export_ids_to_delete:
            conversation_export_after = (
                self.session.execute(
                    select(ConversationExportModel)
                    .filter_by(id=export_id.root)
                    .execution_options(include_deleted=True)
                )
                .scalars()
                .first()
            )

            assert conversation_export_after is not None
            assert conversation_export_after.deleted_at is not None
            assert conversation_export_after.deleted_at <= datetime.utcnow()

        for export_id in conversation_export_ids_to_keep:
            if export_id == conversation_export_id_deleted:
                continue
            conversation_export_not_deleted = (
                self.session.execute(select(ConversationExportModel).filter_by(id=export_id.root)).scalars().first()
            )

            assert conversation_export_not_deleted is not None
            assert conversation_export_not_deleted.deleted_at is None
