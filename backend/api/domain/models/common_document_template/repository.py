from abc import ABC, abstractmethod

from ..bot_template import Id as BotTemplateId
from .common_document_template import (
    Basename,
    CommonDocumentTemplate,
    CommonDocumentTemplateForCreate,
    FileExtension,
)
from .id import Id


class ICommonDocumentTemplateRepository(ABC):
    @abstractmethod
    def find_by_bot_template_id(self, bot_template_id: BotTemplateId) -> list[CommonDocumentTemplate]:
        pass

    @abstractmethod
    def find_by_id(self, bot_template_id: BotTemplateId, id: Id) -> CommonDocumentTemplate:
        pass

    @abstractmethod
    def find_by_bot_template_id_and_basename_and_file_extension(
        self, bot_template_id: BotTemplateId, basename: Basename, file_extension: FileExtension
    ) -> CommonDocumentTemplate:
        pass

    @abstractmethod
    def create(
        self, bot_template_id: BotTemplateId, common_document_template: CommonDocumentTemplateForCreate
    ) -> CommonDocumentTemplate:
        pass

    @abstractmethod
    def update(self, bot_template_id: BotTemplateId, common_document_template: CommonDocumentTemplate) -> None:
        pass

    @abstractmethod
    def delete(self, bot_template_id: BotTemplateId, id: Id) -> None:
        pass
