from abc import ABC, abstractmethod
from typing import Any, Generator

from pydantic import BaseModel, Field

from api.domain.models.attachment.attachment import (
    AttachmentForConversation as Attachment,
)
from api.domain.models.bot import (
    Approach,
    QuerySystemPrompt,
    ResponseSystemPrompt,
    ResponseSystemPromptHidden,
)
from api.domain.models.chat_completion import Message as ChatCompletionMessage
from api.domain.models.conversation import FollowUpQuestion, ImageUrl, Title
from api.domain.models.conversation.conversation_turn import Turn
from api.domain.models.data_point import DataPoint
from api.domain.models.llm import ModelName
from api.domain.models.query import Queries
from api.domain.models.tenant import (
    MaxAttachmentToken,
    Name as TenantName,
)
from api.domain.models.term import TermsDict
from api.domain.models.term.term import TermV2
from api.domain.models.text_2_image_model.model import Text2ImageModelName


class QueryGeneratorInput(BaseModel):
    model: ModelName
    messages: list[ChatCompletionMessage]
    tenant_name: TenantName
    query_system_prompt: QuerySystemPrompt | None


class QueryGeneratorOutput(BaseModel):
    queries: Queries
    input_token: int
    output_token: int
    additional_kwargs: dict[str, Any] = Field(default={})


class ResponseGeneratorInput(BaseModel):
    model: ModelName
    messages: list[ChatCompletionMessage]
    attachments: list[dict[str, Attachment]]
    max_attachment_token: MaxAttachmentToken
    data_points_from_internal: list[DataPoint]
    data_points_from_web: list[DataPoint]
    data_points_from_question_answer: list[DataPoint]
    data_points_from_url: list[DataPoint]
    tenant_name: str
    response_system_prompt: ResponseSystemPrompt | None
    response_system_prompt_hidden: ResponseSystemPromptHidden | None
    terms_dict: TermsDict
    approach: Approach


class Dalle3ResponseGeneratorInput(ResponseGeneratorInput):
    image_url: ImageUrl


class UrsaResponseGeneratorInput(BaseModel):
    queries: Queries
    additional_kwargs: dict[str, Any]


class ResponseGeneratorOutput(BaseModel):
    response: str
    content_filter: bool = False
    input_token: int
    output_token: int
    data_points: list[DataPoint]


class Dalle3ResponseGeneratorOutput(ResponseGeneratorOutput):
    image_url: ImageUrl


class ResponseGeneratorOutputToken(BaseModel):
    input_token: int
    output_token: int


ResponseGeneratorStreamOutput = str | list[DataPoint] | ResponseGeneratorOutputToken


class UrsaQuestionGeneratorInput(BaseModel):
    messages: list[ChatCompletionMessage]
    queries: Queries
    additional_kwargs: dict[str, Any]


class ILLMService(ABC):
    @abstractmethod
    def generate_embeddings(self, text: str, use_foreign_region: bool = False) -> list[float]:
        pass

    @abstractmethod
    def generate_conversation_title(self, model_name: ModelName, turn_list: list[Turn]) -> Title:
        pass

    @abstractmethod
    def generate_query(self, inputs: QueryGeneratorInput) -> QueryGeneratorOutput:
        pass

    @abstractmethod
    def generate_query_for_dalle3(self, inputs: QueryGeneratorInput) -> QueryGeneratorOutput:
        pass

    @abstractmethod
    def generate_ursa_query(self, inputs: QueryGeneratorInput) -> QueryGeneratorOutput:
        pass

    @abstractmethod
    def generate_image(self, model: Text2ImageModelName, prompt: str) -> ImageUrl:
        pass

    @abstractmethod
    def generate_response_with_internal_data(
        self, inputs: ResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        pass

    @abstractmethod
    def generate_response_without_internal_data(
        self, inputs: ResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        pass

    @abstractmethod
    def generate_response_for_dalle3(
        self, inputs: Dalle3ResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        pass

    @abstractmethod
    def generate_ursa_response(
        self, inputs: UrsaResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        pass

    @abstractmethod
    def generate_questions(self, model_name: ModelName, data_points: list[DataPoint]) -> list[FollowUpQuestion]:
        pass

    @abstractmethod
    def generate_ursa_questions(self, inputs: UrsaQuestionGeneratorInput) -> list[FollowUpQuestion]:
        pass

    @abstractmethod
    def update_query_with_terms(self, queries: Queries, terms: list[TermV2]) -> tuple[Queries, TermsDict]:
        pass
