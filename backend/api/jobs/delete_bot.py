from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.delete_bot import DeleteBotUseCase


def delete_bot(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.DeleteBotQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        delete_bot_interactor = injector.get(DeleteBotUseCase)
        delete_bot_interactor.delete_bot(msg.tenant_id, msg.bot_id)
