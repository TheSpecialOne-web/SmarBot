from abc import ABC, abstractmethod

from injector import inject
from pydantic import BaseModel

from api.domain.models import (
    bot as bot_domain,
    question_answer as question_answer_domain,
    tenant as tenant_domain,
)
from api.domain.services import (
    cognitive_search as cognitive_search_domain,
    llm as llm_domain,
)
from api.domain.services.cognitive_search import (
    IndexQuestionAnswerForCreate,
    IndexQuestionAnswerForUpdate,
)
from api.domain.services.queue_storage import IQueueStorageService
from api.libs.exceptions import BadRequest, NotFound


class QuestionAnswerForBulkCreateOrUpdate(BaseModel):
    question: question_answer_domain.Question
    answer: question_answer_domain.Answer


class BulkCreateQuestionAnswersInput(BaseModel):
    bot_id: bot_domain.Id
    tenant_id: tenant_domain.Id
    question_answers: list[QuestionAnswerForBulkCreateOrUpdate]


class IQuestionAnswerUseCase(ABC):
    @abstractmethod
    def find_question_answers_by_bot_id(self, bot_id: bot_domain.Id) -> list[question_answer_domain.QuestionAnswer]:
        pass

    @abstractmethod
    def find_question_answer_by_id_and_bot_id(
        self,
        id: question_answer_domain.Id,
        bot_id: bot_domain.Id,
    ) -> question_answer_domain.QuestionAnswer:
        pass

    @abstractmethod
    def create_question_answer(
        self,
        bot_id: bot_domain.Id,
        tenant: tenant_domain.Tenant,
        question_answer: question_answer_domain.QuestionAnswerForCreate,
    ) -> question_answer_domain.QuestionAnswer:
        pass

    @abstractmethod
    def update_question_answer(
        self,
        bot_id: bot_domain.Id,
        tenant: tenant_domain.Tenant,
        question_answer: question_answer_domain.QuestionAnswerForUpdate,
    ) -> None:
        pass

    @abstractmethod
    def delete_question_answer(
        self,
        id: question_answer_domain.Id,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
    ) -> None:
        pass

    @abstractmethod
    def bulk_create_or_update_question_answers(self, input_data: BulkCreateQuestionAnswersInput) -> None:
        pass


