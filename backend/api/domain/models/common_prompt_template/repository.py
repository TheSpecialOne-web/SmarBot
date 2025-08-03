from abc import ABC, abstractmethod

from ..bot_template.id import Id as BotTemplateId
from .common_prompt_template import CommonPromptTemplate, CommonPromptTemplateForCreate
from .id import Id as CommonPromptTemplateId


class ICommonPromptTemplateRepository(ABC):
    @abstractmethod
    def find_by_bot_template_id(self, bot_template_id: BotTemplateId) -> list[CommonPromptTemplate]:
        pass

    @abstractmethod
    def find_by_id(self, bot_template_id: BotTemplateId, id: CommonPromptTemplateId) -> CommonPromptTemplate:
        pass

    @abstractmethod
    def create(
        self, bot_template_id: BotTemplateId, common_prompt_template: CommonPromptTemplateForCreate
    ) -> CommonPromptTemplate:
        pass

    @abstractmethod
    def update(self, bot_template_id: BotTemplateId, common_prompt_template: CommonPromptTemplate) -> None:
        pass

    @abstractmethod
    def delete_by_ids_and_bot_template_id(
        self,
        bot_template_id: BotTemplateId,
        ids: list[CommonPromptTemplateId],
    ) -> None:
        pass
