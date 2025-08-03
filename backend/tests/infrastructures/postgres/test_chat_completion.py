from datetime import datetime, timedelta
import uuid

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    api_key as ak_domain,
    bot as bot_domain,
    chat_completion as cc_domain,
    data_point as dp_domain,
    document as document_domain,
    question_answer as qa_domain,
    token as token_domain,
    user as user_domain,
)
from api.domain.models.chat_completion import data_point as cc_dp_domain
from api.domain.models.token import TokenCount
from api.infrastructures.postgres.api_key import ApiKeyRepository
from api.infrastructures.postgres.chat_completion import ChatCompletionRepository
from api.infrastructures.postgres.document import DocumentRepository
from api.infrastructures.postgres.document_folder import DocumentFolderRepository
from api.infrastructures.postgres.models.chat_completion import ChatCompletion
from api.infrastructures.postgres.models.chat_completion_data_point import (
    ChatCompletionDataPoint,
)
from api.infrastructures.postgres.question_answer import QuestionAnswerRepository
from tests.conftest import TenantSeed

ChatCompletionsSeed = tuple[bot_domain.Id, list[tuple[ak_domain.ApiKey, cc_domain.ChatCompletion]]]
ApiKeySeed = tuple[ak_domain.ApiKey, bot_domain.Bot]


class TestChatCompletionRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.api_key_repo = ApiKeyRepository(self.session)
        self.chat_completion_repo = ChatCompletionRepository(self.session)
        self.document_folder_repo = DocumentFolderRepository(self.session)
        self.document_repo = DocumentRepository(self.session)
        self.qa_repo = QuestionAnswerRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_create(self, api_key_seed: ApiKeySeed):
        api_key, bot = api_key_seed
        bot_id = bot.id

        chat_completion_id = cc_domain.Id(root=uuid.uuid4())
        chat_completion_data_point_id = cc_dp_domain.Id(root=uuid.uuid4())
        chat_completion_data_point_id_2 = cc_dp_domain.Id(root=uuid.uuid4())
        chat_completion_data_point_id_3 = cc_dp_domain.Id(root=uuid.uuid4())

        document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(bot_id)
        document = self.document_repo.create(
            bot_id=bot_id,
            parent_document_folder_id=document_folder.id,
            document=document_domain.DocumentForCreate(
                name=document_domain.Name(value="test_create_chat_completion_document_name"),
                memo=document_domain.Memo(value="test_create_chat_completion_document_memo"),
                file_extension=document_domain.FileExtension.PDF,
                status=document_domain.Status.COMPLETED,
                data=b"test_create_chat_completion_document_data",
                creator_id=user_domain.Id(value=1),
            ),
        )

        question_answer = self.qa_repo.create(
            bot_id=bot_id,
            question_answer=qa_domain.QuestionAnswerForCreate(
                question=qa_domain.Question(root="test_create_chat_completion_question"),
                answer=qa_domain.Answer(root="test_create_chat_completion_answer"),
                status=qa_domain.Status.INDEXED,
            ),
        )

        chat_completion = cc_domain.ChatCompletion(
            id=chat_completion_id,
            messages=cc_domain.Messages(
                root=[
                    cc_domain.Message(
                        role=cc_domain.Role.USER,
                        content=cc_domain.Content(root="test_create_chat_completion_content"),
                    )
                ]
            ),
            answer=cc_domain.Content(root="test_create_chat_completion_answer"),
            token_count=token_domain.TokenCount(root=100.0),
            data_points=[
                cc_dp_domain.ChatCompletionDataPoint(
                    id=chat_completion_data_point_id,
                    document_id=document.id,
                    question_answer_id=None,
                    cite_number=dp_domain.CiteNumber(root=1),
                    chunk_name=dp_domain.ChunkName(root="test_create_chat_completion_chunk_name"),
                    content=dp_domain.Content(root="test_create_chat_completion_content"),
                    blob_path=dp_domain.BlobPath(root="test.pdf"),
                    page_number=dp_domain.PageNumber(root=1),
                    additional_info=None,
                    url=dp_domain.Url(root=""),
                    type=dp_domain.Type.INTERNAL,
                ),
                cc_dp_domain.ChatCompletionDataPoint(
                    id=chat_completion_data_point_id_2,
                    document_id=None,
                    question_answer_id=question_answer.id,
                    cite_number=dp_domain.CiteNumber(root=2),
                    chunk_name=dp_domain.ChunkName(root="test_create_chat_completion_chunk_name"),
                    content=dp_domain.Content(root="test_create_chat_completion_content"),
                    blob_path=dp_domain.BlobPath(root=""),
                    page_number=dp_domain.PageNumber(root=0),
                    additional_info=None,
                    url=dp_domain.Url(root=""),
                    type=dp_domain.Type.QUESTION_ANSWER,
                ),
                cc_dp_domain.ChatCompletionDataPoint(
                    id=chat_completion_data_point_id_3,
                    document_id=None,
                    question_answer_id=None,
                    cite_number=dp_domain.CiteNumber(root=3),
                    chunk_name=dp_domain.ChunkName(root="test_create_chat_completion_chunk_name"),
                    content=dp_domain.Content(root="test_create_chat_completion_content"),
                    blob_path=dp_domain.BlobPath(root=""),
                    page_number=dp_domain.PageNumber(root=0),
                    additional_info=None,
                    url=dp_domain.Url(root="https://example.com"),
                    type=dp_domain.Type.WEB,
                ),
            ],
        )

        self.chat_completion_repo.create(api_key_id=api_key.id, chat_completion=chat_completion)

        created_chat_completion = (
            self.session.execute(select(ChatCompletion).where(ChatCompletion.id == chat_completion_id.root))
            .scalars()
            .first()
        )
        if created_chat_completion is None:
            raise Exception("ChatCompletion not created")
        domain_chat_completion = created_chat_completion.to_domain()
        domain_chat_completion.created_at = None
        chat_completion.created_at = None
        assert domain_chat_completion == chat_completion

    def test_find_by_api_key_ids_and_date(self, chat_completions_seed: ChatCompletionsSeed):
        _, chat_completions_with_api_key = chat_completions_seed

        chat_completions_with_api_key_id = [
            cc_domain.ChatCompletionWithApiKeyId(
                id=chat_completion.id,
                api_key_id=api_key.id,
                created_at=chat_completion.created_at,
                messages=chat_completion.messages,
                answer=chat_completion.answer,
                token_count=chat_completion.token_count,
                data_points=chat_completion.data_points,
            )
            for api_key, chat_completion in chat_completions_with_api_key
        ]

        got = self.chat_completion_repo.find_by_api_key_ids_and_date(
            api_key_ids=[api_key.id for api_key, _ in chat_completions_with_api_key],
            start_date_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1),
            end_date_time=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1),
        )
        assert len(got) == len(chat_completions_with_api_key_id)
        # created_atがchat_completions_with_api_key_idにないため
        for g, e in zip(got, chat_completions_with_api_key_id):
            g_dict = g.model_dump(exclude={"created_at"})
            e_dict = e.model_dump(exclude={"created_at"})
            assert g_dict == e_dict

    def test_update_chat_completion_feedback_evaluation(self, chat_completions_seed: ChatCompletionsSeed):
        # Given
        _, chat_completions_with_api_key = chat_completions_seed
        chat_completion = chat_completions_with_api_key[0][1]
        chat_completion_id = chat_completion.id
        evaluation = cc_domain.Evaluation("good")

        # Call the method
        self.chat_completion_repo.update_chat_completion_feedback_evaluation(chat_completion.id, evaluation)

        # Assertions
        found_chat_completion = (
            self.session.execute(select(ChatCompletion).where(ChatCompletion.id == chat_completion_id.root))
            .scalars()
            .first()
        )
        if not found_chat_completion:
            raise Exception("Chat Completion is not found")
        assert found_chat_completion.evaluation == evaluation

    def test_update_chat_completion_feedback_comment(self, chat_completions_seed: ChatCompletionsSeed):
        # Given
        _, chat_completions_with_api_key = chat_completions_seed
        chat_completion = chat_completions_with_api_key[0][1]
        chat_completion_id = chat_completion.id
        comment = cc_domain.Comment(root="Thank you")

        # Call the method
        self.chat_completion_repo.update_chat_completion_feedback_comment(chat_completion.id, comment)

        # Assertions
        found_chat_completion = (
            self.session.execute(select(ChatCompletion).where(ChatCompletion.id == chat_completion_id.root))
            .scalars()
            .first()
        )
        if not found_chat_completion:
            raise Exception("Chat Completion is not found")
        assert found_chat_completion.comment == comment.root

    @pytest.mark.parametrize("chat_completions_seed", [{"cleanup_resources": False}], indirect=True)
    def test_delete_completions_and_data_points_by_bot_id(self, chat_completions_seed: ChatCompletionsSeed):
        bot_id, chat_completions_with_api_key = chat_completions_seed

        self.chat_completion_repo.delete_completions_and_data_points_by_bot_id(bot_id)

        data_points = (
            self.session.execute(
                select(ChatCompletionDataPoint).where(
                    ChatCompletionDataPoint.chat_completion_id.in_(
                        [cc.id.root for _, cc in chat_completions_with_api_key]
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(data_points) == 0

        completions = (
            self.session.execute(
                select(ChatCompletion).where(
                    ChatCompletion.id.in_([cc.id.root for _, cc in chat_completions_with_api_key])
                )
            )
            .unique()
            .scalars()
            .all()
        )
        assert len(completions) == 0

    @pytest.mark.parametrize("chat_completions_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_api_key_ids(self, chat_completions_seed: ChatCompletionsSeed):
        bot_id, chat_completions_with_api_key = chat_completions_seed
        api_key_ids = [api_key.id for api_key, _ in chat_completions_with_api_key]

        self.chat_completion_repo.delete_completions_and_data_points_by_bot_id(bot_id)
        self.chat_completion_repo.hard_delete_by_api_key_ids(api_key_ids)

        data_points = (
            self.session.execute(
                select(ChatCompletionDataPoint)
                .where(
                    ChatCompletionDataPoint.chat_completion_id.in_(
                        [cc.id.root for _, cc in chat_completions_with_api_key]
                    )
                )
                .execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )
        assert len(data_points) == 0
        completions = (
            self.session.execute(
                select(ChatCompletion)
                .where(ChatCompletion.id.in_([cc.id.root for _, cc in chat_completions_with_api_key]))
                .execution_options(include_deleted=True)
            )
            .unique()
            .scalars()
            .all()
        )
        assert len(completions) == 0

    def test_get_chat_completion_token_count_by_tenant_id(
        self, tenant_seed: TenantSeed, chat_completions_seed: ChatCompletionsSeed
    ):
        _, chat_completions_with_api_key = chat_completions_seed

        tenant_id = tenant_seed.id
        start_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        end_date_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        want = sum([cc.token_count.root for _, cc in chat_completions_with_api_key])
        got = self.chat_completion_repo.get_chat_completion_token_count_by_tenant_id(
            tenant_id, start_date_time, end_date_time
        )
        assert got == TokenCount(root=want)
