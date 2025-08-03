from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import (
    job as job_domain,
    tenant as tenant_domain,
)
from api.usecase.job.alert_capacity import AlertCapacityUseCase


def alert_capacity(message_content: dict, dequeue_count: int = 0):
    tenant_id = message_content.get("tenant_id", None)
    datetime = message_content.get("datetime", None)

    if tenant_id is None:
        raise ValueError("tenant_id is required")
    if not datetime:
        raise ValueError("datetime is required")

    msg = job_domain.AlertCapacityQueue(tenant_id=tenant_domain.Id(value=tenant_id), datetime=datetime)

    with SessionFactory() as session:
        injector = get_injector(session)
        alert_capacity_interactor = injector.get(AlertCapacityUseCase)
        alert_capacity_interactor.alert_capacity(tenant_id=msg.tenant_id, datetime=msg.datetime)
