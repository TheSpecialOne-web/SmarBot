from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.document import DocumentUseCase


def sync_document_location(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.SyncDocumentLocationQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        document_interactor = injector.get(DocumentUseCase)
        document_interactor.sync_document_location(
            tenant_id=msg.tenant_id, bot_id=msg.bot_id, document_id=msg.document_id
        )
