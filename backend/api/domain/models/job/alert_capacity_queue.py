from datetime import datetime

from pydantic import BaseModel

from api.domain.models import tenant as tenant_domain


class AlertCapacityQueue(BaseModel):
    tenant_id: tenant_domain.Id
    datetime: datetime
