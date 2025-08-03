from pydantic import BaseModel, computed_field

from ..api_key import Id as ApiKeyId
from ..bot import Id as BotId
from ..user import (
    Id as UserId,
    User,
)
from .blob_path import BlobPath
from .created_at import CreatedAt
from .end_date_time import EndDateTime
from .id import Id
from .start_date_time import StartDateTime
from .status import Status


class ChatCompletionExportForCreate(BaseModel):
    creator_id: UserId
    start_date_time: StartDateTime
    end_date_time: EndDateTime
    target_api_key_id: ApiKeyId | None
    target_bot_id: BotId | None


class ChatCompletionExport(ChatCompletionExportForCreate):
    id: Id
    status: Status

    def update_status_to_active(self):
        self.status = Status.ACTIVE

    @computed_field  # type: ignore[misc]
    @property
    def blob_path(self) -> BlobPath:
        return BlobPath(root=f"chat_completion_exports/{self.id.root!s}.csv")


class ChatCompletionExportWithUser(BaseModel):
    id: Id
    creator: User
    created_at: CreatedAt
    status: Status
