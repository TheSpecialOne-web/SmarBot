import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.domain.models import bot as bot_domain
from api.domain.models.bot import prompt_template as prompt_template_domain

from .base import BaseModel


class BotPromptTemplate(BaseModel):
    __tablename__ = "bot_prompt_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    @classmethod
    def from_domain(
        cls,
        domain_model: prompt_template_domain.PromptTemplateForCreate,
        bot_id: bot_domain.Id,
    ) -> "BotPromptTemplate":
        return cls(
            id=domain_model.id.root,
            bot_id=bot_id.value,
            title=domain_model.title.root,
            description=domain_model.description.root if domain_model.description else "",
            prompt=domain_model.prompt.root,
        )

    def to_domain(self) -> prompt_template_domain.PromptTemplate:
        id = prompt_template_domain.Id(root=self.id)
        title = prompt_template_domain.Title(root=self.title)
        description = prompt_template_domain.Description(root=self.description)
        prompt = prompt_template_domain.Prompt(root=self.prompt)
        return prompt_template_domain.PromptTemplate(id=id, title=title, description=description, prompt=prompt)
