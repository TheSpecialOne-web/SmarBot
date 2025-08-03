from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
)

from .base import BaseModel
from .chat_completion import ChatCompletion

if TYPE_CHECKING:
    from .bot import Bot


class ApiKey(BaseModel):
    __tablename__ = "api_keys"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    bot_id: Mapped[int] = mapped_column(Integer, ForeignKey("bots.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    bot: Mapped["Bot"] = relationship(
        "Bot",
        back_populates="api_keys",
    )

    chat_completions: Mapped[list[ChatCompletion]] = relationship(
        "ChatCompletion",
        back_populates="api_key",
    )

    @classmethod
    def from_domain(cls, api_key: api_key_domain.ApiKeyForCreate) -> "ApiKey":
        return cls(
            id=api_key.id.root,
            bot_id=api_key.bot_id.value,
            name=api_key.name.root,
            encrypted_api_key=api_key.encrypted_api_key.root,
            expires_at=api_key.expires_at.root if api_key.expires_at is not None else None,
        )

    def to_domain(self) -> api_key_domain.ApiKey:
        return api_key_domain.ApiKey(
            id=api_key_domain.Id(root=self.id),
            bot_id=bot_domain.Id(value=self.bot_id),
            name=api_key_domain.Name(root=self.name),
            decrypted_api_key=api_key_domain.EncryptedApiKey(root=self.encrypted_api_key).decrypt(),
            expires_at=(api_key_domain.ExpiresAt(root=self.expires_at) if self.expires_at is not None else None),
            endpoint_id=bot_domain.EndpointId(root=self.bot.endpoint_id),
        )
