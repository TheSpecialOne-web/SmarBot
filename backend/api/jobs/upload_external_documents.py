from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.upload_external_documents import UploadExternalDocumentsUseCase


def upload_external_documents(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.UploadExternalDocumentsQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        document_interactor = injector.get(UploadExternalDocumentsUseCase)
        document_interactor.upload_external_documents(
            tenant_id=msg.tenant_id,
            bot_id=msg.bot_id,
            document_folder_id=msg.document_folder_id,
            document_ids=msg.document_ids,
        )
