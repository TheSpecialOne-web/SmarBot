from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    question_answer as qa_domain,
    tenant as tenant_domain,
)
from api.domain.models.job import MAX_DEQUEUE_COUNT
from api.domain.services.cognitive_search import (
    ICognitiveSearchService,
    IndexQuestionAnswerForCreate,
    IndexQuestionAnswerForUpdate,
)
from api.domain.services.llm import ILLMService
from api.domain.services.queue_storage import IQueueStorageService
from api.libs.logging import get_logger


class IUploadQuestionAnswersUseCase(ABC):
    @abstractmethod
    def upload_question_answers(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        question_answer_ids: list[qa_domain.Id],
        dequeue_count: int,
    ):
        pass


class UploadQuestionAnswersUseCase(IUploadQuestionAnswersUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        question_answer_repo: qa_domain.IQuestionAnswerRepository,
        queue_storage_service: IQueueStorageService,
        cognitive_search_service: ICognitiveSearchService,
        llm_service: ILLMService,
    ):
        self.logger = get_logger()
        self.tenant_repo = tenant_repo
        self.question_answer_repo = question_answer_repo
        self.queue_storage_service = queue_storage_service
        self.cognitive_search_service = cognitive_search_service
        self.llm_service = llm_service

    def _generate_embeddings_for_question_answers(
        self, bot_id: bot_domain.Id, question_answers_to_upload: list[qa_domain.QuestionAnswer]
    ) -> tuple[list[IndexQuestionAnswerForCreate], list[IndexQuestionAnswerForUpdate]]:
        index_question_answers_for_create: list[IndexQuestionAnswerForCreate] = []
        index_question_answers_for_update: list[IndexQuestionAnswerForUpdate] = []

        for question_answer_to_upload in question_answers_to_upload:
            try:
                content_vector = self.llm_service.generate_embeddings(
                    text=question_answer_to_upload.question.root,
                )
            except Exception as e:
                self.logger.error(f"Error in generate embedding to question answer: {e}")
                continue

            if question_answer_to_upload.status == qa_domain.Status.PENDING:
                index_question_answers_for_create.append(
                    IndexQuestionAnswerForCreate(
                        bot_id=bot_id.value,
                        question_answer_id=str(question_answer_to_upload.id.root),
                        content=question_answer_to_upload.to_index_document_content(),
                        content_vector=content_vector,
                    )
                )

            if question_answer_to_upload.status == qa_domain.Status.OVERWRITING:
                index_question_answers_for_update.append(
                    IndexQuestionAnswerForUpdate(
                        content=question_answer_to_upload.to_index_document_content(),
                        content_vector=content_vector,
                        question_answer_id=str(question_answer_to_upload.id.root),
                    )
                )
        return index_question_answers_for_create, index_question_answers_for_update

    def _upload_question_answers_to_tenant_index(
        self,
        tenant: tenant_domain.Tenant,
        index_question_answers_for_create: list[IndexQuestionAnswerForCreate],
        index_question_answers_for_update: list[IndexQuestionAnswerForUpdate],
    ) -> list[qa_domain.Id]:
        question_answer_ids_to_update_status: list[qa_domain.Id] = []
        if len(index_question_answers_for_create) > 0:
            successed_question_answer_ids = self.cognitive_search_service.bulk_create_question_answers_to_tenant_index(
                endpoint=tenant.search_service_endpoint,
                index_name=tenant.index_name,
                index_question_answers=index_question_answers_for_create,
            )

            if len(successed_question_answer_ids) > 0:
                question_answer_ids_to_update_status.extend(successed_question_answer_ids)

            self.logger.info(
                f"create_results: {len(successed_question_answer_ids)} succeeded, {len(index_question_answers_for_create) - len(successed_question_answer_ids)} failed"
            )

        if len(index_question_answers_for_update) > 0:
            successed_question_answer_ids = self.cognitive_search_service.bulk_update_question_answers_in_tenant_index(
                endpoint=tenant.search_service_endpoint,
                index_name=tenant.index_name,
                index_question_answers_for_update=index_question_answers_for_update,
            )

            question_answer_ids_to_update_status.extend(successed_question_answer_ids)

            self.logger.info(
                f"update_results: {len(successed_question_answer_ids)} succeeded, {len(index_question_answers_for_update) - len(successed_question_answer_ids)} failed"
            )
        return question_answer_ids_to_update_status

    def _update_unprocessed_question_answers_status_to_failed(
        self, bot_id: bot_domain.Id, question_answer_ids: list[qa_domain.Id]
    ):
        # question_answersの取得 ----------------------------------------
        question_answers_to_upload = self.question_answer_repo.find_by_ids_and_statuses(
            ids=question_answer_ids,
            bot_id=bot_id,
            statuses=[qa_domain.Status.PENDING, qa_domain.Status.OVERWRITING],
        )

        # statusの更新 ----------------------------------------
        self.question_answer_repo.bulk_update_status(
            ids=[question_answer.id for question_answer in question_answers_to_upload],
            bot_id=bot_id,
            status=qa_domain.Status.FAILED,
        )
        self.logger.info(f"updated {len(question_answers_to_upload)} question answers status to FAILED")

    def upload_question_answers(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        question_answer_ids: list[qa_domain.Id],
        dequeue_count: int,
    ):
        try:
            self._upload_question_answers(
                tenant_id=tenant_id,
                bot_id=bot_id,
                question_answer_ids=question_answer_ids,
            )
        except Exception as e:
            if dequeue_count >= MAX_DEQUEUE_COUNT:
                self._update_unprocessed_question_answers_status_to_failed(bot_id, question_answer_ids)
            raise e

    def _upload_question_answers(
        self,
        tenant_id: tenant_domain.Id,
        bot_id: bot_domain.Id,
        question_answer_ids: list[qa_domain.Id],
    ):
        MAX_QUESTION_ANSWERS_TO_PROCESS = 100

        # tenantの取得 ----------------------------------------
        tenant = self.tenant_repo.find_by_id(tenant_id)
        self.logger.info(f"tenant: {tenant.id!s}")

        # question_answersの取得 ----------------------------------------
        question_answers_to_upload = self.question_answer_repo.find_by_ids_and_statuses(
            ids=question_answer_ids[:MAX_QUESTION_ANSWERS_TO_PROCESS],
            bot_id=bot_id,
            statuses=[qa_domain.Status.PENDING, qa_domain.Status.OVERWRITING],
        )

        if len(question_answers_to_upload) == 0:
            self.logger.info("No question answers to upload.")
            return

        self.logger.info(f"remaining question answers : {len(question_answers_to_upload)}")

        # 最初の100件のみを処理する
        (
            index_question_answers_for_create,
            index_question_answers_for_update,
        ) = self._generate_embeddings_for_question_answers(
            bot_id=bot_id, question_answers_to_upload=question_answers_to_upload
        )

        # Cognitive Search にアップロード----------------------------------------
        question_answer_ids_to_update_status = self._upload_question_answers_to_tenant_index(
            tenant=tenant,
            index_question_answers_for_create=index_question_answers_for_create,
            index_question_answers_for_update=index_question_answers_for_update,
        )

        # statusの更新 ----------------------------------------
        if len(question_answer_ids_to_update_status) > 0:
            self.logger.info(f"question_answer_ids_to_update_status: {question_answer_ids_to_update_status}")
            self.question_answer_repo.bulk_update_status(
                ids=question_answer_ids_to_update_status,
                bot_id=bot_id,
                status=qa_domain.Status.INDEXED,
            )
            self.logger.info(f"updated {len(question_answer_ids_to_update_status)} question answers status to INDEXED")

        if (
            len(question_answer_ids_to_update_status) == len(question_answers_to_upload)
            and len(question_answer_ids) <= MAX_QUESTION_ANSWERS_TO_PROCESS
        ):
            self.logger.info("created embeddings for all question answers")
            return

        self.queue_storage_service.send_message_to_upload_question_answers_queue(
            tenant_id=tenant_id,
            bot_id=bot_id,
            question_answer_ids=[
                question_answer_id
                for question_answer_id in question_answer_ids
                if question_answer_id not in question_answer_ids_to_update_status
            ],
        )
