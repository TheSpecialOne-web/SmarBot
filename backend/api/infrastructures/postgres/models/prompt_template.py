from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from api.domain.models import (
    prompt_template as domain,
    tenant as tenant_domain,
)

from .base import BaseModel


class PromptTemplate(BaseModel):
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    @classmethod
    def from_domain(
        cls,
        domain_model: domain.PromptTemplateForCreate,
        tenant_id: tenant_domain.Id,
    ) -> "PromptTemplate":
        return cls(
            tenant_id=tenant_id.value,
            title=domain_model.title.value,
            description=domain_model.description.value,
            prompt=domain_model.prompt.value,
        )

    def to_domain(self) -> domain.PromptTemplate:
        id = domain.Id(value=self.id)
        title = domain.Title(value=self.title)
        description = domain.Description(value=self.description)
        prompt = domain.Prompt(value=self.prompt)
        return domain.PromptTemplate(id=id, title=title, description=description, prompt=prompt)
