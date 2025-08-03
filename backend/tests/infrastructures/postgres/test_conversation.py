from datetime import datetime, timedelta
from typing import Tuple

import pytest
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from api.database import SessionFactory
from api.domain.models import (
    document as document_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.bot import Id as BotId
from api.domain.models.conversation import Conversation, ConversationForCreate, ConversationWithAttachments, Title
from api.domain.models.conversation.conversation_data_point import (
    ConversationDataPointForCreate,
    ConversationDataPointWithTotalGood,
)
from api.domain.models.conversation.conversation_turn import (
    BotOutput,
    Comment,
    ConversationTurn,
    ConversationTurnForCreate,
    Evaluation,
    Query,
    UserInput,
)
from api.domain.models.data_point import (
    AdditionalInfo,
    BlobPath,
    ChunkName,
    CiteNumber,
    Content,
    PageNumber,
    Type,
    Url,
)
from api.domain.models.document import feedback as document_feedback_domain
from api.domain.models.llm import ModelName
from api.domain.models.token import Token, TokenCount, TokenSet
from api.infrastructures.postgres.conversation import ConversationRepository
from api.infrastructures.postgres.models.conversation import Conversation as ConversationModel
from api.infrastructures.postgres.models.conversation_turn import ConversationTurn as ConversationTurnModel
from api.libs.exceptions import NotFound
from tests.conftest import TenantSeed

UserSeed = Tuple[user_domain.Id, user_domain.UserForCreate, tenant_domain.Id, str, user_domain.Id]
ConversationsSeed = Tuple[Conversation, tenant_domain.Id]
ConversationWithTurnsSeed = Tuple[Conversation, list[ConversationTurn]]
UserDocumentSeed = tuple[document_feedback_domain.DocumentFeedback, user_domain.Id, document_domain.Id]


class TestConversationRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.conversation_repo = ConversationRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_save_conversation(self, user_seed: UserSeed):
        """save_conversationメソッドが正常に動作することを確認するテスト"""
        user_id, _, _, _, _ = user_seed
        bot_id = BotId(value=1)

        conversation_for_create = ConversationForCreate(
            user_id=user_id,
            bot_id=bot_id,
        )

        self.conversation_repo.save_conversation(conversation_for_create)

        saved_conversation = (
            self.session.execute(select(ConversationModel).order_by(ConversationModel.created_at.desc()))
            .scalars()
            .first()
        )

        assert saved_conversation is not None
        assert saved_conversation.user_id == user_id.value

    def test_save_conversation_exception(self):
        """save_conversationメソッドが例外を適切に処理することを確認するテスト"""
        with pytest.raises(Exception):
            self.conversation_repo.save_conversation(None)  # type: ignore

    def test_save_conversation_turn(self, conversations_seed: ConversationsSeed):
        """save_conversation_turnメソッドが正常に動作することを確認するテスト"""

        conversation, _ = conversations_seed
        conversation_id = conversation.id
        user_input = UserInput(root="user input")
        bot_output = BotOutput(root="bot output")
        queries = [Query(root="query1"), Query(root="query2")]
        token_set = TokenSet(
            query_input_token=Token(root=1),
            query_output_token=Token(root=2),
            response_input_token=Token(root=3),
            response_output_token=Token(root=4),
        )
        token_count = TokenCount(root=1.0)

        conversation_turn = ConversationTurnForCreate(
            conversation_id=conversation_id,
            user_input=user_input,
            bot_output=bot_output,
            queries=queries,
            token_set=token_set,
            token_count=token_count,
            query_generator_model=ModelName.GPT_35_TURBO,
            response_generator_model=ModelName.GPT_35_TURBO,
            document_folder=None,
        )

        cite_number = CiteNumber(root=1)
        chunk_name = ChunkName(root="chunk_name")
        content = Content(root="content")
        blob_path = BlobPath(root="blob_path")
        page_number = PageNumber(root=1)
        type = Type.INTERNAL
        url = Url(root="url")
        additional_info = AdditionalInfo(root={"key": "value"})

        conversation_data_points = [
            ConversationDataPointForCreate(
                turn_id=conversation_turn.id,
                cite_number=cite_number,
                chunk_name=chunk_name,
                content=content,
                blob_path=blob_path,
                page_number=page_number,
                type=type,
                url=url,
                additional_info=additional_info,
            )
        ]

        returned_conversation_turn = self.conversation_repo.save_conversation_turn(
            conversation_turn, conversation_data_points
        )

        saved_conversation_turn = (
            self.session.execute(
                select(ConversationTurnModel)
                .options(joinedload(ConversationTurnModel.conversation_data_points))
                .order_by(ConversationTurnModel.created_at.desc())
            )
            .scalars()
            .first()
        )

        # 作成されたconversation_turnの確認
        assert saved_conversation_turn is not None
        assert saved_conversation_turn.user_input == user_input.root
        assert saved_conversation_turn.bot_output == bot_output.root
        assert saved_conversation_turn.queries == [query.root for query in queries]
        assert saved_conversation_turn.query_input_token == token_set.query_input_token.root
        assert saved_conversation_turn.query_output_token == token_set.query_output_token.root
        assert saved_conversation_turn.response_input_token == token_set.response_input_token.root
        assert saved_conversation_turn.response_output_token == token_set.response_output_token.root
        assert saved_conversation_turn.token_count == token_count.root
        assert saved_conversation_turn.query_generator_model == ModelName.GPT_35_TURBO
        assert saved_conversation_turn.response_generator_model == ModelName.GPT_35_TURBO
        assert saved_conversation_turn.document_folder_id is None
        assert saved_conversation_turn.conversation_data_points[0].cite_number == cite_number.root
        assert saved_conversation_turn.conversation_data_points[0].chunk_name == chunk_name.root
        assert saved_conversation_turn.conversation_data_points[0].content == content.root
        assert saved_conversation_turn.conversation_data_points[0].blob_path == blob_path.root
        assert saved_conversation_turn.conversation_data_points[0].page_number == page_number.root
        assert saved_conversation_turn.conversation_data_points[0].additional_info == additional_info.root

        # returnされたconversation_turnの確認
        assert returned_conversation_turn is not None
        assert returned_conversation_turn.user_input == user_input
        assert returned_conversation_turn.bot_output == bot_output
        assert returned_conversation_turn.queries == queries
        assert returned_conversation_turn.token_set == token_set
        assert returned_conversation_turn.token_count == token_count
        assert returned_conversation_turn.query_generator_model == ModelName.GPT_35_TURBO
        assert returned_conversation_turn.response_generator_model == ModelName.GPT_35_TURBO
        assert returned_conversation_turn.data_points[0].cite_number == cite_number
        assert returned_conversation_turn.data_points[0].chunk_name == chunk_name
        assert returned_conversation_turn.data_points[0].content == content
        assert returned_conversation_turn.data_points[0].blob_path == blob_path
        assert returned_conversation_turn.data_points[0].page_number == page_number
        assert returned_conversation_turn.data_points[0].additional_info == additional_info

    def test_save_conversation_turn_exception(self):
        """save_conversation_turnメソッドが例外を適切に処理することを確認するテスト"""
        with pytest.raises(Exception):
            self.conversation_repo.save_conversation_turn(None)  # type: ignore

    def test_find_conversation_turns_by_user_ids_bot_ids_and_date(
        self, conversation_with_turns_seed: ConversationWithTurnsSeed
    ):
        """find_conversation_turns_by_user_ids_bot_ids_and_dateメソッドが正常に動作することを確認するテスト"""
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        conversation, conversation_turns = conversation_with_turns_seed
        user_id = conversation.user_id
        bot_id = conversation.bot_id

        # テスト実行
        retrieved_turns = self.conversation_repo.find_conversation_turns_by_user_ids_bot_ids_and_date(
            bot_ids=[bot_id],
            user_ids=[user_id],
            start_date_time=start_date,
            end_date_time=end_date,
        )

        # 検証
        retrieved_turn_ids = {turn.id.root for turn in retrieved_turns}

        for turn in conversation_turns:
            if (
                conversation.bot_id.value == bot_id
                and conversation.user_id.value == user_id
                and start_date <= turn.created_at.root <= end_date
            ):
                assert turn.id.root in retrieved_turn_ids, (
                    f"条件に合致するターン（ID: {turn.id.root}）が取得されていません。"
                    f"created_at: {turn.created_at.root}"
                )
            else:
                assert turn.id.root not in retrieved_turn_ids, (
                    f"条件に合致しないターン（ID: {turn.id.root}）が誤って取得されています。"
                    f"bot_id: {conversation.bot_id.value}, user_id: {conversation.user_id.value}, "
                    f"created_at: {turn.created_at.root}"
                )

        # 追加の検証：取得されたターンの数が正しいことを確認
        expected_turns_count = sum(
            1
            for turn in conversation_turns
            if conversation.bot_id.value == bot_id
            and conversation.user_id.value == user_id
            and start_date <= turn.created_at.root <= end_date
        )
        assert (
            len(retrieved_turns) == expected_turns_count
        ), f"取得されたターンの数が期待値と一致しません。期待値: {expected_turns_count}, 実際: {len(retrieved_turns)}"

    def test_find_conversation_turns_by_user_ids_bot_ids_and_date_with_invalid_ids(self):
        """無効なユーザーIDまたはボットIDが指定された場合のテスト"""
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        user_id = user_domain.Id(value=0)  # 存在しないユーザーID
        bot_id = BotId(value=0)  # 存在しないボットID

        # テスト実行
        conversation_turns = self.conversation_repo.find_conversation_turns_by_user_ids_bot_ids_and_date(
            bot_ids=[bot_id],
            user_ids=[user_id],
            start_date_time=start_date,
            end_date_time=end_date,
        )

        # 検証
        assert conversation_turns == []  # 無効なIDの場合、結果は空のリストになるべき

    def test_find_turns_by_id_and_bot_id(
        self,
        conversation_with_turns_seed: ConversationWithTurnsSeed,
    ):
        """find_turns_by_id_and_bot_idメソッドが正常に動作することを確認するテスト"""
        conversation, conversation_turns = conversation_with_turns_seed

        conversation_id = conversation.id
        bot_id = conversation.bot_id
        user_input = conversation_turns[0].user_input
        bot_output = conversation_turns[0].bot_output

        # テスト実行
        new_turns = self.conversation_repo.find_turns_by_id_and_bot_id(bot_id, conversation_id)
        new_turn = new_turns[0]

        # 検証
        assert len(new_turns) >= 1
        assert new_turn.user.root == user_input.root
        if bot_output is not None and new_turn.bot is not None:
            assert new_turn.bot.root == bot_output.root

    def test_find_with_bot_by_id_and_bot_id_and_user_id(
        self,
        conversation_with_turns_seed: ConversationWithTurnsSeed,
    ):
        """find_with_bot_by_id_and_bot_id_and_user_idメソッドが正常に動作することを確認するテスト"""
        conversation, conversation_turns = conversation_with_turns_seed
        conversation_id = conversation.id
        bot_id = conversation.bot_id
        user_id = conversation.user_id

        # テスト実行
        new_conversation = self.conversation_repo.find_with_bot_by_id_and_bot_id_and_user_id(
            conversation_id, bot_id, user_id
        )

        # テスト用に created_at を削除
        for turn in new_conversation.turns:
            if hasattr(turn, "created_at"):
                del turn.created_at

        for turn in conversation_turns:
            if hasattr(turn, "created_at"):
                del turn.created_at

        # 検証
        assert new_conversation.id == conversation_id
        assert new_conversation.bot_id == bot_id
        assert new_conversation.user_id == user_id
        assert new_conversation.bot.id == bot_id
        assert new_conversation.title == conversation.title
        assert new_conversation.turns == conversation_turns

    def test_find_by_user_id(self, conversations_seed: ConversationsSeed):
        """finds_by_user_idメソッドが正常に動作することを確認するテスト"""
        conversation, tenant_id = conversations_seed
        user_id = conversation.user_id

        offset = 0
        limit = 10

        # テスト実行
        conversations = self.conversation_repo.find_by_user_id(
            tenant_id,
            user_id,
            offset,
            limit,
        )

        # 検証
        assert len(conversations) >= 1
        assert conversations[0].user_id == user_id
        assert conversations[0].id == conversation.id
        assert all(convo.user_id == user_id for convo in conversations)

    def test_update_conversation_timestamp(self, conversations_seed: ConversationsSeed):
        """update_conversation_timestampメソッドが正常に動作することを確認するテスト"""
        conversation, _ = conversations_seed
        conversation_id = conversation.id
        self.conversation_repo.update_conversation_timestamp(conversation_id)
        new_conversation = (
            self.session.execute(select(ConversationModel).where(ConversationModel.id == conversation_id.root))
            .scalars()
            .first()
        )
        assert new_conversation is not None
        assert new_conversation.created_at is not None
        assert new_conversation.updated_at is not None
        assert new_conversation.updated_at > new_conversation.created_at
        assert new_conversation.updated_at > datetime.now() - timedelta(seconds=1)
        assert new_conversation.updated_at < datetime.now() + timedelta(seconds=1)

    def test_update_evaluation(self, conversation_with_turns_seed: ConversationWithTurnsSeed):
        """update_evaluationメソッドが正常に動作することを確認するテスト"""
        conversation, conversation_turns = conversation_with_turns_seed
        conversation_turn = conversation_turns[0]
        new_feedback = Evaluation.GOOD
        self.conversation_repo.update_evaluation(conversation.id, conversation_turn.id, new_feedback)
        new_conversation_turn = (
            self.session.execute(
                select(ConversationTurnModel).where(ConversationTurnModel.id == conversation_turn.id.root)
            )
            .scalars()
            .first()
        )
        assert new_conversation_turn is not None
        assert new_conversation_turn.evaluation == new_feedback

    def test_find_by_id(self, conversation_with_turns_attachment_seed: ConversationWithAttachments):
        """find_by_idメソッドが正常に動作することを確認するテスト"""
        conversation = conversation_with_turns_attachment_seed
        conversation_id = conversation.id
        user_id = conversation.user_id

        # テスト実行
        new_conversation = self.conversation_repo.find_by_id(conversation_id, user_id)

        # テスト用に created_at を削除
        for turn in new_conversation.conversation_turns:
            if hasattr(turn, "created_at"):
                del turn.created_at

        for turn in conversation.conversation_turns:
            if hasattr(turn, "created_at"):
                del turn.created_at
        # 検証
        assert new_conversation.id == conversation_id
        assert new_conversation.user_id == user_id
        assert new_conversation.bot_id == conversation.bot_id
        assert new_conversation.title == conversation.title
        assert new_conversation.id.root == conversation_id.root
        assert new_conversation.conversation_turns == conversation.conversation_turns

    def test_update_conversation_title(self, conversations_seed: ConversationsSeed):
        """update_conversation_titleメソッドが正常に動作することを確認するテスト"""
        conversation, _ = conversations_seed
        conversation_id = conversation.id
        new_title = Title(root="new title")

        # テスト実行
        self.conversation_repo.update_conversation(conversation_id, conversation.user_id, new_title, None)

        # 検証
        updated_conversation = (
            self.session.execute(select(ConversationModel).where(ConversationModel.id == conversation_id.root))
            .scalars()
            .first()
        )
        assert updated_conversation is not None
        assert updated_conversation.title == new_title.root

    def test_update_conversation_is_archived(self, conversations_seed: ConversationsSeed):
        """update_conversation_is_archivedメソッドが正常に動作することを確認するテスト"""
        conversation, _ = conversations_seed
        conversation_id = conversation.id
        is_archived = True

        # テスト実行
        self.conversation_repo.update_conversation(conversation_id, conversation.user_id, None, is_archived)

        # 検証
        updated_conversation = (
            self.session.execute(select(ConversationModel).where(ConversationModel.id == conversation_id.root))
            .scalars()
            .first()
        )
        assert updated_conversation is not None
        assert updated_conversation.archived_at is not None
        assert updated_conversation.archived_at > datetime.now() - timedelta(seconds=1)
        assert updated_conversation.archived_at < datetime.now() + timedelta(seconds=1)

    def test_save_conversation_title(self, conversations_seed: ConversationsSeed):
        """save_conversation_titleメソッドが正常に動作することを確認するテスト"""
        conversation, _ = conversations_seed
        conversation_id = conversation.id
        new_title = Title(root="new title")

        # テスト実行
        self.conversation_repo.save_conversation_title(conversation_id, new_title)

        conv = self.conversation_repo.find_by_id(conversation_id, conversation.user_id)

        # 検証
        assert conv.title == new_title

    def test_find_with_total_good_by_user_id_and_id_and_turn_id(
        self, conversation_with_turns_seed: ConversationWithTurnsSeed, user_document_seed: UserDocumentSeed
    ):
        # Input
        conversation, conversation_turns = conversation_with_turns_seed
        conversation_turn = conversation_turns[0]
        data_points = conversation_turn.data_points
        _, user_id, _ = user_document_seed

        # Expected
        expected_output = [
            ConversationDataPointWithTotalGood(
                **data_point.model_dump(),
                total_good=0,
            )
            for data_point in data_points
        ]

        # Execute
        output = self.conversation_repo.find_data_points_with_total_good_by_user_id_and_id_and_turn_id(
            user_id, conversation.id, conversation_turn.id
        )

        # Test
        assert output == expected_output

    @pytest.mark.parametrize("conversation_with_turns_seed", [{"cleanup_resources": False}], indirect=True)
    def test_delete_by_bot_id(self, conversation_with_turns_seed: ConversationWithTurnsSeed):
        conversation, _ = conversation_with_turns_seed
        bot_id = conversation.bot_id

        self.conversation_repo.delete_by_bot_id(bot_id)

        with pytest.raises(NotFound):
            self.conversation_repo.find_by_id(conversation.id, conversation.user_id)

    def test_save_comment(self, conversation_with_turns_seed: ConversationWithTurnsSeed):
        """save_commentメソッドが正常に動作することを確認するテスト"""
        conversation, conversation_turns = conversation_with_turns_seed
        conversation_id = conversation.id
        conversation_turn = conversation_turns[0]
        comment = Comment(root="comment")

        # テスト実行
        self.conversation_repo.save_comment(conversation_id, conversation_turn.id, comment)

        # 検証
        updated_conversation_turn = (
            self.session.execute(
                select(ConversationTurnModel).where(ConversationTurnModel.id == conversation_turn.id.root)
            )
            .scalars()
            .first()
        )
        assert updated_conversation_turn is not None
        assert updated_conversation_turn.comment == comment.root

    @pytest.mark.parametrize("conversation_with_turns_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_user_ids(self, conversation_with_turns_seed: ConversationWithTurnsSeed):
        """会話履歴物理削除テスト"""
        conversation, _ = conversation_with_turns_seed
        user_id = conversation.user_id

        self.conversation_repo.delete_by_bot_id(conversation.bot_id)
        self.conversation_repo.hard_delete_by_user_ids([user_id])

        turns = (
            self.session.execute(
                select(ConversationTurnModel)
                .where(ConversationTurnModel.conversation_id == conversation.id.root)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .unique()
            .all()
        )
        assert len(turns) == 0
        conversations = (
            self.session.execute(
                select(ConversationModel)
                .where(ConversationModel.user_id == user_id.value)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .unique()
            .all()
        )
        assert len(conversations) == 0

    def test_get_conversation_token_count_by_tenant_id(
        self, tenant_seed: TenantSeed, conversation_with_turns_seed: ConversationWithTurnsSeed
    ):
        """get_conversation_token_count_by_tenant_idメソッドが正常に動作することを確認するテスト"""
        _, conversation_turns = conversation_with_turns_seed
        tenant = tenant_seed
        tenant_id = tenant.id
        # 現在より2日前から2日後までの期間を設定
        start_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
        end_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2)

        want = TokenCount(root=sum(turn.token_count.root for turn in conversation_turns))

        got = self.conversation_repo.get_conversation_token_count_by_tenant_id(
            tenant_id, start_date_time, end_date_time
        )
        assert got == want
