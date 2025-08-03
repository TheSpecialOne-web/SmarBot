from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
)
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.text_2_image_model.model import Text2ImageModelFamily

from .api_key import ApiKey
from .approach_variable import ApproachVariable
from .attachment import Attachment
from .base import BaseModel
from .document import Document
from .document_folder import DocumentFolder
from .metering import Metering
from .tenant import Tenant
from .user_liked_bots import UserLikedBot

if TYPE_CHECKING:
    from .group import Group


# Botモデルの更新
class Bot(BaseModel):
    __tablename__ = "bots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    index_name: Mapped[str] = mapped_column(String(255), nullable=True)
    container_name: Mapped[str] = mapped_column(String(255), nullable=False)
    approach: Mapped[str] = mapped_column(String(255), nullable=False)
    example_questions: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False)
    search_method: Mapped[str] = mapped_column(String(255), nullable=True, default="default")
    query_generator_model: Mapped[str] = mapped_column(String(255), nullable=True, default="gpt-3.5-turbo")
    response_generator_model: Mapped[str] = mapped_column(String(255), nullable=True, default="gpt-3.5-turbo")
    image_generator_model: Mapped[str] = mapped_column(String(511), nullable=True)
    pdf_parser: Mapped[str] = mapped_column(String(255), nullable=True, default="pypdf")
    enable_web_browsing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enable_follow_up_questions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(255), nullable=False, default="active")
    icon_url: Mapped[str] = mapped_column(String(255), nullable=True)
    icon_color: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    response_generator_model_family: Mapped[str] = mapped_column(String(255), nullable=True)
    image_generator_model_family: Mapped[str] = mapped_column(String(255), nullable=True)
    max_conversation_turns: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)

    tenant: Mapped[Tenant] = relationship(
        "Tenant",
        back_populates="bots",
    )

    approach_variables: Mapped[list[ApproachVariable]] = relationship(
        "ApproachVariable",
        back_populates="bot",
    )
    document_folders: Mapped[list[DocumentFolder]] = relationship(
        "DocumentFolder",
        back_populates="bot",
    )
    documents: Mapped[list[Document]] = relationship(
        "Document",
        back_populates="bot",
    )
    attachments: Mapped[list[Attachment]] = relationship(
        "Attachment",
        back_populates="bot",
    )
    conversations = relationship(
        "Conversation",
        back_populates="bot",
    )
    api_keys: Mapped[list[ApiKey]] = relationship(
        "ApiKey",
        back_populates="bot",
    )

    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="bots",
    )

    meterings: Mapped[list["Metering"]] = relationship(
        "Metering",
        back_populates="bot",
    )

    users_liked: Mapped[list["UserLikedBot"]] = relationship(
        "UserLikedBot",
        back_populates="bot",
    )

    __table_args__ = (
        Index(
            "bots_name_tenant_id_idx",
            "name",
            "tenant_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    @classmethod
    def from_domain(
        cls,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        bot: bot_domain.BotForCreate,
    ) -> "Bot":
        return cls(
            tenant_id=tenant_id.value,
            group_id=group_id.value,
            name=bot.name.value,
            description=bot.description.value,
            index_name=bot.index_name.root if bot.index_name else "",
            container_name=bot.container_name.root if bot.container_name else "",
            approach=bot.approach.value,
            example_questions=[example_question.value for example_question in bot.example_questions],
            search_method=bot.search_method.value if bot.search_method else "",
            response_generator_model_family=bot.response_generator_model_family.value,
            image_generator_model_family=(
                bot.image_generator_model_family.value if bot.image_generator_model_family else None
            ),
            pdf_parser=bot.pdf_parser.value if bot.pdf_parser else "",
            enable_web_browsing=bot.enable_web_browsing.root,
            enable_follow_up_questions=bot.enable_follow_up_questions.root,
            status=bot.status.value,
            data_source_id=uuid.uuid4(),
            icon_url=bot.icon_url.root if bot.icon_url else None,
            icon_color=bot.icon_color.root,
            max_conversation_turns=bot.max_conversation_turns.root if bot.max_conversation_turns else None,
        )

    def to_domain(self, approach_variable_dtos: list[ApproachVariable]) -> bot_domain.Bot:
        id = bot_domain.Id(value=self.id)
        name = bot_domain.Name(value=self.name)
        group_id = group_domain.Id(value=self.group_id)
        description = bot_domain.Description(value=self.description)
        created_at = bot_domain.CreatedAt(root=self.created_at)
        index_name = IndexName(root=self.index_name)
        container_name = ContainerName(root=self.container_name)
        approach = bot_domain.Approach(self.approach)
        example_questions = [
            bot_domain.ExampleQuestion(value=example_question) for example_question in self.example_questions
        ]
        search_method = bot_domain.SearchMethod(self.search_method) if self.search_method else None
        response_generator_model_family = ModelFamily(self.response_generator_model_family)
        image_generator_model_family = (
            Text2ImageModelFamily(self.image_generator_model_family) if self.image_generator_model_family else None
        )
        pdf_parser = llm_domain.PdfParser(self.pdf_parser)
        approach_variables = [approach_variable.to_domain() for approach_variable in approach_variable_dtos]
        enable_web_browsing = bot_domain.EnableWebBrowsing(root=self.enable_web_browsing)
        enable_follow_up_questions = bot_domain.EnableFollowUpQuestions(root=self.enable_follow_up_questions)
        status = bot_domain.Status(self.status)
        icon_url = bot_domain.IconUrl(root=self.icon_url) if self.icon_url else None
        icon_color = bot_domain.IconColor(root=self.icon_color)
        endpoint_id = bot_domain.EndpointId(root=self.endpoint_id)
        max_conversation_turns = (
            bot_domain.MaxConversationTurns(root=self.max_conversation_turns) if self.max_conversation_turns else None
        )

        return bot_domain.Bot(
            id=id,
            group_id=group_id,
            name=name,
            description=description,
            created_at=created_at,
            index_name=index_name,
            container_name=container_name,
            approach=approach,
            example_questions=example_questions,
            search_method=search_method,
            response_generator_model_family=response_generator_model_family,
            image_generator_model_family=image_generator_model_family,
            pdf_parser=pdf_parser,
            approach_variables=approach_variables,
            enable_web_browsing=enable_web_browsing,
            enable_follow_up_questions=enable_follow_up_questions,
            status=status,
            icon_url=icon_url,
            icon_color=icon_color,
            endpoint_id=endpoint_id,
            max_conversation_turns=max_conversation_turns,
        )

    def to_domain_with_group_name(self) -> bot_domain.BotWithGroupName:
        bot = self.to_domain(self.approach_variables)
        return bot_domain.BotWithGroupName(
            id=bot.id,
            group_id=bot.group_id,
            group_name=group_domain.Name(value=self.group.name),
            name=bot.name,
            description=bot.description,
            created_at=bot.created_at,
            index_name=bot.index_name,
            container_name=bot.container_name,
            approach=bot.approach,
            example_questions=bot.example_questions,
            approach_variables=bot.approach_variables,
            search_method=bot.search_method,
            response_generator_model_family=bot.response_generator_model_family,
            image_generator_model_family=bot.image_generator_model_family,
            pdf_parser=bot.pdf_parser,
            enable_web_browsing=bot.enable_web_browsing,
            enable_follow_up_questions=bot.enable_follow_up_questions,
            status=bot.status,
            icon_url=bot.icon_url,
            icon_color=bot.icon_color,
            endpoint_id=bot.endpoint_id,
            max_conversation_turns=bot.max_conversation_turns,
        )

    def to_domain_with_tenant(
        self, approach_variable_dtos: list[ApproachVariable], tenant_dto: Tenant
    ) -> bot_domain.BotWithTenant:
        bot = self.to_domain(approach_variable_dtos)
        tenant = tenant_dto.to_domain()
        return bot_domain.BotWithTenant(
            id=bot.id,
            tenant=tenant,
            group_id=bot.group_id,
            name=bot.name,
            description=bot.description,
            created_at=bot.created_at,
            index_name=bot.index_name,
            container_name=bot.container_name,
            approach=bot.approach,
            example_questions=bot.example_questions,
            approach_variables=bot.approach_variables,
            search_method=bot.search_method,
            response_generator_model_family=bot.response_generator_model_family,
            image_generator_model_family=bot.image_generator_model_family,
            pdf_parser=bot.pdf_parser,
            enable_web_browsing=bot.enable_web_browsing,
            enable_follow_up_questions=bot.enable_follow_up_questions,
            status=bot.status,
            icon_url=bot.icon_url,
            icon_color=bot.icon_color,
            endpoint_id=bot.endpoint_id,
            max_conversation_turns=bot.max_conversation_turns,
        )
