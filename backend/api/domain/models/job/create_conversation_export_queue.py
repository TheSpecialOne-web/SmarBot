from pydantic import BaseModel

from api.domain.models import (
    conversation_export as conversation_export_domain,
    tenant as tenant_domain,
)


class CreateConversationExportQueue(BaseModel):
    tenant_id: tenant_domain.Id
    conversation_export_id: conversation_export_domain.Id

    @classmethod
    def from_dict(cls, data: dict) -> "CreateConversationExportQueue":
        try:
            tenant_id = tenant_domain.Id(value=data["tenant_id"])
            conversation_export_id = conversation_export_domain.Id(root=data["conversation_export_id"])
        except KeyError as e:
            raise ValueError(f"Missing required key: {e}")
        return cls(
            tenant_id=tenant_id,
            conversation_export_id=conversation_export_id,
        )
