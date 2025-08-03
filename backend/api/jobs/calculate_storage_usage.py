from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job import CalculateStorageUsageUseCase


def calculate_storage_usage(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.CalculateStorageUsageQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        calculate_storage_usage_interactor = injector.get(CalculateStorageUsageUseCase)
        calculate_storage_usage_interactor.calculate_storage_usage(
            tenant_id=msg.tenant_id, bot_id=msg.bot_id, document_id=msg.document_id
        )
