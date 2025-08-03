from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import (
    job as job_domain,
    tenant as tenant_domain,
)
from api.usecase.job.delete_attachments import DeleteAttachmentUseCase


def delete_attachments(message_content: dict, dequeue_count: int = 0):
    tid = message_content.get("tenant_id")
    if not tid:
        raise ValueError("tenant_id is required")
    msg = job_domain.DeleteAttachmentsQueue(tenant_id=tenant_domain.Id(value=tid))

    with SessionFactory() as session:
        injector = get_injector(session)
        delete_attachment_interactor = injector.get(DeleteAttachmentUseCase)
        delete_attachment_interactor.delete_attachments(msg.tenant_id)
