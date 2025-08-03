from pydantic import BaseModel, Field

from .answer import Answer
from .id import Id, create_id
from .question import Question
from .status import Status
from .updated_at import UpdatedAt


class QuestionAnswerProps(BaseModel):
    id: Id
    question: Question
    answer: Answer

    def to_index_document_content(self) -> str:
        return f"質問： {self.question.root} 回答： {self.answer.root}"

    def update_status_to_indexed(self) -> None:
        self.status = Status.INDEXED


class QuestionAnswerForCreate(QuestionAnswerProps):
    id: Id = Field(default_factory=create_id)
    status: Status = Field(default=Status.PENDING)

    def update_status(self, status: Status) -> None:
        self.status = status


class QuestionAnswerForUpdate(QuestionAnswerProps):
    pass


class QuestionAnswer(QuestionAnswerProps):
    status: Status
    updated_at: UpdatedAt

    def update(self, question_answer_for_update: QuestionAnswerForUpdate) -> None:
        self.question = question_answer_for_update.question
        self.answer = question_answer_for_update.answer

    def update_status(self, status: Status) -> None:
        self.status = status
