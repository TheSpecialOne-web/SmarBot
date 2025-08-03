from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.create_chat_completion_export import (
    CreateChatCompletionExportUseCase,
)


def create_chat_completion_export(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.CreateChatCompletionExportQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        create_conversation_export_interactor = injector.get(CreateChatCompletionExportUseCase)
        create_conversation_export_interactor.create_chat_completion_export(
            msg.tenant_id, msg.chat_completion_export_id
        )
