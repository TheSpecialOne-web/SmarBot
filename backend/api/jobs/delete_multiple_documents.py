from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job import DeleteMultipleDocumentsUseCase


def delete_multiple_documents(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.DeleteMultipleDocumentsQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        delete_multiple_documents_interactor = injector.get(DeleteMultipleDocumentsUseCase)
        delete_multiple_documents_interactor.delete_multiple_documents(
            tenant_id=msg.tenant_id, bot_id=msg.bot_id, document_ids=msg.document_ids
        )
