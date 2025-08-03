from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.delete_tenant import DeleteTenantUseCase


def delete_tenant(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.DeleteTenantQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        delete_tenant_interactor = injector.get(DeleteTenantUseCase)
        delete_tenant_interactor.delete_tenant(msg.tenant_id)
