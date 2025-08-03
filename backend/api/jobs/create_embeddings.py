from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.create_embeddings import CreateEmbeddingsUseCase


def create_embeddings(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.CreateEmbeddingsQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        create_embeddings_interactor = injector.get(CreateEmbeddingsUseCase)
        create_embeddings_interactor.create_embeddings(msg.tenant_id, msg.bot_id, msg.document_id, dequeue_count)
