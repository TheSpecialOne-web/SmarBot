from typing import Generator, Literal, Optional

from pydantic import BaseModel, RootModel, StrictInt, model_validator

from api.domain.models import (
    bot as bot_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.attachment import Id as AttachmentId
from api.domain.models.conversation import (
    Event,
    Id,
    ImageUrl,
    Title,
    conversation_turn as ct_domain,
)
from api.domain.models.conversation.use_web_browsing import UseWebBrowsing
from api.domain.models.data_point import DataPoint
from api.domain.models.document_folder import Id as DocumentFolderId
from api.domain.models.llm.model import ModelFamily
from api.domain.models.tenant import Id as TenantId
from api.domain.models.user import Id as UserId


class Offset(RootModel):
    root: StrictInt

    @model_validator(mode="after")
    def check_value(self) -> "Offset":
        if self.root < 0:
            raise ValueError("offset は 0以上である必要があります。")
        if self.root is None:
            raise ValueError("offset は必須項目です。")
        return self


class Limit(RootModel):
    root: StrictInt

    @model_validator(mode="after")
    def check_value(self) -> "Limit":
        if self.root < 1:
            raise ValueError("limit は 1以上である必要があります。")
        if self.root is None:
            raise ValueError("limit は必須項目です。")
        return self


class GetConversationsByUserIdInput(BaseModel):
    tenant_id: TenantId
    user_id: UserId
    offset: Offset
    limit: Limit


class ConversationAttachment(BaseModel):
    from_: Literal["bot", "user"]
    attachment_id: AttachmentId


class CreateConversationInput(BaseModel):
    tenant: tenant_domain.Tenant
    bot_id: bot_domain.Id
    user_id: user_domain.Id
    conversation_id: Optional[Id]
    question: ct_domain.UserInput
    attachments: list[ConversationAttachment]
    use_web_browsing: UseWebBrowsing
    document_folder_id: Optional[DocumentFolderId] = None


class CreateConversationOutput(BaseModel):
    conversation_id: Id
    conversation_turn_id: ct_domain.Id
    data_points: list[DataPoint]
    answer: str
    query: list[str]
    follow_up_questions: list[str]
    image_url: ImageUrl


class ConversationOutputDataPoints(BaseModel):
    data_points: list[DataPoint]


class ConversationOutputAnswer(BaseModel):
    answer: str


class ConversationOutputToken(BaseModel):
    query_input_token: int
    query_output_token: int
    response_input_token: int
    response_output_token: int


class ConversationOutputQuery(BaseModel):
    query: list[str]


class ConversationOutputImageUrl(BaseModel):
    image_url: ImageUrl


class ConversationOutputFollowUpQuestions(BaseModel):
    follow_up_questions: list[str]


class ConversationOutputEvent(BaseModel):
    event: Event


CreateConversationOutputStream = Generator[
    Id
    | ct_domain.Id
    | ConversationOutputDataPoints
    | ConversationOutputAnswer
    | ConversationOutputToken
    | ConversationOutputQuery
    | ConversationOutputImageUrl
    | ConversationOutputFollowUpQuestions
    | ConversationOutputEvent,
    None,
    None,
]


class PreviewConversationInput(BaseModel):
    tenant: tenant_domain.Tenant
    history: list[ct_domain.Turn]
    approach: bot_domain.Approach
    response_generator_model_family: ModelFamily
    response_system_prompt: Optional[bot_domain.ResponseSystemPrompt] = None

    @model_validator(mode="after")
    def check_approach(self) -> "PreviewConversationInput":
        if self.approach != bot_domain.Approach.CUSTOM_GPT:
            raise ValueError("approach は custom_gpt である必要があります。")
        return self


PreviewConversationOutput = Generator[ConversationOutputDataPoints | ConversationOutputAnswer, None, None]


class UpdateConversationInput(BaseModel):
    conversation_id: Id
    user_id: user_domain.Id
    title: Optional[Title]
    is_archived: Optional[bool]


class UpdateConversationEvaluationInput(BaseModel):
    conversation_id: Id
    conversation_turn_id: ct_domain.Id
    evaluation: ct_domain.Evaluation


class CreateOrUpdateConversationTurnFeedbackCommentInput(BaseModel):
    conversation_id: Id
    conversation_turn_id: ct_domain.Id
    comment: ct_domain.Comment
