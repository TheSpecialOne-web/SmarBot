from pydantic import BaseModel

from api.domain.models import tenant as tenant_domain


class DeleteTenantQueue(BaseModel):
    tenant_id: tenant_domain.Id

    @classmethod
    def from_dict(cls, data: dict) -> "DeleteTenantQueue":
        try:
            tenant_id = tenant_domain.Id(value=data["tenant_id"])
        except KeyError as e:
            raise ValueError(f"Missing required key: {e}")
        return cls(
            tenant_id=tenant_id,
        )
