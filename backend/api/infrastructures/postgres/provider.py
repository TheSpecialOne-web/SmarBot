from injector import Module, provider
from sqlalchemy.orm import Session

from api.domain.models.api_key import IApiKeyRepository
from api.domain.models.attachment import IAttachmentRepository
from api.domain.models.bot import IBotRepository
from api.domain.models.bot_template import IBotTemplateRepository
from api.domain.models.chat_completion.repository import IChatCompletionRepository
from api.domain.models.chat_completion_export import IChatCompletionExportRepository
from api.domain.models.common_document_template import ICommonDocumentTemplateRepository
from api.domain.models.common_prompt_template import ICommonPromptTemplateRepository
from api.domain.models.conversation import IConversationRepository
from api.domain.models.conversation_export import IConversationExportRepository
from api.domain.models.document import IDocumentRepository
from api.domain.models.document_folder import IDocumentFolderRepository
from api.domain.models.group import IGroupRepository
from api.domain.models.metering import IMeteringRepository
from api.domain.models.notification.repository import INotificationRepository
from api.domain.models.prompt_template import IPromptTemplateRepository
from api.domain.models.question_answer import IQuestionAnswerRepository
from api.domain.models.statistics import IStatisticsRepository
from api.domain.models.tenant import ITenantRepository
from api.domain.models.tenant.tenant_alert import ITenantAlertRepository
from api.domain.models.term import ITermV2Repository
from api.domain.models.user import IUserRepository
from api.domain.models.workflow import IWorkflowRepository
from api.domain.models.workflow_thread import IWorkflowThreadRepository

from .api_key import ApiKeyRepository
from .attachment import AttachmentRepository
from .bot import BotRepository
from .bot_template import BotTemplateRepository
from .chat_completion import ChatCompletionRepository
from .chat_completion_export import ChatCompletionExportRepository
from .common_document_template import CommonDocumentTemplateRepository
from .common_prompt_template import CommonPromptTemplateRepository
from .conversation import ConversationRepository
from .conversation_export import ConversationExportRepository
from .document import DocumentRepository
from .document_folder import DocumentFolderRepository
from .group import GroupRepository
from .metering import MeteringRepository
from .notification import NotificationRepository
from .prompt_template import PromptTemplateRepository
from .question_answer import QuestionAnswerRepository
from .statistics import StatisticsRepository
from .tenant import TenantRepository
from .tenant_alert import TenantAlertRepository
from .term_v2 import TermV2Repository
from .user import UserRepository
from .workflow import WorkflowRepository
from .workflow_thread import WorkflowThreadRepository


class PostgresModule(Module):
    def __init__(self, session: Session) -> None:
        self.session = session

    @provider
    def api_key_repo(self) -> IApiKeyRepository:
        return ApiKeyRepository(self.session)

    @provider
    def attachment_repo(self) -> IAttachmentRepository:
        return AttachmentRepository(self.session)

    @provider
    def bot_template_repo(self) -> IBotTemplateRepository:
        return BotTemplateRepository(self.session)

    @provider
    def bot_repo(self) -> IBotRepository:
        return BotRepository(self.session)

    @provider
    def chat_completion_repo(self) -> IChatCompletionRepository:
        return ChatCompletionRepository(self.session)

    @provider
    def common_document_template_repo(self) -> ICommonDocumentTemplateRepository:
        return CommonDocumentTemplateRepository(self.session)

    @provider
    def common_prompt_template_repo(self) -> ICommonPromptTemplateRepository:
        return CommonPromptTemplateRepository(self.session)

    @provider
    def conversation_export_repo(self) -> IConversationExportRepository:
        return ConversationExportRepository(self.session)

    @provider
    def chat_completion_export_repo(self) -> IChatCompletionExportRepository:
        return ChatCompletionExportRepository(self.session)

    @provider
    def conversation_repo(self) -> IConversationRepository:
        return ConversationRepository(self.session)

    @provider
    def document_folder_repo(self) -> IDocumentFolderRepository:
        return DocumentFolderRepository(self.session)

    @provider
    def document_repo(self) -> IDocumentRepository:
        return DocumentRepository(self.session)

    @provider
    def group_repo(self) -> IGroupRepository:
        return GroupRepository(self.session)

    @provider
    def metering_repo(self) -> IMeteringRepository:
        return MeteringRepository(self.session)

    @provider
    def notification_repo(self) -> INotificationRepository:
        return NotificationRepository(self.session)

    @provider
    def prompt_template_repo(self) -> IPromptTemplateRepository:
        return PromptTemplateRepository(self.session)

    @provider
    def question_answer_repo(self) -> IQuestionAnswerRepository:
        return QuestionAnswerRepository(self.session)

    @provider
    def statistics_repo(self) -> IStatisticsRepository:
        return StatisticsRepository(self.session)

    @provider
    def tenant_alert_repo(self) -> ITenantAlertRepository:
        return TenantAlertRepository(self.session)

    @provider
    def tenant_repo(self) -> ITenantRepository:
        return TenantRepository(self.session)

    @provider
    def term_v2_repo(self) -> ITermV2Repository:
        return TermV2Repository(self.session)

    @provider
    def user_repo(self) -> IUserRepository:
        return UserRepository(self.session)

    @provider
    def workflow_repo(self) -> IWorkflowRepository:
        return WorkflowRepository(self.session)

    @provider
    def workflow_thread_repo(self) -> IWorkflowThreadRepository:
        return WorkflowThreadRepository(self.session)
