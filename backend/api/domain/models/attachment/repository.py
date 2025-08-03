from abc import ABC, abstractmethod
from typing import List

from ..bot import Id as BotId
from ..conversation.conversation_turn import Id as ConversationTurnId
from ..user import Id as UserId
from .attachment import Attachment, AttachmentForCreate
from .id import Id


class IAttachmentRepository(ABC):
    @abstractmethod
    def create(self, bot_id: BotId, user_id: UserId, attachment: AttachmentForCreate) -> Attachment:
        pass

    @abstractmethod
    def find_by_id(self, id: Id) -> Attachment:
        pass

    @abstractmethod
    def delete(self, id: Id) -> None:
        pass

    @abstractmethod
    def update_conversation_turn_ids(self, id: List[Id], conversation_turn_id: ConversationTurnId) -> None:
        pass

    @abstractmethod
    def get_attachments_by_bot_id_after_24_hours(self, bot_id: BotId) -> List[Attachment]:
        pass

    @abstractmethod
    def update_blob_deleted(self, id: Id) -> None:
        pass

    @abstractmethod
    def delete_by_bot_id(self, bot_id: BotId) -> None:
        pass

    @abstractmethod
    def hard_delete_by_bot_ids(self, bot_ids: List[BotId]) -> None:
        pass
