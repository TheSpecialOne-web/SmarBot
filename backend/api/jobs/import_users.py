from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.import_users import ImportUsersUseCase


def import_users(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.UsersImportQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        import_users_interactor = injector.get(ImportUsersUseCase)
        import_users_interactor.import_users(msg.tenant_id, msg.filename)
