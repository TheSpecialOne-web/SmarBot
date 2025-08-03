from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    document as document_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.attachment.repository import IAttachmentRepository
from api.domain.models.chat_completion.repository import IChatCompletionRepository
from api.domain.models.conversation.repository import IConversationRepository
from api.domain.models.document_folder.repository import IDocumentFolderRepository
from api.domain.models.question_answer.repository import IQuestionAnswerRepository
from api.domain.models.term.repository import ITermV2Repository
from api.domain.services.blob_storage import IBlobStorageService
from api.infrastructures.cognitive_search.cognitive_search import (
    ICognitiveSearchService,
)
from api.libs.feature_flag import get_feature_flag
from api.libs.logging import get_logger


class IDeleteBotUseCase(ABC):
    @abstractmethod
    def delete_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id):
        pass


class DeleteBotUseCase(IDeleteBotUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        api_key_repo: api_key_domain.IApiKeyRepository,
        document_repo: document_domain.IDocumentRepository,
        attachment_repo: IAttachmentRepository,
        conversation_repo: IConversationRepository,
        document_folder_repo: IDocumentFolderRepository,
        question_answer_repo: IQuestionAnswerRepository,
        term_v2_repo: ITermV2Repository,
        chat_completion_repo: IChatCompletionRepository,
        user_repo: user_domain.IUserRepository,
        blob_storage_service: IBlobStorageService,
        cognitive_search_service: ICognitiveSearchService,
    ):
        self.logger = get_logger()
        self.bot_repo = bot_repo
        self.tenant_repo = tenant_repo
        self.api_key_repo = api_key_repo
        self.document_repo = document_repo
        self.attachment_repo = attachment_repo
        self.conversation_repo = conversation_repo
        self.document_folder_repo = document_folder_repo
        self.question_answer_repo = question_answer_repo
        self.term_v2_repo = term_v2_repo
        self.chat_completion_repo = chat_completion_repo
        self.user_repo = user_repo
        self.blob_storage_service = blob_storage_service
        self.cognitive_search_service = cognitive_search_service

    def delete_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id):
        tenant = self.tenant_repo.find_by_id(tenant_id)
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)
        documents = self.document_repo.find_by_bot_id(bot_id)

        if bot.status != bot_domain.Status.DELETING:
            raise Exception(f"bot is not in deleting status. bot_id: {bot_id.value}")

        if not all(document.status == document_domain.Status.DELETING for document in documents):
            raise Exception("some documents are not in deleting status.")

        FLAG_KEY = "blob-container-renewal"
        feature_flag = get_feature_flag(FLAG_KEY, tenant_id, tenant.name, default=True)

        self.logger.info(f"deleting bot from blob storage. bot_id: {bot_id.value}")
        if bot.icon_url is not None:
            self.blob_storage_service.delete_bot_icon(tenant.alias, bot.icon_url)

        if feature_flag:
            self.blob_storage_service.delete_blobs_by_bot_id(tenant.container_name, bot.id)
        else:
            if bot.container_name is None:
                raise Exception("container_name is not set")
            self.blob_storage_service.delete_blob_container(bot.container_name)

        self.logger.info(f"deleting bot from AI search. bot_id: {bot_id.value}")
        if bot.approach in [bot_domain.Approach.NEOLLM, bot_domain.Approach.URSA, bot_domain.Approach.CUSTOM_GPT]:
            search_service_endpoint = (
                tenant.search_service_endpoint
                if bot.search_method not in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]
                else bot.search_service_endpoint
            )
            if search_service_endpoint is None:
                raise Exception("search service endpoint is not set")

            index_name = (
                tenant.index_name
                if bot.search_method not in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]
                else bot.index_name
            )
            if index_name is None:
                raise Exception("index name is not set")

            if bot.search_method in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]:
                self.cognitive_search_service.delete_index(search_service_endpoint, index_name)
            else:
                self.cognitive_search_service.delete_documents_from_index_by_bot_id(
                    search_service_endpoint, index_name, bot.id
                )

        self.logger.info(f"deleting bot from database. bot_id: {bot_id.value}")
        self.chat_completion_repo.delete_completions_and_data_points_by_bot_id(bot_id)
        self.api_key_repo.delete_by_bot_id(bot_id)
        self.attachment_repo.delete_by_bot_id(bot_id)
        self.conversation_repo.delete_by_bot_id(bot_id)
        self.document_folder_repo.delete_by_bot_id(bot_id)
        self.document_repo.delete_by_bot_id(bot_id)
        self.question_answer_repo.delete_by_bot_id(bot_id)
        self.term_v2_repo.delete_by_bot_id(bot_id)
        self.user_repo.delete_user_policy_by_bot_id(bot_id)
        self.bot_repo.delete_prompt_templates_by_bot_id(bot_id)
        self.bot_repo.delete(bot.id)

        self.logger.info(f"bot deleted. bot_id: {bot_id.value}")
