from pydantic import BaseModel

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    tenant as tenant_domain,
)


class DeleteMultipleDocumentsQueue(BaseModel):
    tenant_id: tenant_domain.Id
    bot_id: bot_domain.Id
    document_ids: list[document_domain.Id]

    @classmethod
    def from_dict(cls, data: dict) -> "DeleteMultipleDocumentsQueue":
        try:
            tenant_id = tenant_domain.Id(value=data["tenant_id"])
            bot_id = bot_domain.Id(value=data["bot_id"])
            document_ids = [document_domain.Id(value=doc_id) for doc_id in data["document_ids"]]
        except KeyError as e:
            raise ValueError(f"Missing required key: {e}")
        return cls(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_ids=document_ids,
        )
