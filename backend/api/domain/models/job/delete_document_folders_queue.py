from pydantic import BaseModel

from api.domain.models import (
    bot as bot_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
)


class DeleteDocumentFoldersQueue(BaseModel):
    tenant_id: tenant_domain.Id
    bot_id: bot_domain.Id
    document_folder_ids: list[document_folder_domain.Id]

    @classmethod
    def from_dict(cls, data: dict):
        try:
            tenant_id = tenant_domain.Id(value=data["tenant_id"])
            bot_id = bot_domain.Id(value=data["bot_id"])
            document_folder_ids = [
                document_folder_domain.Id(root=document_folder_id)
                for document_folder_id in data["document_folder_ids"]
            ]
        except KeyError as e:
            raise ValueError(f"Missing required key: {e}")
        return cls(
            tenant_id=tenant_id,
            bot_id=bot_id,
            document_folder_ids=document_folder_ids,
        )
