import datetime
from unittest.mock import MagicMock, Mock, call, patch
from uuid import uuid4

import pytest

from api.domain.models import (
    bot as bot_domain,
    llm as llm_domain,
    question_answer as qa_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.infrastructures.cognitive_search.cognitive_search import (
    IndexQuestionAnswerForCreate,
    IndexQuestionAnswerForUpdate,
)
from api.usecase.job.upload_question_answers import UploadQuestionAnswersUseCase


class TestUploadQuestionAnswersUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = Mock()
        self.bot_repo_mock = Mock()
        self.question_repo_mock = Mock()
        self.answer_repo_mock = Mock()
        self.queue_storage_service_mock = Mock()
        self.cognitive_search_service_mock = Mock()
        self.llm_service_mock = Mock()
        self.upload_question_answers_case = UploadQuestionAnswersUseCase(
            tenant_repo=self.tenant_repo_mock,
            question_answer_repo=self.question_repo_mock,
            queue_storage_service=self.queue_storage_service_mock,
            cognitive_search_service=self.cognitive_search_service_mock,
            llm_service=self.llm_service_mock,
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

    def test_upload_question_answers_with_success(self, monkeypatch, setup):
        dummy_tenant = self.dummy_tenant()
        mock_uuid_1 = uuid4()
        mock_uuid_2 = uuid4()

        mock_datetime = datetime.datetime(2024, 1, 1, 0, 0, 0)
        datetime_mock = MagicMock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mock_datetime
        monkeypatch.setattr(datetime, "datetime", datetime_mock)

        self.tenant_repo_mock.find_by_id.return_value = dummy_tenant
        pending_question_answer = qa_domain.QuestionAnswer(
            id=qa_domain.Id(root=mock_uuid_1),
            question=qa_domain.Question(root="question1"),
            answer=qa_domain.Answer(root="answer1"),
            status=qa_domain.Status.PENDING,
            updated_at=qa_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
        )
        overwriting_question_answer = qa_domain.QuestionAnswer(
            id=qa_domain.Id(root=mock_uuid_2),
            question=qa_domain.Question(root="question2"),
            answer=qa_domain.Answer(root="answer2"),
            status=qa_domain.Status.OVERWRITING,
            updated_at=qa_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
        )

        self.upload_question_answers_case.question_answer_repo.find_by_ids_and_statuses.return_value = [
            pending_question_answer,
            overwriting_question_answer,
        ]
        self.upload_question_answers_case.llm_service.generate_embeddings.return_value = [0.1, 0.2, 0.3]
        self.upload_question_answers_case.cognitive_search_service.bulk_create_question_answers_to_tenant_index.return_value = [
            qa_domain.Id(root=mock_uuid_1)
        ]
        self.upload_question_answers_case.cognitive_search_service.bulk_update_question_answers_in_tenant_index.return_value = [
            qa_domain.Id(root=mock_uuid_2)
        ]
        self.upload_question_answers_case.question_answer_repo.bulk_update_status.return_value = None

        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        question_answer_ids = [qa_domain.Id(root=mock_uuid_1), qa_domain.Id(root=mock_uuid_2)]
        with patch("uuid.uuid4", return_value=mock_uuid_1):
            self.upload_question_answers_case.upload_question_answers(
                tenant_id=tenant_id, bot_id=bot_id, question_answer_ids=question_answer_ids, dequeue_count=0
            )

        # Assertion
        self.tenant_repo_mock.find_by_id.assert_called_once_with(tenant_id)
        self.upload_question_answers_case.question_answer_repo.find_by_ids_and_statuses.assert_called_once_with(
            ids=question_answer_ids,
            bot_id=bot_id,
            statuses=[qa_domain.Status.PENDING, qa_domain.Status.OVERWRITING],
        )

        self.upload_question_answers_case.llm_service.generate_embeddings.assert_has_calls(
            [
                call(text=pending_question_answer.question.root),
                call(text=overwriting_question_answer.question.root),
            ]
        )
        self.upload_question_answers_case.cognitive_search_service.bulk_create_question_answers_to_tenant_index.assert_called_once_with(
            endpoint=dummy_tenant.search_service_endpoint,
            index_name=dummy_tenant.index_name,
            index_question_answers=[
                IndexQuestionAnswerForCreate(
                    id=str(mock_uuid_1),
                    bot_id=bot_id.value,
                    question_answer_id=str(mock_uuid_1),
                    content=pending_question_answer.to_index_document_content(),
                    created_at=str(mock_datetime.isoformat()),
                    updated_at=str(mock_datetime.isoformat()),
                    content_vector=[0.1, 0.2, 0.3],
                )
            ],
        )
        self.upload_question_answers_case.cognitive_search_service.bulk_update_question_answers_in_tenant_index.assert_called_once_with(
            endpoint=dummy_tenant.search_service_endpoint,
            index_name=dummy_tenant.index_name,
            index_question_answers_for_update=[
                IndexQuestionAnswerForUpdate(
                    content=overwriting_question_answer.to_index_document_content(),
                    content_vector=[0.1, 0.2, 0.3],
                    updated_at=str(mock_datetime.isoformat()),
                    question_answer_id=str(mock_uuid_2),
                )
            ],
        )

        self.upload_question_answers_case.question_answer_repo.bulk_update_status.assert_called_once_with(
            ids=[pending_question_answer.id, overwriting_question_answer.id],
            bot_id=bot_id,
            status=qa_domain.Status.INDEXED,
        )

    def test_upload_question_answers_with_failure(self, monkeypatch, setup):
        dummy_tenant = self.dummy_tenant()
        mock_uuid_1 = uuid4()
        mock_uuid_2 = uuid4()

        mock_datetime = datetime.datetime(2024, 1, 1, 0, 0, 0)
        datetime_mock = MagicMock(wraps=datetime.datetime)
        datetime_mock.now.return_value = mock_datetime
        monkeypatch.setattr(datetime, "datetime", datetime_mock)

        self.tenant_repo_mock.find_by_id.return_value = dummy_tenant
        pending_question_answer = qa_domain.QuestionAnswer(
            id=qa_domain.Id(root=mock_uuid_1),
            question=qa_domain.Question(root="question1"),
            answer=qa_domain.Answer(root="answer1"),
            status=qa_domain.Status.PENDING,
            updated_at=qa_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
        )
        overwriting_question_answer = qa_domain.QuestionAnswer(
            id=qa_domain.Id(root=mock_uuid_2),
            question=qa_domain.Question(root="question2"),
            answer=qa_domain.Answer(root="answer2"),
            status=qa_domain.Status.OVERWRITING,
            updated_at=qa_domain.UpdatedAt(root=datetime.datetime(2024, 1, 1, 0, 0, 0)),
        )

        self.upload_question_answers_case.question_answer_repo.find_by_ids_and_statuses.return_value = [
            pending_question_answer,
            overwriting_question_answer,
        ]
        self.upload_question_answers_case.llm_service.generate_embeddings.return_value = [0.1, 0.2, 0.3]
        self.upload_question_answers_case.cognitive_search_service.bulk_create_question_answers_to_tenant_index.return_value = [
            qa_domain.Id(root=mock_uuid_1)
        ]
        self.upload_question_answers_case.cognitive_search_service.bulk_update_question_answers_in_tenant_index.return_value = []
        self.upload_question_answers_case.question_answer_repo.bulk_update_status.return_value = None

        self.upload_question_answers_case.queue_storage_service.send_message_to_upload_question_answers_queue.return_value = None

        tenant_id = tenant_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)
        question_answer_ids = [qa_domain.Id(root=mock_uuid_1), qa_domain.Id(root=mock_uuid_2)]
        with patch("uuid.uuid4", return_value=mock_uuid_1):
            self.upload_question_answers_case.upload_question_answers(
                tenant_id=tenant_id, bot_id=bot_id, question_answer_ids=question_answer_ids, dequeue_count=0
            )

        # Assertion
        self.tenant_repo_mock.find_by_id.assert_called_once_with(tenant_id)
        self.upload_question_answers_case.question_answer_repo.find_by_ids_and_statuses.assert_called_once_with(
            ids=question_answer_ids,
            bot_id=bot_id,
            statuses=[qa_domain.Status.PENDING, qa_domain.Status.OVERWRITING],
        )
        self.upload_question_answers_case.llm_service.generate_embeddings.assert_has_calls(
            [
                call(text=pending_question_answer.question.root),
                call(text=overwriting_question_answer.question.root),
            ]
        )
        self.upload_question_answers_case.cognitive_search_service.bulk_create_question_answers_to_tenant_index.assert_called_once_with(
            endpoint=dummy_tenant.search_service_endpoint,
            index_name=dummy_tenant.index_name,
            index_question_answers=[
                IndexQuestionAnswerForCreate(
                    id=str(mock_uuid_1),
                    bot_id=bot_id.value,
                    question_answer_id=str(mock_uuid_1),
                    content=pending_question_answer.to_index_document_content(),
                    created_at=str(mock_datetime.isoformat()),
                    updated_at=str(mock_datetime.isoformat()),
                    content_vector=[0.1, 0.2, 0.3],
                )
            ],
        )
        self.upload_question_answers_case.cognitive_search_service.bulk_update_question_answers_in_tenant_index.assert_called_once_with(
            endpoint=dummy_tenant.search_service_endpoint,
            index_name=dummy_tenant.index_name,
            index_question_answers_for_update=[
                IndexQuestionAnswerForUpdate(
                    content=overwriting_question_answer.to_index_document_content(),
                    content_vector=[0.1, 0.2, 0.3],
                    updated_at=str(mock_datetime.isoformat()),
                    question_answer_id=str(mock_uuid_2),
                )
            ],
        )

        self.upload_question_answers_case.question_answer_repo.bulk_update_status.assert_called_once_with(
            ids=[pending_question_answer.id],
            bot_id=bot_id,
            status=qa_domain.Status.INDEXED,
        )
        self.upload_question_answers_case.queue_storage_service.send_message_to_upload_question_answers_queue.assert_called_once_with(
            tenant_id=tenant_id,
            bot_id=bot_id,
            question_answer_ids=[qa_domain.Id(root=mock_uuid_2)],
        )
