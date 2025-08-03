from pydantic import BaseModel

from api.domain.models import tenant as tenant_domain


class DeleteAttachmentsQueue(BaseModel):
    tenant_id: tenant_domain.Id
