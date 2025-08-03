from pydantic import BaseModel, computed_field

from ..bot import Id as BotId
from ..user import (
    Id as UserId,
    User,
)
from .blob_path import BlobPath
from .create_at import CreateAt
from .end_date_time import EndDateTime
from .id import Id
from .start_date_time import StartDateTime
from .status import Status


class ConversationExportForCreate(BaseModel):
    user_id: UserId
    start_date_time: StartDateTime
    end_date_time: EndDateTime
    target_user_id: UserId | None
    target_bot_id: BotId | None


class ConversationExport(ConversationExportForCreate):
    id: Id
    status: Status

    def update_status_to_active(self):
        self.status = Status.ACTIVE

    @computed_field  # type: ignore[misc]
    @property
    def blob_path(self) -> BlobPath:
        return BlobPath(root=f"conversation_exports/{self.id.root!s}.csv")


class ConversationExportWithUser(BaseModel):
    id: Id
    user: User
    created_at: CreateAt
    status: Status
