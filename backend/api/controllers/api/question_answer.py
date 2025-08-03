from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request
from injector import Injector

from api.dependency_injector import get_injector
from api.domain.models import (
    bot as bot_domain,
    question_answer as qa_domain,
)
from api.libs.ctx import get_bot_from_request
from api.libs.exceptions import BadRequest
from api.usecase.question_answer import IQuestionAnswerUseCase, QuestionAnswerUseCase

from .openapi import models


def get_question_answer_interactor(
    injector: Injector = Depends(get_injector),  # noqa: B008
) -> IQuestionAnswerUseCase:
    return injector.get(QuestionAnswerUseCase)


question_answer_router = APIRouter()


@question_answer_router.get(
    "/endpoints/{endpoint_id}/question-answers/{question_answer_id}",
    dependencies=[],
    response_model=models.QuestionAnswer,
)
def get_question_answer(
    request: Request,
    question_answer_interactor: IQuestionAnswerUseCase = Depends(get_question_answer_interactor),  # noqa: B008
    endpoint_id: UUID = Path(...),  # noqa: B008
    question_answer_id: UUID = Path(...),  # noqa: B008
):
    bot = get_bot_from_request(request)
    endpoint_id_param = bot_domain.EndpointId(root=endpoint_id)
    if bot.endpoint_id != endpoint_id_param:
        raise BadRequest("endpoint_id is invalid")

    question_answer_id_param = qa_domain.Id(root=question_answer_id)

    question_answer = question_answer_interactor.find_question_answer_by_id_and_bot_id(
        bot_id=bot.id,
        id=question_answer_id_param,
    )

    return models.QuestionAnswer(
        id=question_answer.id.root,
        question=question_answer.question.root,
        answer=question_answer.answer.root,
        updated_at=question_answer.updated_at.formatted(),
        status=models.QuestionAnswerStatus(question_answer.status.value),
    )
