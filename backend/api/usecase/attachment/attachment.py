from abc import ABC, abstractmethod
from typing import Literal, Optional, TypedDict

from injector import inject

from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    llm as llm_domain,
    storage as storage_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.services.blob_storage import IBlobStorageService
from api.libs.exceptions import BadRequest


class AttachmentUploadError(TypedDict):
    type: Literal[
        "attachments_exists",
        "get_attachment_error",
        "create_attachment_error",
        "upload_attachment_error",
    ]
    message: str
    attachment_id: Optional[attachment_domain.Id]


class IAttachmentUseCase(ABC):
    @abstractmethod
    def create_attachment(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        user_id: user_domain.Id,
        container_name: storage_domain.ContainerName,
        attachments_for_create: list[attachment_domain.AttachmentForCreate],
    ) -> list[attachment_domain.Attachment]:
        pass

    @abstractmethod
    def get_attachment_signed_url(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        attachment_id: attachment_domain.Id,
    ) -> attachment_domain.SignedUrl:
        pass


class AttachmentUseCase(IAttachmentUseCase):
    @inject
    def __init__(
        self,
        bot_repo: bot_domain.IBotRepository,
        attachment_repo: attachment_domain.IAttachmentRepository,
        blob_storage_service: IBlobStorageService,
    ):
        self.bot_repo = bot_repo
        self.attachment_repo = attachment_repo
        self.blob_storage_service = blob_storage_service

    def _is_pdf_parser_valid(
        self,
        tenant: tenant_domain.Tenant,
        bot: bot_domain.Bot,
        attachments_for_create: list[attachment_domain.AttachmentForCreate],
    ) -> bool:
        include_image = any(attachment.file_extension.is_image() for attachment in attachments_for_create)
        # 画像が含まれていない場合はどのパーサーでも良い
        if not include_image:
            return True
        # 画像が含まれている場合
        # 基盤モデルの場合は、テナントの設定を確認
        if bot.is_basic_ai() and tenant.basic_ai_pdf_parser in [
            llm_domain.BasicAiPdfParser.DOCUMENT_INTELLIGENCE,
            llm_domain.BasicAiPdfParser.LLM_DOCUMENT_READER,
        ]:
            return True
        # 基盤モデル以外の場合は、ボットの設定を確認
        if not bot.is_basic_ai() and bot.pdf_parser in [
            llm_domain.PdfParser.DOCUMENT_INTELLIGENCE,
            llm_domain.PdfParser.LLM_DOCUMENT_READER,
        ]:
            return True
        return False

    def create_attachment(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        user_id: user_domain.Id,
        container_name: storage_domain.ContainerName,
        attachments_for_create: list[attachment_domain.AttachmentForCreate],
    ) -> list[attachment_domain.Attachment]:
        uploaded_attachments: list[attachment_domain.Attachment] = []
        attachment_upload_error: Optional[AttachmentUploadError] = None

        bot = self.bot_repo.find_by_id(bot_id)

        if not self._is_pdf_parser_valid(tenant, bot, attachments_for_create):
            raise BadRequest("ドキュメント読み取りオプションの設定が不正です。")

        for attachment_for_create in attachments_for_create:
            try:
                # アタッチメントをDBに保存
                attachment = self.attachment_repo.create(bot_id, user_id, attachment_for_create)
            except Exception as e:
                file_name = f"{attachment_for_create.name.root}.{attachment_for_create.file_extension}"
                attachment_upload_error = {
                    "type": "create_attachment_error",
                    "message": f"Failed to create attachment : {file_name}{e!s}",
                    "attachment_id": None,
                }
                break

            try:
                # アタッチメントをBlobストレージにアップロード
                self.blob_storage_service.upload_attachment(
                    container_name=container_name,
                    bot_id=bot_id,
                    user_id=user_id,
                    attachment_for_create=attachment_for_create,
                )

            except Exception as e:
                file_name = f"{attachment_for_create.name.root}.{attachment_for_create.file_extension}"
                attachment_upload_error = {
                    "type": "upload_attachment_error",
                    "message": f"Failed to upload attachment {file_name}: {e!s}",
                    "attachment_id": attachment.id,
                }
                break

            uploaded_attachments.append(attachment)

        if attachment_upload_error is not None:
            # 何らかのエラーが発生した場合は、アップロードされたアタッチメントを削除
            if uploaded_attachments:
                for attachment in uploaded_attachments:
                    self.blob_storage_service.delete_attachment_blob(
                        container_name=container_name, bot_id=bot_id, blob_name=attachment.blob_name
                    )
                    self.attachment_repo.delete(attachment.id)
            # アタッチメントが既に存在する場合は、BadRequestを返す
            if attachment_upload_error["type"] == "document_exists":
                raise BadRequest(attachment_upload_error["message"])
            if (
                attachment_upload_error["type"] == "upload_document_error"
                and attachment_upload_error["document_id"] is not None
            ):
                self.attachment_repo.delete(attachment_upload_error["document_id"])
            raise Exception(attachment_upload_error["message"])

        return uploaded_attachments

    def get_attachment_signed_url(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        attachment_id: attachment_domain.Id,
    ) -> attachment_domain.SignedUrl:
        attachment = self.attachment_repo.find_by_id(attachment_id)

        return self.blob_storage_service.create_attachment_blob_sas_url(
            tenant.container_name, bot_id, attachment.blob_name
        )
