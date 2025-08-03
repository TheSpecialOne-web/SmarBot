from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import bot as bot_domain
from api.domain.models.bot import approach_variable as approach_variable_domain

from .base import BaseModel


# ApproachVariableモデルの定義
class ApproachVariable(BaseModel):
    __tablename__ = "approach_variables"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)

    bot = relationship("Bot", back_populates="approach_variables")

    @classmethod
    def from_domain(
        cls,
        bot_id: bot_domain.Id,
        approach_variable: approach_variable_domain.ApproachVariable,
    ) -> "ApproachVariable":
        return cls(
            bot_id=bot_id.value,
            name=approach_variable.name.value,
            value=approach_variable.value.value,
        )

    def to_domain(self) -> approach_variable_domain.ApproachVariable:
        name = approach_variable_domain.Name(value=self.name)
        value = approach_variable_domain.Value(value=self.value)
        return approach_variable_domain.ApproachVariable(name=name, value=value)
