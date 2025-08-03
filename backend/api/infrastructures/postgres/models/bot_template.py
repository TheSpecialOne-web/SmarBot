import uuid

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.domain.models import (
    bot_template as bot_template_domain,
    llm as llm_domain,
)
from api.domain.models.llm.model import ModelFamily

from .base import BaseModel


class BotTemplate(BaseModel):
    __tablename__ = "bot_templates"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    approach: Mapped[str] = mapped_column(String(255), nullable=False)
    response_generator_model: Mapped[str] = mapped_column(String(511), nullable=True, default="gpt-3.5-turbo")
    pdf_parser: Mapped[str] = mapped_column(String(255), nullable=True, default="pypdf")
    enable_web_browsing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enable_follow_up_questions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    response_system_prompt: Mapped[str] = mapped_column(Text, nullable=True, default="")
    document_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    icon_url: Mapped[str] = mapped_column(String(255), nullable=True)
    icon_color: Mapped[str] = mapped_column(String(255), nullable=False)
    response_generator_model_family: Mapped[str] = mapped_column(String(255), nullable=True)

    @classmethod
    def from_domain(
        cls,
        domain_model: bot_template_domain.BotTemplateForCreate,
    ) -> "BotTemplate":
        return cls(
            id=domain_model.id.root,
            name=domain_model.name.root,
            description=domain_model.description.root,
            approach=domain_model.approach.value,
            response_generator_model_family=domain_model.response_generator_model_family.value,
            pdf_parser=domain_model.pdf_parser.value,
            enable_web_browsing=domain_model.enable_web_browsing.root,
            enable_follow_up_questions=domain_model.enable_follow_up_questions.root,
            response_system_prompt=domain_model.response_system_prompt.root,
            document_limit=domain_model.document_limit.root,
            is_public=domain_model.is_public.root,
            icon_color=domain_model.icon_color.root,
            icon_url=domain_model.icon_url.root if domain_model.icon_url else None,
        )

    def to_domain(self) -> bot_template_domain.BotTemplate:
        return bot_template_domain.BotTemplate(
            id=bot_template_domain.Id(root=self.id),
            name=bot_template_domain.Name(root=self.name),
            description=bot_template_domain.Description(root=self.description),
            approach=bot_template_domain.Approach(self.approach),
            response_generator_model_family=ModelFamily(self.response_generator_model_family),
            pdf_parser=llm_domain.PdfParser(self.pdf_parser),
            response_system_prompt=bot_template_domain.ResponseSystemPrompt(root=self.response_system_prompt),
            document_limit=bot_template_domain.DocumentLimit(root=self.document_limit),
            enable_web_browsing=bot_template_domain.EnableWebBrowsing(root=self.enable_web_browsing),
            enable_follow_up_questions=bot_template_domain.EnableFollowUpQuestions(
                root=self.enable_follow_up_questions
            ),
            is_public=bot_template_domain.IsPublic(root=self.is_public),
            icon_url=bot_template_domain.IconUrl(root=self.icon_url) if self.icon_url is not None else None,
            icon_color=bot_template_domain.IconColor(root=self.icon_color),
        )
