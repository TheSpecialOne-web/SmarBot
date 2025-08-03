from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job import ConvertAndUploadPdfDocumentUseCase


def convert_and_upload_pdf_document(message_content: dict, dequeue_count: int = 0) -> None:
    msg = job_domain.ConvertAndUploadPdfDocumentQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        convert_and_upload_pdf_document_interactor = injector.get(ConvertAndUploadPdfDocumentUseCase)
        convert_and_upload_pdf_document_interactor.convert_and_upload_pdf_document(
            tenant_id=msg.tenant_id, bot_id=msg.bot_id, document_id=msg.document_id
        )
