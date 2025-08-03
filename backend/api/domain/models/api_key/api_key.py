from datetime import datetime

from pydantic import BaseModel, Field

from ..bot import (
    EndpointId,
    bot as bot_domain,
)
from .crypt_api_key import DecryptedApiKey, EncryptedApiKey, create_encrypted_api_key
from .expires_at import ExpiresAt
from .id import Id, create_id
from .name import Name


class ApiKeyProps(BaseModel):
    bot_id: bot_domain.Id
    name: Name
    expires_at: ExpiresAt | None


class ApiKeyForCreate(ApiKeyProps):
    id: Id = Field(default_factory=create_id)
    encrypted_api_key: EncryptedApiKey = Field(default_factory=create_encrypted_api_key)


class ApiKey(ApiKeyProps):
    id: Id
    decrypted_api_key: DecryptedApiKey
    endpoint_id: EndpointId

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        if self.expires_at.root < datetime.now():
            return True
        return False
