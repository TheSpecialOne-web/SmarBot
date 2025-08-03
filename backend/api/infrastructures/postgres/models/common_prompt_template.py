import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.domain.models import (
    bot_template as bot_template_domain,
    common_prompt_template as cpt_domain,
)

from .base import BaseModel


class CommonPromptTemplate(BaseModel):
    __tablename__ = "common_prompt_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    bot_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bot_templates.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    @classmethod
    def from_domain(
        cls,
        domain_model: cpt_domain.CommonPromptTemplateForCreate,
        bot_template_id: bot_template_domain.Id,
    ) -> "CommonPromptTemplate":
        return cls(
            id=domain_model.id.root,
            bot_template_id=bot_template_id.root,
            title=domain_model.title.root,
            prompt=domain_model.prompt.root,
        )

    def to_domain(self) -> cpt_domain.CommonPromptTemplate:
        id = cpt_domain.Id(root=self.id)
        title = cpt_domain.Title(root=self.title)
        prompt = cpt_domain.Prompt(root=self.prompt)
        return cpt_domain.CommonPromptTemplate(id=id, title=title, prompt=prompt)
