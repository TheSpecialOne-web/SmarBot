from abc import ABC, abstractmethod
import uuid

from injector import inject
from pydantic import BaseModel

from api.domain.models.bot_template import (
    BotTemplate,
    BotTemplateForCreate,
    BotTemplateForUpdate,
    IBotTemplateRepository,
    IconFileExtension,
    Id,
)
from api.domain.services.blob_storage.blob_storage import IBlobStorageService
from api.libs.logging import get_logger


class UploadBotTemplateIconInput(BaseModel):
    file: bytes
    extension: IconFileExtension

    def to_file_path(self, bot_template_id: Id) -> str:
        return f"bot-templates/{bot_template_id.root}/icons/{uuid.uuid4()}.{self.extension.value}"


class IBotTemplateUseCase(ABC):
    @abstractmethod
    def find_all_bot_templates(self) -> list[BotTemplate]:
        pass

    @abstractmethod
    def find_bot_template_by_id(self, id: Id) -> BotTemplate:
        pass

    @abstractmethod
    def find_public_bot_templates(self) -> list[BotTemplate]:
        pass

    @abstractmethod
    def create_bot_template(self, bot_template: BotTemplateForCreate) -> BotTemplate:
        pass

    @abstractmethod
    def update_bot_template(self, id: Id, bot_template: BotTemplateForUpdate) -> None:
        pass

    @abstractmethod
    def delete_bot_template(self, id: Id) -> None:
        pass

    @abstractmethod
    def upload_bot_template_icon(self, bot_template_id: Id, input: UploadBotTemplateIconInput) -> None:
        pass

    @abstractmethod
    def delete_bot_template_icon(self, bot_template_id: Id) -> None:
        pass


class BotTemplateUseCase(IBotTemplateUseCase):
    @inject
    def __init__(self, bot_template_repo: IBotTemplateRepository, blob_storage_service: IBlobStorageService) -> None:
        self.logger = get_logger()
        self.bot_template_repo = bot_template_repo
        self.blob_storage_service = blob_storage_service

    def find_all_bot_templates(self) -> list[BotTemplate]:
        return self.bot_template_repo.find_all()

    def find_bot_template_by_id(self, id: Id) -> BotTemplate:
        return self.bot_template_repo.find_by_id(id=id)

    def find_public_bot_templates(self) -> list[BotTemplate]:
        return self.bot_template_repo.find_public()

    def create_bot_template(self, bot_template: BotTemplateForCreate) -> BotTemplate:
        return self.bot_template_repo.create(bot_template=bot_template)

    def update_bot_template(self, id: Id, bot_template: BotTemplateForUpdate) -> None:
        bot_template_to_update = self.bot_template_repo.find_by_id(id=id)
        bot_template_to_update.update(bot_template_for_update=bot_template)
        self.bot_template_repo.update(bot_template=bot_template_to_update)

    def delete_bot_template(self, id: Id) -> None:
        self.bot_template_repo.delete(id=id)

    def upload_bot_template_icon(self, bot_template_id: Id, input: UploadBotTemplateIconInput) -> None:
        bot_template = self.bot_template_repo.find_by_id(bot_template_id)
        old_icon_url = bot_template.icon_url

        filepath = input.to_file_path(bot_template_id)
        icon_url = self.blob_storage_service.upload_bot_template_icon(filepath, input.file)

        bot_template.update_icon_url(icon_url)
        self.bot_template_repo.update(bot_template)

        if old_icon_url is None:
            return
        try:
            self.blob_storage_service.delete_bot_template_icon(bot_template_id, old_icon_url)
        except Exception as e:
            # アイコンのアップロードは成功しているので、エラーログを出力して処理を続行
            self.logger.error(f"Failed to delete old icon: {old_icon_url}, error: {e!s}")

    def delete_bot_template_icon(self, bot_template_id: Id) -> None:
        bot_template = self.bot_template_repo.find_by_id(bot_template_id)
        if bot_template.icon_url is None:
            return
        try:
            self.blob_storage_service.delete_bot_template_icon(bot_template_id, bot_template.icon_url)
        except Exception as e:
            # アイコンの削除は失敗しているが、処理を続行してDBのicon_urlを削除
            self.logger.error(f"Failed to delete icon: {bot_template.icon_url}, error: {e!s}")

        bot_template.update_icon_url(None)
        self.bot_template_repo.update(bot_template)
