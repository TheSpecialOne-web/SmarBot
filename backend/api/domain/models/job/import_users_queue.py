from pydantic import BaseModel

from api.domain.models import (
    storage as storage_domain,
    tenant as tenant_domain,
)


class UsersImportQueue(BaseModel):
    tenant_id: tenant_domain.Id
    filename: storage_domain.BlobName

    @classmethod
    def from_dict(cls, data: dict) -> "UsersImportQueue":
        try:
            tenant_id = tenant_domain.Id(value=data["tenant_id"])
            filename = storage_domain.BlobName(root=data["filename"])
        except KeyError as e:
            raise ValueError(f"Missing required key: {e}")
        return cls(
            tenant_id=tenant_id,
            filename=filename,
        )
