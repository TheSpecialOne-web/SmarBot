from typing import Tuple

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    tenant as tenant_domain,
)
from api.domain.models.conversation import (
    Conversation,
    conversation_turn as conversation_turn_domain,
)
from api.infrastructures.postgres.attachment import AttachmentRepository
from api.infrastructures.postgres.models.attachment import Attachment as AttachmentModel
from api.libs.exceptions import NotFound

BotsSeed = Tuple[list[bot_domain.Bot], list[dict], tenant_domain.Tenant]
AttachmentSeed = Tuple[attachment_domain.Attachment, attachment_domain.AttachmentForCreate, bot_domain.Id]
ConversationTurnSeed = Tuple[conversation_turn_domain.ConversationTurn]


class TestAttachmentRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.attachment_repo = AttachmentRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_create(self, attachment_seed: AttachmentSeed):
        """新しいアタッチメントを作成するテスト"""
        new_attachment, _, _ = attachment_seed

        # データベースに新しいアタッチメントが保存されていることを確認
        saved_attachment = self.attachment_repo.find_by_id(new_attachment.id)
        assert saved_attachment == new_attachment

    def test_find_by_id(self, attachment_seed: AttachmentSeed):
        """存在するattachment.id"""
        new_attachment, _, _ = attachment_seed

        attachment = self.attachment_repo.find_by_id(new_attachment.id)

        assert attachment == new_attachment

    def test_update_conversation_turn_ids(
        self,
        attachment_seed: AttachmentSeed,
        conversation_with_turns_seed: Tuple[Conversation, list[conversation_turn_domain.ConversationTurn]],
    ):
        """update_conversation_turn_idsメソッドが正常に動作することを確認するテスト"""
        attachment, _, _ = attachment_seed
        _, conversation_turns = conversation_with_turns_seed

        conversation_turn = conversation_turns[0]
        new_conversation_turn_id = conversation_turn.id
        self.attachment_repo.update_conversation_turn_ids([attachment.id], new_conversation_turn_id)
        new_attachment = (
            self.session.execute(select(AttachmentModel).where(AttachmentModel.id == attachment.id.root))
            .scalars()
            .first()
        )
        assert new_attachment is not None
        assert new_attachment.conversation_turn_id == new_conversation_turn_id.root

    @pytest.mark.parametrize("attachment_seed", [{"cleanup_resources": False}], indirect=True)
    def test_delete_by_bot_id(self, attachment_seed: AttachmentSeed):
        """アタッチメント削除テスト"""
        attachment, _, bot_id = attachment_seed

        self.attachment_repo.delete_by_bot_id(bot_id)

        with pytest.raises(NotFound):
            self.attachment_repo.find_by_id(attachment.id)

    @pytest.mark.parametrize("attachment_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_bot_ids(self, attachment_seed: AttachmentSeed):
        """アタッチメントの物理削除テスト"""
        attachment, _, bot_id = attachment_seed

        self.attachment_repo.delete_by_bot_id(bot_id)
        self.attachment_repo.hard_delete_by_bot_ids([bot_id])

        found_attachment = (
            self.session.execute(
                select(AttachmentModel)
                .where(AttachmentModel.id == attachment.id.root)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .first()
        )

        assert found_attachment is None
