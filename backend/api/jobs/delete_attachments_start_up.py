from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.usecase.job.delete_attachments import DeleteAttachmentUseCase


def delete_attachments_start_up():
    with SessionFactory() as session:
        injector = get_injector(session)
        delete_attachment_interactor = injector.get(DeleteAttachmentUseCase)
        return delete_attachment_interactor.delete_attachments_start_up()
