from abc import ABC, abstractmethod

from injector import inject

from api.domain.models.bot_template import (
    IBotTemplateRepository,
    Id as BotTemplateId,
)
from api.domain.models.common_document_template import (
    CommonDocumentTemplate,
    CommonDocumentTemplateForCreate,
    CommonDocumentTemplateForUpdate,
    ICommonDocumentTemplateRepository,
    Id,
    Url,
)
from api.domain.services.blob_storage.blob_storage import IBlobStorageService
from api.libs.exceptions import BadRequest, NotFound
from api.libs.logging import logging

logger = logging.getLogger(__name__)


class ICommonDocumentTemplateUseCase(ABC):
    @abstractmethod
    def find_common_document_templates_by_bot_template_id(
        self, bot_template_id: BotTemplateId
    ) -> list[CommonDocumentTemplate]:
        pass

    @abstractmethod
    def create_common_document_template(
        self,
        bot_template_id: BotTemplateId,
        common_document_templates_for_create: list[CommonDocumentTemplateForCreate],
    ) -> None:
        pass

    @abstractmethod
    def update_common_document_template(
        self,
        bot_template_id: BotTemplateId,
        id: Id,
        common_document_template_for_update: CommonDocumentTemplateForUpdate,
    ) -> None:
        pass

    @abstractmethod
    def delete_common_document_template(self, bot_template_id: BotTemplateId, id: Id) -> None:
        pass

    @abstractmethod
    def get_url_by_bot_template_id_and_id(self, bot_template_id: BotTemplateId, id: Id) -> Url:
        pass


class CommonDocumentTemplateUseCase(ICommonDocumentTemplateUseCase):
    @inject
    def __init__(
        self,
        common_document_template_repo: ICommonDocumentTemplateRepository,
        bot_template_repo: IBotTemplateRepository,
        blob_storage_service: IBlobStorageService,
    ) -> None:
        self.common_document_template_repo = common_document_template_repo
        self.bot_template_repo = bot_template_repo
        self.blob_storage_service = blob_storage_service

    def find_common_document_templates_by_bot_template_id(
        self, bot_template_id: BotTemplateId
    ) -> list[CommonDocumentTemplate]:
        return self.common_document_template_repo.find_by_bot_template_id(bot_template_id=bot_template_id)

    def create_common_document_template(
        self,
        bot_template_id: BotTemplateId,
        common_document_templates_for_create: list[CommonDocumentTemplateForCreate],
    ) -> None:
        for common_document_template_for_create in common_document_templates_for_create:
            try:
                self.common_document_template_repo.find_by_bot_template_id_and_basename_and_file_extension(
                    bot_template_id=bot_template_id,
                    basename=common_document_template_for_create.basename,
                    file_extension=common_document_template_for_create.file_extension,
                )
            except NotFound:
                continue
            else:
                raise BadRequest("すでに同じ名前のドキュメントが存在します。")
        for common_document_template_for_create in common_document_templates_for_create:
            # ドキュメントをblob_storageに保存
            self.blob_storage_service.upload_common_document_template_to_common_container(
                bot_template_id=bot_template_id,
                common_document_template=common_document_template_for_create,
            )

            try:
                self.common_document_template_repo.create(
                    bot_template_id=bot_template_id, common_document_template=common_document_template_for_create
                )
            except Exception as e:
                self.blob_storage_service.delete_common_document_template_from_common_container(
                    bot_template_id=bot_template_id,
                    blob_name=common_document_template_for_create.blob_name,
                )
                raise e

    def update_common_document_template(
        self,
        bot_template_id: BotTemplateId,
        id: Id,
        common_document_template_for_update: CommonDocumentTemplateForUpdate,
    ) -> None:
        common_document_template = self.common_document_template_repo.find_by_id(
            bot_template_id=bot_template_id, id=id
        )
        common_document_template.update(common_document_template_for_update)
        self.common_document_template_repo.update(
            bot_template_id=bot_template_id, common_document_template=common_document_template
        )

    def delete_common_document_template(self, bot_template_id: BotTemplateId, id: Id) -> None:
        common_document_template = self.common_document_template_repo.find_by_id(
            bot_template_id=bot_template_id, id=id
        )
        self.common_document_template_repo.delete(bot_template_id=bot_template_id, id=id)
        self.blob_storage_service.delete_common_document_template_from_common_container(
            bot_template_id=bot_template_id,
            blob_name=common_document_template.blob_name,
        )

    def get_url_by_bot_template_id_and_id(self, bot_template_id: BotTemplateId, id: Id) -> Url:
        common_document_template = self.common_document_template_repo.find_by_id(
            bot_template_id=bot_template_id, id=id
        )
        return self.blob_storage_service.create_common_document_template_url(
            bot_template_id=bot_template_id,
            blob_name=common_document_template.blob_name,
        )
