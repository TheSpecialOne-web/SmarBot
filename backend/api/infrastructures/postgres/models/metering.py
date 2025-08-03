from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    metering as metering_domain,
    tenant as tenant_domain,
)
from api.domain.models.bot import bot as bot_domain
from api.infrastructures.postgres.models.base import BaseModel

if TYPE_CHECKING:
    from .bot import Bot
    from .workflow import Workflow


class Metering(BaseModel):
    __tablename__ = "metering"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False)
    bot_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("bots.id"), nullable=True)
    workflow_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("workflows.id"), nullable=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    bot: Mapped["Bot"] = relationship(
        "Bot",
        back_populates="meterings",
    )
    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        back_populates="meterings",
    )

    @classmethod
    def from_domain(
        cls,
        domain_model: metering_domain.PdfParserMeterForCreate,
        tenant_id: tenant_domain.Id,
    ) -> "Metering":
        return cls(
            tenant_id=tenant_id.value,
            bot_id=domain_model.bot_id.value if domain_model.bot_id is not None else None,
            workflow_id=domain_model.workflow_id.root if domain_model.workflow_id is not None else None,
            type=domain_model.type.value,
            quantity=domain_model.quantity.root,
        )

    def to_domain(self) -> metering_domain.BotPdfParserPageCount:
        if self.bot_id is None:
            raise ValueError("bot_idは必須です。")
        return metering_domain.BotPdfParserPageCount(
            bot_id=bot_domain.Id(value=self.bot_id),
            bot_name=bot_domain.Name(value=self.bot.name),
            page_count=metering_domain.Quantity(root=self.quantity),
            count_type=metering_domain.PDFParserCountType(self.type),
        )