class QuestionAnswerUseCase(IQuestionAnswerUseCase):
    @inject
    def __init__(
        self,
        question_answer_repo: question_answer_domain.IQuestionAnswerRepository,
        llm_service: llm_domain.ILLMService,
        cognitive_search_service: cognitive_search_domain.ICognitiveSearchService,
        queue_storage_service: IQueueStorageService,
    ) -> None:
        self.question_answer_repo = question_answer_repo
        self.llm_service = llm_service
        self.cognitive_search_service = cognitive_search_service
        self.queue_storage_service = queue_storage_service

    def find_question_answers_by_bot_id(
        self,
        bot_id: bot_domain.Id,
    ) -> list[question_answer_domain.QuestionAnswer]:
        return self.question_answer_repo.find_by_bot_id(bot_id=bot_id)

    def find_question_answer_by_id_and_bot_id(
        self, id: question_answer_domain.Id, bot_id: bot_domain.Id
    ) -> question_answer_domain.QuestionAnswer:
        return self.question_answer_repo.find_by_id(id=id, bot_id=bot_id)

    def create_question_answer(
        self,
        bot_id: bot_domain.Id,
        tenant: tenant_domain.Tenant,
        question_answer: question_answer_domain.QuestionAnswerForCreate,
    ) -> question_answer_domain.QuestionAnswer:
        content = question_answer.to_index_document_content()
        content_vector = self.llm_service.generate_embeddings(text=question_answer.question.root)

        # 質問が重複した場合にはエラーを投げる
        try:
            existing_question_answer = self.question_answer_repo.find_by_bot_id_and_question(
                bot_id=bot_id, question=question_answer.question
            )
            if existing_question_answer:
                raise BadRequest("質問が重複しています。")
        except NotFound:
            pass

        index_question_answer = IndexQuestionAnswerForCreate(
            bot_id=bot_id.value,
            content=content,
            question_answer_id=str(question_answer.id.root),
            content_vector=content_vector,
        )

        self.cognitive_search_service.add_question_answer_to_tenant_index(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            index_question_answer=index_question_answer,
        )

        question_answer.update_status(status=question_answer_domain.Status.INDEXED)
        return self.question_answer_repo.create(bot_id=bot_id, question_answer=question_answer)

    def update_question_answer(
        self,
        bot_id: bot_domain.Id,
        tenant: tenant_domain.Tenant,
        question_answer: question_answer_domain.QuestionAnswerForUpdate,
    ) -> None:
        current = self.question_answer_repo.find_by_id(id=question_answer.id, bot_id=bot_id)
        if current.status in [question_answer_domain.Status.PENDING, question_answer_domain.Status.OVERWRITING]:
            raise BadRequest("処理中のFAQは更新できません。")

        current.update(question_answer)

        # 質問が重複した場合にはエラーを投げる
        try:
            existing_question_answer = self.question_answer_repo.find_by_bot_id_and_question(
                bot_id=bot_id, question=question_answer.question
            )
            if existing_question_answer and existing_question_answer.id != question_answer.id:
                raise BadRequest("質問が重複しています。")
        except NotFound:
            pass

        content_vector = self.llm_service.generate_embeddings(text=question_answer.question.root)
        index_question_answer_for_update = IndexQuestionAnswerForUpdate(
            question_answer_id=str(question_answer.id.root),
            content=question_answer.to_index_document_content(),
            content_vector=content_vector,
        )
        self.cognitive_search_service.update_question_answer_in_tenant_index(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
            index_question_answer_for_update=index_question_answer_for_update,
        )
        self.question_answer_repo.update(bot_id=bot_id, question_answer=current)

    def delete_question_answer(
        self,
        id: question_answer_domain.Id,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
    ) -> None:
        question_answer = self.question_answer_repo.find_by_id(id=id, bot_id=bot_id)
        if question_answer.status in [
            question_answer_domain.Status.PENDING,
            question_answer_domain.Status.OVERWRITING,
        ]:
            raise BadRequest("処理中のFAQは削除できません。")

        self.question_answer_repo.delete(id=id, bot_id=bot_id)
        self.cognitive_search_service.delete_question_answer_from_tenant_index(
            endpoint=tenant.search_service_endpoint, index_name=tenant.index_name, question_answer_id=id
        )

    def _categorize_question_answers(
        self,
        bot_id: bot_domain.Id,
        input_question_answers: list[QuestionAnswerForBulkCreateOrUpdate],
    ) -> tuple[list[question_answer_domain.QuestionAnswerForCreate], list[question_answer_domain.QuestionAnswer]]:
        question_answers_for_create: list[question_answer_domain.QuestionAnswerForCreate] = []
        question_answers_for_update: list[question_answer_domain.QuestionAnswer] = []

        existing_question_answers = self.question_answer_repo.find_by_bot_id(bot_id=bot_id)
        for input_question_answer in input_question_answers:
            existing_question_answer = next(
                (ea for ea in existing_question_answers if ea.question == input_question_answer.question), None
            )
            if existing_question_answer:
                if existing_question_answer.status in [
                    question_answer_domain.Status.PENDING,
                    question_answer_domain.Status.OVERWRITING,
                ]:
                    raise BadRequest("処理中のFAQを更新することはできません。")

                existing_question_answer.update(
                    question_answer_domain.QuestionAnswerForUpdate(
                        id=existing_question_answer.id,
                        question=input_question_answer.question,
                        answer=input_question_answer.answer,
                    )
                )
                existing_question_answer.update_status(status=question_answer_domain.Status.OVERWRITING)
                question_answers_for_update.append(existing_question_answer)
            else:
                question_answers_for_create.append(
                    question_answer_domain.QuestionAnswerForCreate(
                        question=input_question_answer.question,
                        answer=input_question_answer.answer,
                    )
                )

        return question_answers_for_create, question_answers_for_update

    def bulk_create_or_update_question_answers(self, input: BulkCreateQuestionAnswersInput) -> None:
        # FAQを新規作成するか、既存のFAQを更新するかを判定
        question_answers_for_create, question_answers_for_update = self._categorize_question_answers(
            bot_id=input.bot_id,
            input_question_answers=input.question_answers,
        )

        self.question_answer_repo.bulk_create(bot_id=input.bot_id, question_answers=question_answers_for_create)
        self.question_answer_repo.bulk_update(bot_id=input.bot_id, question_answers=question_answers_for_update)

        question_answer_ids_to_upload: list[question_answer_domain.Id] = [qa.id for qa in question_answers_for_update]
        question_answer_ids_to_upload.extend([qa.id for qa in question_answers_for_create])
        self.queue_storage_service.send_message_to_upload_question_answers_queue(
            tenant_id=input.tenant_id,
            bot_id=input.bot_id,
            question_answer_ids=question_answer_ids_to_upload,
        )
