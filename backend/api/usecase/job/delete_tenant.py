from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    api_key as api_key_domain,
    attachment as attachment_domain,
    bot as bot_domain,
    chat_completion as chat_completion_domain,
    conversation as conversation_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    metering as metering_domain,
    prompt_template as prompt_template_domain,
    question_answer as question_answer_domain,
    tenant as tenant_domain,
    term as term_domain,
    user as user_domain,
)
from api.libs.exceptions import NotFound
from api.libs.logging import get_logger


class IDeleteTenantUseCase(ABC):
    @abstractmethod
    def delete_tenant(self, tenant_id: tenant_domain.Id) -> None:
        pass


class DeleteTenantUseCase(IDeleteTenantUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        group_repo: group_domain.IGroupRepository,
        metering_repo: metering_domain.IMeteringRepository,
        prompt_template_repo: prompt_template_domain.IPromptTemplateRepository,
        bot_repo: bot_domain.IBotRepository,
        api_key_repo: api_key_domain.IApiKeyRepository,
        document_repo: document_domain.IDocumentRepository,
        attachment_repo: attachment_domain.IAttachmentRepository,
        conversation_repo: conversation_domain.IConversationRepository,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
        question_answer_repo: question_answer_domain.IQuestionAnswerRepository,
        term_v2_repo: term_domain.ITermV2Repository,
        chat_completion_repo: chat_completion_domain.IChatCompletionRepository,
        user_repo: user_domain.IUserRepository,
    ):
        self.logger = get_logger()
        self.bot_repo = bot_repo
        self.tenant_repo = tenant_repo
        self.group_repo = group_repo
        self.metering_repo = metering_repo
        self.prompt_template_repo = prompt_template_repo
        self.api_key_repo = api_key_repo
        self.document_repo = document_repo
        self.attachment_repo = attachment_repo
        self.conversation_repo = conversation_repo
        self.document_folder_repo = document_folder_repo
        self.question_answer_repo = question_answer_repo
        self.term_v2_repo = term_v2_repo
        self.chat_completion_repo = chat_completion_repo
        self.user_repo = user_repo

    def delete_tenant(self, tenant_id: tenant_domain.Id) -> None:
        is_tenant_soft_deleted = False
        try:
            self.tenant_repo.find_by_id(tenant_id)
        except NotFound:
            is_tenant_soft_deleted = True
        if not is_tenant_soft_deleted:
            raise Exception(f"Tenant is not soft deleted. Skip hard delete. tenant_id: {tenant_id}")

        bots = self.bot_repo.find_all_by_tenant_id(tenant_id, include_deleted=True)
        bot_ids = [bot.id for bot in bots]
        users = self.user_repo.find_by_tenant_id(tenant_id, include_deleted=True)
        user_ids = [user.id for user in users]
        api_keys = self.api_key_repo.find_by_bot_ids(bot_ids, include_deleted=True)
        api_key_ids = [api_key.id for api_key in api_keys]
        document_folders = self.document_folder_repo.find_by_bot_ids(bot_ids, include_deleted=True)
        document_folder_ids = [document_folder.id for document_folder in document_folders]

        self.chat_completion_repo.hard_delete_by_api_key_ids(api_key_ids)
        self.api_key_repo.hard_delete_by_bot_ids(bot_ids)
        self.attachment_repo.hard_delete_by_bot_ids(bot_ids)
        self.conversation_repo.hard_delete_by_user_ids(user_ids)
        self.document_repo.hard_delete_by_document_folder_ids(document_folder_ids)
        # フォルダ機能以前に削除されたドキュメントには document_folder_id がないので、bot_id で削除する
        self.document_repo.hard_delete_by_bot_ids(bot_ids)
        self.document_folder_repo.hard_delete_by_bot_ids(bot_ids)
        self.term_v2_repo.hard_delete_by_bot_ids(bot_ids)
        self.question_answer_repo.hard_delete_by_bot_ids(bot_ids)
        self.metering_repo.hard_delete_by_tenant_id(tenant_id)
        self.bot_repo.hard_delete_by_tenant_id(tenant_id)
        self.group_repo.hard_delete_by_tenant_id(tenant_id)
        self.user_repo.hard_delete_by_tenant_id(tenant_id)
        self.prompt_template_repo.hard_delete_by_tenant_id(tenant_id)
        self.tenant_repo.hard_delete(tenant_id)

        self.logger.info(f"Deleted tenant: {tenant_id}")
