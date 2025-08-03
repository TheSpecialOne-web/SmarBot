from pydantic import BaseModel

from ..api_key import Id, Name
from ..token import TokenCount


class ApiKeyTokenCount(BaseModel):
    api_key_id: Id
    name: Name
    token_count: TokenCount


class ApiKeyTokenCountSummary(BaseModel):
    total_count: TokenCount
    api_keys_tokens: list[ApiKeyTokenCount]
