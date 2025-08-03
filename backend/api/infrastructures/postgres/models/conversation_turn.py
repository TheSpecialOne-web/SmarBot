from typing import TYPE_CHECKING
import uuid

from sqlalchemy import ARRAY, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import TEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    conversation as conversation_domain,
    document_folder as document_folder_domain,
    token as token_domain,
)
from api.domain.models.bot import Name as BotName
from api.domain.models.conversation import conversation_turn as conversation_turn_domain
from api.domain.models.group import Name as GroupName
from api.domain.models.llm import ModelName
from api.domain.models.text_2_image_model import Text2ImageModelName
from api.domain.models.user import Name as UserName

from ..attachment import Attachment
from .base import BaseModel

if TYPE_CHECKING:
    from ..document_folder import DocumentFolder
    from .conversation import Conversation
    from .conversation_data_point import ConversationDataPoint


class ConversationTurn(BaseModel):
    __tablename__ = "conversation_turns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    user_input: Mapped[str] = mapped_column(TEXT)
    bot_output: Mapped[str] = mapped_column(TEXT)
    queries: Mapped[list[str]] = mapped_column(ARRAY(String(255)))
    query_input_token: Mapped[int] = mapped_column(Integer)
    query_output_token: Mapped[int] = mapped_column(Integer)
    response_input_token: Mapped[int] = mapped_column(Integer)
    response_output_token: Mapped[int] = mapped_column(Integer)
    token_count: Mapped[float] = mapped_column(Float)
    query_generator_model: Mapped[str] = mapped_column(String(255))
    response_generator_model: Mapped[str] = mapped_column(String(255))
    image_generator_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evaluation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_folder_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_folders.id"), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(TEXT, nullable=True)

    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="conversation_turns",
    )

    conversation_data_points: Mapped[list["ConversationDataPoint"]] = relationship(
        "ConversationDataPoint",
        back_populates="conversation_turn",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    attachments: Mapped[list[Attachment]] = relationship(
        "Attachment",
        back_populates="conversation_turn",
    )

    document_folder: Mapped["DocumentFolder | None"] = relationship(
        "DocumentFolder",
        back_populates="conversation_turns",
    )

    @classmethod
    def from_domain(
        cls,
        domain_model: conversation_turn_domain.ConversationTurnForCreate,
    ) -> "ConversationTurn":
        QUERY_MAX_LENGTH = 511
        queries = [query.shortened(QUERY_MAX_LENGTH) for query in domain_model.queries]
        return cls(
            id=domain_model.id.root,
            conversation_id=domain_model.conversation_id.root,
            user_input=domain_model.user_input.root,
            bot_output=domain_model.bot_output.root,
            queries=[query.root for query in queries],
            query_input_token=domain_model.token_set.query_input_token.root,
            query_output_token=domain_model.token_set.query_output_token.root,
            response_input_token=domain_model.token_set.response_input_token.root,
            response_output_token=domain_model.token_set.response_output_token.root,
            token_count=domain_model.token_count.root,
            query_generator_model=(
                domain_model.query_generator_model.value if domain_model.query_generator_model else None
            ),
            response_generator_model=domain_model.response_generator_model.value,
            image_generator_model=(
                domain_model.image_generator_model.value if domain_model.image_generator_model else None
            ),
            document_folder_id=domain_model.document_folder.id.root if domain_model.document_folder else None,
            evaluation=domain_model.evaluation.value if domain_model.evaluation else None,
        )

    def to_domain(self) -> conversation_turn_domain.ConversationTurn:
        id = conversation_turn_domain.Id(root=self.id)
        conversation_id = conversation_domain.Id(root=self.conversation_id)
        user_input = conversation_turn_domain.UserInput(root=self.user_input)
        bot_output = conversation_turn_domain.BotOutput(root=self.bot_output)
        queries = [conversation_turn_domain.Query(root=query) for query in self.queries]
        token_set = token_domain.TokenSet(
            query_input_token=token_domain.Token(root=self.query_input_token),
            query_output_token=token_domain.Token(root=self.query_output_token),
            response_input_token=token_domain.Token(root=self.response_input_token),
            response_output_token=token_domain.Token(root=self.response_output_token),
        )
        query_generator_model = ModelName(self.query_generator_model) if self.query_generator_model else None
        response_generator_model = ModelName(self.response_generator_model)
        image_generator_model = Text2ImageModelName(self.image_generator_model) if self.image_generator_model else None
        created_at = conversation_turn_domain.CreatedAt(root=self.created_at)
        data_points = [data_point.to_domain() for data_point in self.conversation_data_points]
        evaluation = conversation_turn_domain.Evaluation(self.evaluation) if self.evaluation else None
        comment = conversation_turn_domain.Comment(root=self.comment) if self.comment else None

        return conversation_turn_domain.ConversationTurn(
            id=id,
            conversation_id=conversation_id,
            user_input=user_input,
            bot_output=bot_output,
            queries=queries,
            token_set=token_set,
            token_count=token_domain.TokenCount(root=self.token_count),
            query_generator_model=query_generator_model,
            response_generator_model=response_generator_model,
            image_generator_model=image_generator_model,
            created_at=created_at,
            data_points=data_points,
            evaluation=evaluation,
            comment=comment,
        )

    def to_domain_with_attachments(self) -> conversation_turn_domain.ConversationTurnWithAttachments:
        ct = self.to_domain()
        return conversation_turn_domain.ConversationTurnWithAttachments(
            id=ct.id,
            conversation_id=ct.conversation_id,
            user_input=ct.user_input,
            bot_output=ct.bot_output,
            queries=ct.queries,
            token_set=ct.token_set,
            token_count=ct.token_count,
            query_generator_model=ct.query_generator_model,
            response_generator_model=ct.response_generator_model,
            image_generator_model=ct.image_generator_model,
            created_at=ct.created_at,
            data_points=ct.data_points,
            evaluation=ct.evaluation,
            attachments=[attachment.to_domain() for attachment in self.attachments],
            document_folder=(
                document_folder_domain.DocumentFolder(
                    id=document_folder_domain.Id(root=self.document_folder.id),
                    name=(
                        document_folder_domain.Name(root=self.document_folder.name)
                        if self.document_folder.name is not None
                        else None
                    ),
                    created_at=document_folder_domain.CreatedAt(root=self.document_folder.created_at),
                )
                if self.document_folder
                else None
            ),
            comment=ct.comment,
        )

    def to_domain_with_attachment_and_user_and_bot(self) -> conversation_turn_domain.ConversationTurnWithUserAndBot:
        ct = self.to_domain()
        return conversation_turn_domain.ConversationTurnWithUserAndBot(
            id=ct.id,
            conversation_id=ct.conversation_id,
            user_input=ct.user_input,
            bot_output=ct.bot_output,
            queries=ct.queries,
            token_set=ct.token_set,
            token_count=ct.token_count,
            query_generator_model=ct.query_generator_model,
            response_generator_model=ct.response_generator_model,
            image_generator_model=ct.image_generator_model,
            created_at=ct.created_at,
            data_points=ct.data_points,
            evaluation=ct.evaluation,
            user_name=UserName(value=self.conversation.user.name),
            bot_name=BotName(value=self.conversation.bot.name),
            comment=ct.comment,
        )

    def to_domain_with_user_and_bot_and_group(self):
        ct = self.to_domain_with_attachment_and_user_and_bot()
        return conversation_turn_domain.ConversationTurnWithUserAndBotAndGroup(
            id=ct.id,
            conversation_id=ct.conversation_id,
            user_input=ct.user_input,
            bot_output=ct.bot_output,
            queries=ct.queries,
            token_set=ct.token_set,
            token_count=ct.token_count,
            query_generator_model=ct.query_generator_model,
            response_generator_model=ct.response_generator_model,
            image_generator_model=ct.image_generator_model,
            created_at=ct.created_at,
            data_points=[data_point.to_domain_with_detail() for data_point in self.conversation_data_points],
            evaluation=ct.evaluation,
            user_name=UserName(value=self.conversation.user.name),
            bot_name=BotName(value=self.conversation.bot.name),
            group_names=[GroupName(value=user_group.group.name) for user_group in self.conversation.user.user_groups],
            comment=ct.comment,
            attachments=[
                attachment.to_domain() for attachment in self.attachments if attachment.is_blob_deleted is False
            ],
        )
