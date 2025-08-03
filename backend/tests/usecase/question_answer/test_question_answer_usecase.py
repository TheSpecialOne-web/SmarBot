import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from api.domain.models import (
    bot as bot_domain,
    llm as llm_domain,
    question_answer as question_answer_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.libs.exceptions import BadRequest, NotFound
from api.usecase.question_answer.question_answer import (
    BulkCreateQuestionAnswersInput,
    IndexQuestionAnswerForCreate,
    IndexQuestionAnswerForUpdate,
    QuestionAnswerForBulkCreateOrUpdate,
    QuestionAnswerUseCase,
)


class TestQuestionAnswerUsecase:
    @pytest.fixture
    def setup(self):
        self.question_answer_repo = Mock()
        self.llm_service = Mock()
        self.cognitive_search_service = Mock()
        self.queue_storage_service = Mock()

        self.question_usecase = QuestionAnswerUseCase(
            question_answer_repo=self.question_answer_repo,
            llm_service=self.llm_service,
            cognitive_search_service=self.cognitive_search_service,
            queue_storage_service=self.queue_storage_service,
        )

    def dummy_tenant(self) -> tenant_domain.Tenant:
        return tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test_tenant_name"),
            alias=tenant_domain.Alias(root="test-tenant-alias"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test-tenant-alias"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test-tenant-alias"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=False),
            basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

    def test_find_question_answers_by_bot_id(self, setup):
        bot_id = bot_domain.Id(value=1)
        question_answers = [
            question_answer_domain.QuestionAnswer(
                id=question_answer_domain.Id(root=uuid4()),
                question=question_answer_domain.Question(root="question1"),
                answer=question_answer_domain.Answer(root="answer1"),
                updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
                status=question_answer_domain.Status.INDEXED,
            ),
            question_answer_domain.QuestionAnswer(
                id=question_answer_domain.Id(root=uuid4()),
                question=question_answer_domain.Question(root="question2"),
                answer=question_answer_domain.Answer(root="answer2"),
                updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
                status=question_answer_domain.Status.INDEXED,
            ),
        ]
        self.question_usecase.question_answer_repo.find_by_bot_id.return_value = question_answers

        res = self.question_usecase.find_question_answers_by_bot_id(bot_id)

        self.question_usecase.question_answer_repo.find_by_bot_id.assert_called_once_with(
            bot_id=bot_id,
        )
        assert res == question_answers

    def test_find_question_answer_by_id_and_bot_id(self, setup):
        bot_id = bot_domain.Id(value=1)
        id = question_answer_domain.Id(root=uuid4())
        question_answer = question_answer_domain.QuestionAnswer(
            id=id,
            question=question_answer_domain.Question(root="question1"),
            answer=question_answer_domain.Answer(root="answer1"),
            updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
            status=question_answer_domain.Status.INDEXED,
        )
        self.question_usecase.question_answer_repo.find_by_id.return_value = question_answer
        res = self.question_usecase.find_question_answer_by_id_and_bot_id(id, bot_id)
        self.question_usecase.question_answer_repo.find_by_id.assert_called_once_with(
            id=id,
            bot_id=bot_id,
        )
        assert res == question_answer

    def test_create_question_answer_no_duplication(self, monkeypatch, setup):
        mock_datetime = datetime.datetime(2024, 1, 1, 0, 0, 0)
        datetime_mock = MagicMock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mock_datetime
        monkeypatch.setattr(datetime, "datetime", datetime_mock)
        bot_id = bot_domain.Id(value=1)
        dummy_tenant = self.dummy_tenant()
        mock_uuid = uuid4()

        self.question_usecase.question_answer_repo.find_by_bot_id_and_question = Mock(
            side_effect=NotFound("Not Found")
        )

        want = question_answer_domain.QuestionAnswer(
            id=question_answer_domain.Id(root=mock_uuid),
            question=question_answer_domain.Question(root="question1"),
            answer=question_answer_domain.Answer(root="answer1"),
            updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
            status=question_answer_domain.Status.INDEXED,
        )
        self.question_usecase.question_answer_repo.create.return_value = want
        self.question_usecase.cognitive_search_service.add_question_answer_to_tenant_index.return_value = None
        self.question_usecase.llm_service.generate_embeddings.return_value = [0.1, 0.2, 0.3]

        with patch("uuid.uuid4", return_value=mock_uuid):
            question_answer_for_create = question_answer_domain.QuestionAnswerForCreate(
                question=question_answer_domain.Question(root="question1"),
                answer=question_answer_domain.Answer(root="answer1"),
            )
            res = self.question_usecase.create_question_answer(bot_id, dummy_tenant, question_answer_for_create)

        self.question_usecase.llm_service.generate_embeddings.assert_called_once_with(
            text=question_answer_for_create.question.root,
        )

        self.question_usecase.cognitive_search_service.add_question_answer_to_tenant_index.assert_called_once_with(
            endpoint=dummy_tenant.search_service_endpoint,
            index_name=dummy_tenant.index_name,
            index_question_answer=IndexQuestionAnswerForCreate(
                id=str(mock_uuid),
                bot_id=bot_id.value,
                question_answer_id=str(want.id.root),
                content=question_answer_for_create.to_index_document_content(),
                content_vector=[0.1, 0.2, 0.3],
                created_at=mock_datetime.isoformat(),
                updated_at=mock_datetime.isoformat(),
            ),
        )

        self.question_usecase.question_answer_repo.create.assert_called_once_with(
            bot_id=bot_id,
            question_answer=question_answer_for_create,
        )
        self.question_usecase.question_answer_repo.find_by_bot_id_and_question.assert_called_once_with(
            bot_id=bot_id,
            question=question_answer_for_create.question,
        )

        assert res == want

    def test_create_question_answer_exist_duplication(self, setup):
        bot_id = bot_domain.Id(value=1)
        dummy_tenant = self.dummy_tenant()

        duplicated_question_answer = question_answer_domain.QuestionAnswer(
            id=question_answer_domain.Id(root=uuid4()),
            question=question_answer_domain.Question(root="question1"),
            answer=question_answer_domain.Answer(root="answer2"),
            updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
            status=question_answer_domain.Status.INDEXED,
        )
        self.question_usecase.question_answer_repo.find_by_bot_id_and_question = Mock(
            return_value=duplicated_question_answer
        )

        question_answer_for_create = question_answer_domain.QuestionAnswerForCreate(
            question=question_answer_domain.Question(root="question1"),
            answer=question_answer_domain.Answer(root="answer1"),
        )

        with pytest.raises(BadRequest):
            self.question_usecase.create_question_answer(bot_id, dummy_tenant, question_answer_for_create)

    def test_update_question_answer_no_duplication(self, monkeypatch, setup):
        bot_id = bot_domain.Id(value=1)
        dummy_tenant = self.dummy_tenant()

        mock_datetime = datetime.datetime(2024, 1, 1, 0, 0, 0)
        datetime_mock = MagicMock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mock_datetime
        monkeypatch.setattr(datetime, "datetime", datetime_mock)

        self.question_usecase.question_answer_repo.find_by_bot_id_and_question = Mock(
            side_effect=NotFound("Not Found")
        )

        question_answer = question_answer_domain.QuestionAnswer(
            id=question_answer_domain.Id(root=uuid4()),
            question=question_answer_domain.Question(root="質問"),
            answer=question_answer_domain.Answer(root="回答"),
            updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
            status=question_answer_domain.Status.INDEXED,
        )
        self.question_usecase.question_answer_repo.find_by_id.return_value = question_answer
        self.question_usecase.question_answer_repo.update.return_value = None
        self.question_usecase.llm_service.generate_embeddings.return_value = [0.1, 0.2, 0.3]

        self.question_usecase.cognitive_search_service.update_question_answer_in_tenant_index.return_value = None

        self.question_usecase.update_question_answer(bot_id, dummy_tenant, question_answer)

        self.question_usecase.question_answer_repo.find_by_id.assert_called_once_with(
            id=question_answer.id,
            bot_id=bot_id,
        )
        self.question_usecase.llm_service.generate_embeddings.assert_called_once_with(
            text=question_answer.question.root,
        )

        self.question_usecase.cognitive_search_service.update_question_answer_in_tenant_index.assert_called_once_with(
            endpoint=dummy_tenant.search_service_endpoint,
            index_name=dummy_tenant.index_name,
            index_question_answer_for_update=IndexQuestionAnswerForUpdate(
                question_answer_id=str(question_answer.id.root),
                content=question_answer.to_index_document_content(),
                content_vector=[0.1, 0.2, 0.3],
                updated_at=mock_datetime.isoformat(),
            ),
        )

        self.question_usecase.question_answer_repo.find_by_bot_id_and_question.assert_called_once_with(
            bot_id=bot_id,
            question=question_answer.question,
        )
        self.question_usecase.question_answer_repo.update.assert_called_once_with(
            bot_id=bot_id,
            question_answer=question_answer,
        )

    def test_update_question_answer_exist_duplication(self, setup):
        bot_id = bot_domain.Id(value=1)
        dummy_tenant = self.dummy_tenant()

        duplicated_question_answer = question_answer_domain.QuestionAnswer(
            id=question_answer_domain.Id(root=uuid4()),
            question=question_answer_domain.Question(root="質問"),
            answer=question_answer_domain.Answer(root="回答1"),
            updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
            status=question_answer_domain.Status.INDEXED,
        )

        self.question_usecase.question_answer_repo.find_by_bot_id_and_question = Mock(
            return_value=duplicated_question_answer
        )

        question_answer = question_answer_domain.QuestionAnswer(
            id=question_answer_domain.Id(root=uuid4()),
            question=question_answer_domain.Question(root="質問"),
            answer=question_answer_domain.Answer(root="回答2"),
            updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
            status=question_answer_domain.Status.INDEXED,
        )
        self.question_usecase.question_answer_repo.find_by_id.return_value = question_answer

        with pytest.raises(BadRequest):
            self.question_usecase.update_question_answer(bot_id, dummy_tenant, question_answer)

    def test_delete_question_answer(self, setup):
        bot_id = bot_domain.Id(value=1)
        dummy_tenant = self.dummy_tenant()
        question_answer = question_answer_domain.QuestionAnswer(
            id=question_answer_domain.Id(root=uuid4()),
            question=question_answer_domain.Question(root="situmonn"),
            answer=question_answer_domain.Answer(root="answer1"),
            updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
            status=question_answer_domain.Status.INDEXED,
        )

        self.question_usecase.question_answer_repo.delete.return_value = None

        self.question_usecase.delete_question_answer(question_answer.id, dummy_tenant, bot_id)

        self.question_usecase.question_answer_repo.delete.assert_called_once_with(
            id=question_answer.id,
            bot_id=bot_id,
        )

    def test_bulk_create_or_update_question_answer(self, setup):
        mock_uuid = uuid4()
        input = BulkCreateQuestionAnswersInput(
            bot_id=bot_domain.Id(value=1),
            tenant_id=tenant_domain.Id(value=1),
            question_answers=[
                QuestionAnswerForBulkCreateOrUpdate(
                    question=question_answer_domain.Question(root="question3"),
                    answer=question_answer_domain.Answer(root="answer3"),
                ),
                QuestionAnswerForBulkCreateOrUpdate(
                    question=question_answer_domain.Question(root="question4"),
                    answer=question_answer_domain.Answer(root="answer4"),
                ),
            ],
        )

        self.question_usecase.question_answer_repo.find_by_bot_id.return_value = [
            question_answer_domain.QuestionAnswer(
                id=question_answer_domain.Id(root=mock_uuid),
                question=question_answer_domain.Question(root="question4"),
                answer=question_answer_domain.Answer(root="answer4"),
                updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
                status=question_answer_domain.Status.INDEXED,
            )
        ]
        self.question_usecase.queue_storage_service.send_message_to_upload_question_answers_queue.return_value = None

        created_question_answer = question_answer_domain.QuestionAnswer(
            question=question_answer_domain.Question(root="question3"),
            answer=question_answer_domain.Answer(root="answer3"),
            status=question_answer_domain.Status.PENDING,
            id=question_answer_domain.Id(root=mock_uuid),
            updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
        )
        self.question_usecase.question_answer_repo.bulk_create.return_value = [created_question_answer]

        with patch("uuid.uuid4", return_value=mock_uuid):
            self.question_usecase.bulk_create_or_update_question_answers(input)

        self.question_usecase.question_answer_repo.find_by_bot_id.assert_called_once_with(
            bot_id=input.bot_id,
        )

        self.question_usecase.question_answer_repo.bulk_create.assert_called_once_with(
            bot_id=input.bot_id,
            question_answers=[
                question_answer_domain.QuestionAnswerForCreate(
                    question=question_answer_domain.Question(root="question3"),
                    answer=question_answer_domain.Answer(root="answer3"),
                    id=question_answer_domain.Id(root=mock_uuid),
                ),
            ],
        )

        self.question_usecase.question_answer_repo.bulk_update.assert_called_once_with(
            bot_id=input.bot_id,
            question_answers=[
                question_answer_domain.QuestionAnswer(
                    id=question_answer_domain.Id(root=mock_uuid),
                    question=question_answer_domain.Question(root="question4"),
                    answer=question_answer_domain.Answer(root="answer4"),
                    status=question_answer_domain.Status.OVERWRITING,
                    updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
                ),
            ],
        )

        self.question_usecase.queue_storage_service.send_message_to_upload_question_answers_queue.assert_called_once_with(
            tenant_id=input.tenant_id,
            bot_id=input.bot_id,
            question_answer_ids=[
                question_answer_domain.Id(root=mock_uuid),
                created_question_answer.id,
            ],
        )

    def test_bulk_create_or_update_question_answer_with_pending_duplication(self, setup):
        input = BulkCreateQuestionAnswersInput(
            bot_id=bot_domain.Id(value=1),
            tenant_id=tenant_domain.Id(value=1),
            question_answers=[
                QuestionAnswerForBulkCreateOrUpdate(
                    question=question_answer_domain.Question(root="question3"),
                    answer=question_answer_domain.Answer(root="answer3"),
                ),
                QuestionAnswerForBulkCreateOrUpdate(
                    question=question_answer_domain.Question(root="question4"),
                    answer=question_answer_domain.Answer(root="answer4"),
                ),
            ],
        )

        self.question_usecase.question_answer_repo.find_by_bot_id.return_value = [
            question_answer_domain.QuestionAnswer(
                id=question_answer_domain.Id(root=uuid4()),
                question=question_answer_domain.Question(root="question4"),
                answer=question_answer_domain.Answer(root="answer4"),
                updated_at=question_answer_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
                status=question_answer_domain.Status.PENDING,
            )
        ]

        with pytest.raises(BadRequest):
            self.question_usecase.bulk_create_or_update_question_answers(input)
