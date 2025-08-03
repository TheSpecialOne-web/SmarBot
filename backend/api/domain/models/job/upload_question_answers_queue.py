from pydantic import BaseModel

from api.domain.models import (
    bot as bot_domain,
    question_answer as qa_domain,
    tenant as tenant_domain,
)


class UploadQuestionAnswersQueue(BaseModel):
    tenant_id: tenant_domain.Id
    bot_id: bot_domain.Id
    question_answer_ids: list[qa_domain.Id]
