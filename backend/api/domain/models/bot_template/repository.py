from abc import ABC, abstractmethod

from .bot_template import BotTemplate, BotTemplateForCreate
from .id import Id


class IBotTemplateRepository(ABC):
    @abstractmethod
    def find_all(self) -> list[BotTemplate]:
        pass

    @abstractmethod
    def find_by_id(self, id: Id) -> BotTemplate:
        pass

    @abstractmethod
    def find_public(self) -> list[BotTemplate]:
        pass

    @abstractmethod
    def create(self, bot_template: BotTemplateForCreate) -> BotTemplate:
        pass

    @abstractmethod
    def update(self, bot_template: BotTemplate) -> None:
        pass

    @abstractmethod
    def delete(self, id: Id) -> None:
        pass
