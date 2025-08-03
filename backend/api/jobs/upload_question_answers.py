from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import (
    bot as bot_domain,
    job as job_domain,
    question_answer as qa_domain,
    tenant as tenant_domain,
)
from api.usecase.job.upload_question_answers import UploadQuestionAnswersUseCase


def upload_question_answers(message_content: dict, dequeue_count: int = 0):
    tenant_id = message_content.get("tenant_id")
    if not tenant_id:
        raise ValueError("tenant_id is required")
    bot_id = message_content.get("bot_id")
    if not bot_id:
        raise ValueError("bot_id is required")
    question_answer_ids = message_content.get("question_answer_ids")
    if not question_answer_ids or len(question_answer_ids) == 0:
        raise ValueError("question_answer_ids is required")

    msg = job_domain.UploadQuestionAnswersQueue(
        tenant_id=tenant_domain.Id(value=tenant_id),
        bot_id=bot_domain.Id(value=bot_id),
        question_answer_ids=[qa_domain.Id(root=qa_id) for qa_id in question_answer_ids],
    )

    with SessionFactory() as session:
        injector = get_injector(session)
        upload_question_answers_interactor = injector.get(UploadQuestionAnswersUseCase)
        upload_question_answers_interactor.upload_question_answers(
            msg.tenant_id, msg.bot_id, msg.question_answer_ids, dequeue_count
        )
