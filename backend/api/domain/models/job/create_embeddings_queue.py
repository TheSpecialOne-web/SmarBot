from pydantic import BaseModel

from ..bot import Id as BotId
from ..document import Id as DocumentId
from ..tenant import Id as TenantId


class CreateEmbeddingsQueue(BaseModel):
    tenant_id: TenantId
    bot_id: BotId
    document_id: DocumentId

    @classmethod
    def from_dict(cls, data: dict) -> "CreateEmbeddingsQueue":
        try:
            tenant_id = TenantId(value=data["tenant_id"])
            bot_id = BotId(value=data["bot_id"])
            document_id = DocumentId(value=data["document_id"])
        except KeyError as e:
            raise ValueError(f"Missing required key: {e}")
        return cls(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_id=document_id,
        )
