from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from dateutil.relativedelta import relativedelta
from injector import inject

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    chat_completion as chat_completion_domain,
    conversation as conversation_domain,
    metering as metering_domain,
    statistics as statistics_domain,
    tenant as tenant_domain,
    user as user_domain,
    workflow_thread as workflow_thread_domain,
)
from api.domain.models.statistics.token_count_breakdown import TokenCountBreakdown
from api.domain.models.tenant import tenant_alert as tenant_alert_domain
from api.infrastructures.cognitive_search.cognitive_search import (
    ICognitiveSearchService,
)
from api.infrastructures.msgraph.msgraph import IMsgraphService
from api.infrastructures.queue_storage.queue_storage import IQueueStorageService
from api.libs.datetime import convert_jst_to_utc, convert_utc_to_jst
from api.libs.exceptions import NotFound
from api.libs.feature_flag import get_feature_flag
from api.libs.logging import get_logger


class IAlertCapacityUseCase(ABC):
    @abstractmethod
    def alert_capacity(self, tenant_id: tenant_domain.Id, datetime: datetime):
        pass

    @abstractmethod
    def alert_capacity_start_up(self):
        pass


class AlertCapacityUseCase(IAlertCapacityUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        api_key_repo: api_key_domain.IApiKeyRepository,
        user_repo: user_domain.IUserRepository,
        tenant_alert_repo: tenant_alert_domain.ITenantAlertRepository,
        metering_repo: metering_domain.IMeteringRepository,
        statistic_repo: statistics_domain.IStatisticsRepository,
        queue_storage_service: IQueueStorageService,
        cognitive_search_service: ICognitiveSearchService,
        msgraph_service: IMsgraphService,
        conversation_repo: conversation_domain.IConversationRepository,
        chat_completion_repo: chat_completion_domain.IChatCompletionRepository,
        workflow_thread_repo: workflow_thread_domain.IWorkflowThreadRepository,
    ):
        self.logger = get_logger()
        self.tenant_repo = tenant_repo
        self.bot_repo = bot_repo
        self.api_key_repo = api_key_repo
        self.user_repo = user_repo
        self.tenant_alert_repo = tenant_alert_repo
        self.metering_repo = metering_repo
        self.statistic_repo = statistic_repo
        self.queue_storage_service = queue_storage_service
        self.cognitive_search_service = cognitive_search_service
        self.msgraph_service = msgraph_service
        self.conversation_repo = conversation_repo
        self.chat_completion_repo = chat_completion_repo
        self.workflow_thread_repo = workflow_thread_repo

    def alert_capacity(self, tenant_id: tenant_domain.Id, datetime: datetime):
        self.logger.info(f"datetime: {datetime}, tenant_id: {tenant_id}")
        alerts = self._get_alerts(tenant_id)
        if len(alerts) == 0:
            self.logger.info(f"no need to send alert, tenant_id: {tenant_id}")
            return
        self._send_alert_to_admins(tenant_id, alerts)

        now = datetime.now()
        try:
            tenant_alert = self.tenant_alert_repo.find_by_tenant_id(tenant_id)
        except NotFound:
            tenant_alert = tenant_alert_domain.TenantAlert.from_alerts(tenant_id, alerts, now)
            self.tenant_alert_repo.create(tenant_alert)
            return

        tenant_alert.update_by_alerts(alerts, now)
        self.tenant_alert_repo.update(tenant_alert)

    def alert_capacity_start_up(self):
        tenants = self.tenant_repo.find_all()
        tenant_ids = [tenant.id for tenant in tenants]
        self.logger.info(f"tenant_ids: {tenant_ids}")
        now = datetime.now()
        for tenant_id in tenant_ids:
            self.queue_storage_service.send_message_to_alert_capacity_queue(tenant_id, now)
        self.logger.info("sent all messages to alert_capacity_queue")

    def _get_alerts(self, tenant_id: tenant_domain.Id) -> List[tenant_alert_domain.Alert]:
        tenant = self.tenant_repo.find_by_id(tenant_id)
        try:
            tenant_alert = self.tenant_alert_repo.find_by_tenant_id(tenant_id)
        except NotFound:
            tenant_alert = None
        alerts = []

        # ストレージ使用量のチェック
        storage_usage = self.cognitive_search_service.get_index_storage_usage(
            tenant.search_service_endpoint, tenant.index_name
        )
        storage_limit = tenant.usage_limit.free_storage + tenant.usage_limit.additional_storage
        storage_alert = tenant_alert_domain.Alert(
            usage=storage_usage,
            limit=tenant_alert_domain.Limit(root=storage_limit),
            type=tenant_alert_domain.AlertType.STORAGE,
        )
        should_send_storage_alert = storage_alert.should_send_alert(
            last_alerted_at_jst=(
                convert_utc_to_jst(tenant_alert.last_storage_alerted_at.root)
                if tenant_alert and tenant_alert.last_storage_alerted_at is not None
                else None
            ),
            last_alerted_threshold=(
                tenant_alert.last_storage_alerted_threshold.root
                if tenant_alert and tenant_alert.last_storage_alerted_threshold
                else None
            ),
        )
        if should_send_storage_alert:
            alerts.append(
                tenant_alert_domain.Alert(
                    type=tenant_alert_domain.AlertType.STORAGE,
                    usage=storage_usage,
                    limit=tenant_alert_domain.Limit(root=storage_limit),
                )
            )

        # JSTの月初から月末まで
        now = datetime.now()
        start_date_time = convert_jst_to_utc(datetime(now.year, now.month, 1))
        end_date_time = convert_jst_to_utc(datetime(now.year, now.month, 1)) + relativedelta(months=1)

        FLAG = "tmp-ocr-to-token"
        flag = get_feature_flag(FLAG, tenant.id, tenant.name)

        # トークン使用量のチェック
        conversation_token_count = self.conversation_repo.get_conversation_token_count_by_tenant_id(
            tenant_id, start_date_time, end_date_time
        )
        chat_completion_token_count = self.chat_completion_repo.get_chat_completion_token_count_by_tenant_id(
            tenant_id, start_date_time, end_date_time
        )
        pdf_parser_token_count = self.metering_repo.get_pdf_parser_token_count_by_tenant_id(
            tenant_id, start_date_time, end_date_time
        )
        workflow_thread_token_count = self.workflow_thread_repo.get_workflow_thread_token_count_by_tenant_id(
            tenant_id, start_date_time, end_date_time
        )
        token_count_breakdown = TokenCountBreakdown(
            conversation_token_count=conversation_token_count,
            chat_completion_token_count=chat_completion_token_count,
            pdf_parser_token_count=pdf_parser_token_count,
            workflow_thread_token_count=workflow_thread_token_count,
        )
        token_limit = tenant.usage_limit.free_token + tenant.usage_limit.additional_token
        token_alert = tenant_alert_domain.Alert(
            usage=token_count_breakdown.total_token_count,
            limit=tenant_alert_domain.Limit(root=token_limit),
            type=tenant_alert_domain.AlertType.TOKEN,
        )
        should_send_token_alert = token_alert.should_send_alert(
            last_alerted_at_jst=(
                convert_utc_to_jst(tenant_alert.last_token_alerted_at.root)
                if tenant_alert and tenant_alert.last_token_alerted_at is not None
                else None
            ),
            last_alerted_threshold=(
                tenant_alert.last_token_alerted_threshold.root
                if tenant_alert and tenant_alert.last_token_alerted_threshold
                else None
            ),
        )
        if should_send_token_alert:
            alerts.append(
                tenant_alert_domain.Alert(
                    type=tenant_alert_domain.AlertType.TOKEN,
                    usage=token_count_breakdown.total_token_count,
                    limit=tenant_alert_domain.Limit(root=token_limit),
                )
            )

        # OCR使用量のチェック
        if flag:
            return alerts

        ocr_usage = self.metering_repo.get_document_intelligence_page_count(tenant.id, start_date_time, end_date_time)
        ocr_limit = tenant.usage_limit.document_intelligence_page
        ocr_alert = tenant_alert_domain.Alert(
            usage=ocr_usage,
            limit=tenant_alert_domain.Limit(root=ocr_limit),
            type=tenant_alert_domain.AlertType.OCR,
        )
        should_send_ocr_alert = ocr_alert.should_send_alert(
            last_alerted_at_jst=(
                convert_utc_to_jst(tenant_alert.last_ocr_alerted_at.root)
                if tenant_alert and tenant_alert.last_ocr_alerted_at is not None
                else None
            ),
            last_alerted_threshold=(
                tenant_alert.last_ocr_alerted_threshold.root
                if tenant_alert and tenant_alert.last_ocr_alerted_threshold
                else None
            ),
        )
        if should_send_ocr_alert:
            alerts.append(
                tenant_alert_domain.Alert(
                    type=tenant_alert_domain.AlertType.OCR,
                    usage=ocr_usage,
                    limit=tenant_alert_domain.Limit(root=ocr_limit),
                )
            )

        return alerts

    def _send_alert_to_admins(self, tenant_id: tenant_domain.Id, alerts: List[tenant_alert_domain.Alert]) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)

        admins = self.user_repo.find_admins_by_tenant_id(tenant_id)
        administrators = self.user_repo.find_administrators()

        self.msgraph_service.send_alert_email_to_tenant_users(
            tenant_name=tenant.name,
            recipients=[admin.email for admin in admins],
            bcc_recipients=[administrator.email for administrator in administrators],
            alerts=alerts,
        )
