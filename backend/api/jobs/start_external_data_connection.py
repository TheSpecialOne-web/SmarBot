from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.start_external_data_connection import StartExternalDataConnectionUseCase


def start_external_data_connection(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.StartExternalDataConnectionQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        document_interactor = injector.get(StartExternalDataConnectionUseCase)
        document_interactor.start_external_data_connection(
            tenant_id=msg.tenant_id, bot_id=msg.bot_id, document_folder_id=msg.document_folder_id
        )
