from pydantic import BaseModel

from ..token import TokenCount
from ..user import Id, Name


class UserTokenCount(BaseModel):
    user_id: Id
    user_name: Name
    token_count: TokenCount


class UserTokenCountSummary(BaseModel):
    total_count: TokenCount
    users_tokens: list[UserTokenCount]
