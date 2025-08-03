from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    user as user_domain,
)
from api.domain.models.conversation import conversation_turn as conversation_turn_domain
from api.libs.exceptions import NotFound

from .models.attachment import Attachment


class AttachmentRepository(attachment_domain.IAttachmentRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        bot_id: bot_domain.Id,
        user_id: user_domain.Id,
        attachment: attachment_domain.AttachmentForCreate,
    ) -> attachment_domain.Attachment:
        try:
            new_attachment = Attachment.from_domain(
                attachment=attachment,
                bot_id=bot_id,
                user_id=user_id,
            )
            self.session.add(new_attachment)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return new_attachment.to_domain()

    def find_by_id(self, id: attachment_domain.Id) -> attachment_domain.Attachment:
        attachment = self.session.execute(select(Attachment).filter_by(id=id.root)).scalars().first()
        if not attachment:
            raise NotFound("添付ファイルが見つかりませんでした")

        return attachment.to_domain()

    def delete(self, id: attachment_domain.Id) -> None:
        try:
            attachment = self.session.execute(select(Attachment).filter_by(id=id.root)).scalars().first()
            if not attachment:
                raise NotFound("添付ファイルが見つかりませんでした")
            attachment.deleted_at = datetime.utcnow()
            attachment.is_blob_deleted = True
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    # 複数のatttachmentのconversation_turn_idを更新する
    def update_conversation_turn_ids(
        self, ids: list[attachment_domain.Id], conversation_turn_id: conversation_turn_domain.Id
    ) -> None:
        try:
            id_values = [id.root for id in ids]
            self.session.execute(
                update(Attachment)
                .where(Attachment.id.in_(id_values))
                .values(
                    conversation_turn_id=conversation_turn_id.root,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_attachments_by_bot_id_after_24_hours(self, bot_id: bot_domain.Id) -> list[attachment_domain.Attachment]:
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        query = self.session.execute(
            select(Attachment)
            .where(Attachment.bot_id == bot_id.value)
            .where(Attachment.created_at <= cutoff_time)
            .where(Attachment.is_blob_deleted.is_(False))
        ).scalars()
        attachments = query.all()
        return [attachment.to_domain() for attachment in attachments]

    def update_blob_deleted(self, attachment_id: attachment_domain.Id) -> None:
        attachment = (
            self.session.execute(select(Attachment).where(Attachment.id == attachment_id.root)).scalars().first()
        )
        if not attachment:
            raise NotFound("添付ファイルが見つかりませんでした")
        attachment.is_blob_deleted = True
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_bot_id(self, bot_id: bot_domain.Id) -> None:
        try:
            self.session.execute(
                update(Attachment)
                .where(Attachment.bot_id == bot_id.value)
                .values(deleted_at=datetime.now(timezone.utc))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_bot_ids(self, bot_ids: list[bot_domain.Id]) -> None:
        bot_id_values = [bot_id.value for bot_id in bot_ids]
        try:
            self.session.execute(
                delete(Attachment).where(Attachment.bot_id.in_(bot_id_values)).where(Attachment.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
