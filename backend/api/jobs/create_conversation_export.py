from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.create_conversation_export import CreateConversationExportUseCase


def create_conversation_export(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.CreateConversationExportQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        create_conversation_export_interactor = injector.get(CreateConversationExportUseCase)
        create_conversation_export_interactor.create_conversation_export(msg.tenant_id, msg.conversation_export_id)
