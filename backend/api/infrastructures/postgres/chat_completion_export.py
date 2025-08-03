from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from api.domain.models import (
    chat_completion_export as chat_completion_export_domain,
    tenant as tenant_domain,
)
from api.infrastructures.postgres.models.chat_completion_export import (
    ChatCompletionExport as ChatCompletionExportModel,
)
from api.infrastructures.postgres.models.user import User
from api.libs.exceptions import NotFound


class ChatCompletionExportRepository(chat_completion_export_domain.IChatCompletionExportRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(
        self, chat_completion_export: chat_completion_export_domain.ChatCompletionExportForCreate
    ) -> chat_completion_export_domain.ChatCompletionExportWithUser:
        new_chat_completion_export = ChatCompletionExportModel.from_domain(chat_completion_export)

        try:
            self.session.add(new_chat_completion_export)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return new_chat_completion_export.to_domain_with_user()

    def find_by_id(
        self, tenant_id: tenant_domain.Id, id: chat_completion_export_domain.Id
    ) -> chat_completion_export_domain.ChatCompletionExport:
        stmt = (
            select(ChatCompletionExportModel)
            .where(ChatCompletionExportModel.id == id.root)
            .join(User, User.id == ChatCompletionExportModel.creator_id)
            .where(User.tenant_id == tenant_id.value)
        )
        chat_completion_export = self.session.execute(stmt).scalars().first()
        if chat_completion_export is None:
            raise NotFound("指定された会話履歴エクスポートは存在しません")
        return chat_completion_export.to_domain()

    def find_by_ids_and_tenant_id(
        self, tenant_id: tenant_domain.Id, ids: list[chat_completion_export_domain.Id]
    ) -> list[chat_completion_export_domain.ChatCompletionExport]:
        stmt = (
            select(ChatCompletionExportModel)
            .where(ChatCompletionExportModel.id.in_([id.root for id in ids]))
            .join(User, User.id == ChatCompletionExportModel.creator_id)
            .where(User.tenant_id == tenant_id.value)
        )
        chat_completion_exports = self.session.execute(stmt).scalars().all()
        return [chat_completion_export.to_domain() for chat_completion_export in chat_completion_exports]

    def update(self, chat_completion_export: chat_completion_export_domain.ChatCompletionExport) -> None:
        try:
            self.session.execute(
                update(ChatCompletionExportModel)
                .where(ChatCompletionExportModel.id == chat_completion_export.id.root)
                .values(
                    status=chat_completion_export.status.value,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_with_user_by_tenant_id(
        self, tenant_id: tenant_domain.Id
    ) -> list[chat_completion_export_domain.ChatCompletionExportWithUser]:
        stmt = (
            select(ChatCompletionExportModel)
            .join(User, User.id == ChatCompletionExportModel.creator_id)
            .where(User.tenant_id == tenant_id.value)
            .options(joinedload(ChatCompletionExportModel.creator))
        )
        results = self.session.execute(stmt).unique().scalars().all()

        return [result.to_domain_with_user() for result in results]

    def delete_by_ids_and_tenant_id(
        self, tenant_id: tenant_domain.Id, ids: list[chat_completion_export_domain.Id]
    ) -> None:
        try:
            self.session.execute(
                update(ChatCompletionExportModel)
                .where(
                    ChatCompletionExportModel.id.in_([id.root for id in ids]),
                    ChatCompletionExportModel.creator_id == User.id,
                    User.tenant_id == tenant_id.value,
                )
                .values(deleted_at=datetime.now(timezone.utc), status=chat_completion_export_domain.Status.DELETED)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
