from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.sync_document_name import SyncDocumentNameUseCase


def sync_document_name(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.SyncDocumentNameQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        alert_capacity_interactor = injector.get(SyncDocumentNameUseCase)
        alert_capacity_interactor.sync_document_name(
            tenant_id=msg.tenant_id,
            bot_id=msg.bot_id,
            document_id=msg.document_id,
        )
