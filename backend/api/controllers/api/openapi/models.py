from enum import Enum
from uuid import UUID

from pydantic.json_schema import SkipJsonSchema

from api.controllers.common import CustomBaseModel


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class Message(CustomBaseModel):
    role: MessageRole
    content: str


class CreateChatCompletionRequest(CustomBaseModel):
    messages: list[Message]
    stream: bool


class UpdateChatCompletionFeedbackCommentRequest(CustomBaseModel):
    comment: str


class Evaluation(str, Enum):
    good = "good"
    bad = "bad"


class Feedback(CustomBaseModel):
    evaluation: Evaluation | SkipJsonSchema[None] = None
    comment: str | SkipJsonSchema[None] = None


class DataPointType(str, Enum):
    internal = "internal"
    question_answer = "question_answer"


class DataPoint(CustomBaseModel):
    document_id: int | SkipJsonSchema[None] = None
    question_answer_id: UUID | SkipJsonSchema[None] = None
    cite_number: int
    chunk_name: str
    file_name: str
    content: str
    page_number: int
    type: DataPointType


class CreateChatCompletionResponse(CustomBaseModel):
    id: UUID
    content: str
    data_points: list[DataPoint]
    error: str | SkipJsonSchema[None] = None


class DocumentSignedUrl(CustomBaseModel):
    signed_url_original: str
    signed_url_pdf: str | SkipJsonSchema[None] = None


class QuestionAnswerStatus(str, Enum):
    pending = "pending"
    overwriting = "overwriting"
    indexed = "indexed"
    failed = "failed"


class QuestionAnswer(CustomBaseModel):
    id: UUID
    question: str
    answer: str
    updated_at: str
    status: QuestionAnswerStatus


class UpdateChatCompletionFeedbackEvaluationRequest(CustomBaseModel):
    evaluation: Evaluation


class Assistant(CustomBaseModel):
    id: int
    name: str
    description: str
    icon_url: str | SkipJsonSchema[None] = None
    icon_color: str


class EndpointInfo(CustomBaseModel):
    id: UUID
    assistant: Assistant
