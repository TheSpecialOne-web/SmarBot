import uuid

from sqlalchemy import ARRAY, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from api.domain.models import (
    bot as bot_domain,
    term as term_domain,
)

from .base import BaseModel


class TermV2(BaseModel):
    __tablename__ = "terms_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    names: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    @classmethod
    def from_domain(
        cls,
        domain_model: term_domain.TermForCreateV2,
        bot_id: bot_domain.Id,
    ) -> "TermV2":
        return cls(
            id=domain_model.id.root,
            bot_id=bot_id.value,
            names=[name.root for name in domain_model.names],
            description=domain_model.description.root,
        )

    def to_domain(self) -> term_domain.TermV2:
        id = term_domain.IdV2(root=self.id)
        names = self.get_names()
        description = term_domain.DescriptionV2(root=self.description)
        return term_domain.TermV2(
            id=id,
            names=names,
            description=description,
        )

    def get_names(self) -> list[term_domain.NameV2]:
        if self.names is None:
            return []
        names: list[term_domain.NameV2] = []
        for name in self.names:
            names.append(term_domain.NameV2(root=name))
        return names
