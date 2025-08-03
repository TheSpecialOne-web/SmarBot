from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    tenant as tenant_domain,
)
from api.domain.services.blob_storage import IBlobStorageService
from api.infrastructures.queue_storage.queue_storage import IQueueStorageService
from api.libs.logging import get_logger


class IDeleteAttachmentUseCase(ABC):
    @abstractmethod
    def delete_attachments(self, tenant_id: tenant_domain.Id):
        pass

    @abstractmethod
    def delete_attachments_start_up(self):
        pass


class DeleteAttachmentUseCase(IDeleteAttachmentUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        attachment_repo: attachment_domain.IAttachmentRepository,
        blob_storage_service: IBlobStorageService,
        queue_storage_service: IQueueStorageService,
    ):
        self.logger = get_logger()
        self.bot_repo = bot_repo
        self.tenant_repo = tenant_repo
        self.attachment_repo = attachment_repo
        self.blob_storage_service = blob_storage_service
        self.queue_storage_service = queue_storage_service

    def delete_attachments(self, tenant_id: tenant_domain.Id):
        tenant = self.tenant_repo.find_by_id(tenant_id)
        bots = self.bot_repo.find_all_by_tenant_id(tenant_id)
        bot_ids = [bot.id for bot in bots]

        for bot_id in bot_ids:
            attachments = self.attachment_repo.get_attachments_by_bot_id_after_24_hours(bot_id)
            if len(attachments) == 0:
                continue
            for attachment in attachments:
                try:
                    self._delete_single_attachment(tenant, bot_id, attachment)
                except Exception as e:
                    self.logger.warning(f"Error deleting attachment: {attachment.model_dump_json()}. Details: {e}")

    def delete_attachments_start_up(self):
        self.logger.info("Start Time Job Queue delete_attachments_start_up")

        tenants = self.tenant_repo.find_all()
        tenant_ids = [tenant.id for tenant in tenants]
        self.logger.info(f"tenant_ids: {tenant_ids}")

        for tenant_id in tenant_ids:
            self.queue_storage_service.send_message_to_delete_attachment_queue(tenant_id)

    def _delete_single_attachment(
        self, tenant: tenant_domain.Tenant, bot_id: bot_domain.Id, attachment: attachment_domain.Attachment
    ) -> None:
        self.blob_storage_service.delete_attachment_blob(
            container_name=tenant.container_name, bot_id=bot_id, blob_name=attachment.blob_name
        )
        self.attachment_repo.update_blob_deleted(attachment.id)
        self.logger.info(f"deleted attachment: {attachment.model_dump_json()}")
