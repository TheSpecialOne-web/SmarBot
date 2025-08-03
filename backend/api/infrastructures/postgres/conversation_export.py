from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from api.domain.models import (
    conversation_export as conversation_export_domain,
    tenant as tenant_domain,
)
from api.libs.exceptions import NotFound

from .models.conversation_export import ConversationExport as ConversationExportModel
from .models.tenant import Tenant
from .models.user import User


class ConversationExportRepository(conversation_export_domain.IConversationExportRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(
        self, conversation_export: conversation_export_domain.ConversationExportForCreate
    ) -> conversation_export_domain.ConversationExport:
        new_conversation_export = ConversationExportModel.from_domain(conversation_export)

        try:
            self.session.add(new_conversation_export)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return new_conversation_export.to_domain()

    def find_by_id(
        self, tenant_id: tenant_domain.Id, id: conversation_export_domain.Id
    ) -> conversation_export_domain.ConversationExport:
        stmt = (
            select(ConversationExportModel)
            .where(ConversationExportModel.id == id.root)
            .join(User, User.id == ConversationExportModel.user_id)
            .join(Tenant, Tenant.id == User.tenant_id)
            .where(Tenant.id == tenant_id.value)
        )
        conversation_export = self.session.execute(stmt).scalars().first()
        if conversation_export is None:
            raise NotFound("指定された会話履歴エクスポートは存在しません")
        return conversation_export.to_domain()

    def find_by_ids_and_tenant_id(
        self, tenant_id: tenant_domain.Id, ids: list[conversation_export_domain.Id]
    ) -> list[conversation_export_domain.ConversationExport]:
        stmt = (
            select(ConversationExportModel)
            .where(ConversationExportModel.id.in_([id.root for id in ids]))
            .join(User, User.id == ConversationExportModel.user_id)
            .where(User.tenant_id == tenant_id.value)
        )
        conversation_exports = self.session.execute(stmt).scalars().all()
        return [conversation_export.to_domain() for conversation_export in conversation_exports]

    def find_with_user_by_tenant_id(
        self, tenant_id: tenant_domain.Id
    ) -> list[conversation_export_domain.ConversationExportWithUser]:
        stmt = (
            select(ConversationExportModel)
            .join(User, User.id == ConversationExportModel.user_id)
            .where(User.tenant_id == tenant_id.value)
            .options(joinedload(ConversationExportModel.user).joinedload(User.policies))
        )
        results = self.session.execute(stmt).unique().scalars().all()

        return [result.to_domain_with_user() for result in results]

    def update(self, conversation_export: conversation_export_domain.ConversationExport) -> None:
        try:
            self.session.execute(
                update(ConversationExportModel)
                .where(ConversationExportModel.id == conversation_export.id.root)
                .values(
                    status=conversation_export.status.value,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_ids_and_tenant_id(
        self, tenant_id: tenant_domain.Id, ids: list[conversation_export_domain.Id]
    ) -> None:
        try:
            # Step 1: Create a subquery to select ConversationExportModel IDs
            subquery = (
                select(ConversationExportModel.id)
                .join(User, User.id == ConversationExportModel.user_id)
                .where(User.tenant_id == tenant_id.value, ConversationExportModel.id.in_([id.root for id in ids]))
                .scalar_subquery()
            )

            # Step 2: Use the subquery in the update statement
            self.session.execute(
                update(ConversationExportModel)
                .where(ConversationExportModel.id.in_(subquery))
                .values(deleted_at=datetime.now(timezone.utc), status=conversation_export_domain.Status.DELETED)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
