from pydantic import BaseModel

from api.domain.models import (
    chat_completion_export as chat_completion_export_domain,
    tenant as tenant_domain,
)


class CreateChatCompletionExportQueue(BaseModel):
    tenant_id: tenant_domain.Id
    chat_completion_export_id: chat_completion_export_domain.Id

    @classmethod
    def from_dict(cls, data: dict) -> "CreateChatCompletionExportQueue":
        try:
            tenant_id = tenant_domain.Id(value=data["tenant_id"])
            chat_completion_export_id = chat_completion_export_domain.Id(root=data["chat_completion_export_id"])
        except KeyError as e:
            raise ValueError(f"Missing required key: {e}")
        return cls(
            tenant_id=tenant_id,
            chat_completion_export_id=chat_completion_export_id,
        )
