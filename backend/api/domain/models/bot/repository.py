from abc import ABC, abstractmethod

from ..group import Id as GroupId
from ..llm.model import ModelFamily
from ..tenant import Id as TenantId
from ..text_2_image_model import Text2ImageModelFamily
from ..user import Id as UserId
from .approach import Approach
from .bot import Bot, BotForCreate, BotWithGroupName, BotWithTenant
from .id import Id
from .name import Name
from .prompt_template import (
    Id as PromptTemplateId,
    PromptTemplate,
    PromptTemplateForCreate,
)
from .status import Status


class IBotRepository(ABC):
    @abstractmethod
    def find_by_id(self, id: Id, include_deleted: bool = False) -> Bot:
        pass

    @abstractmethod
    def find_by_id_and_group_id(self, id: Id, group_id: GroupId) -> Bot:
        pass

    @abstractmethod
    def find_with_tenant_by_id(self, id: Id) -> BotWithTenant:
        pass

    @abstractmethod
    def find_by_tenant_id(self, tenant_id: TenantId, statuses: list[Status] | None = None) -> list[Bot]:
        pass

    @abstractmethod
    def find_all_by_tenant_id(self, tenant_id: TenantId, include_deleted: bool = False) -> list[Bot]:
        pass

    @abstractmethod
    def find_by_id_and_tenant_id(self, id: Id, tenant_id: TenantId) -> Bot:
        pass

    @abstractmethod
    def find_by_ids_and_tenant_id(
        self, ids: list[Id], tenant_id: TenantId, statuses: list[Status] | None = None
    ) -> list[Bot]:
        pass

    @abstractmethod
    def find_by_ids_and_group_id(
        self, bot_ids: list[Id], group_id: GroupId, statuses: list[Status] | None = None
    ) -> list[Bot]:
        pass

    @abstractmethod
    def find_by_tenant_id_and_approaches(
        self,
        tenant_id: TenantId,
        approaches: list[Approach],
        exclude_ids: list[Id],
        statuses: list[Status] | None = None,
    ) -> list[Bot]:
        pass

    @abstractmethod
    def find_by_group_id_and_name(self, group_id: GroupId, name: Name) -> Bot:
        pass

    @abstractmethod
    def find_basic_ai_by_response_generator_model_family(
        self, tenant_id: TenantId, group_id: GroupId, model_family: ModelFamily, statuses: list[Status]
    ) -> Bot:
        pass

    @abstractmethod
    def find_basic_ai_by_image_generator_model_family(
        self,
        tenant_id: TenantId,
        group_id: GroupId,
        model_family: Text2ImageModelFamily,
        statuses: list[Status],
    ) -> Bot:
        pass

    @abstractmethod
    def find_with_groups_by_tenant_id(
        self, tenant_id: TenantId, statuses: list[Status] | None = None
    ) -> list[BotWithGroupName]:
        pass

    @abstractmethod
    def find_with_groups_by_ids_and_tenant_id(
        self, ids: list[Id], tenant_id: TenantId, statuses: list[Status] | None = None
    ) -> list[BotWithGroupName]:
        pass

    @abstractmethod
    def create(self, tenant_id: TenantId, group_id: GroupId, bot: BotForCreate) -> Bot:
        pass

    @abstractmethod
    def delete(self, id: Id) -> None:
        pass

    @abstractmethod
    def hard_delete_by_tenant_id(self, tenant_id: TenantId) -> None:
        pass

    @abstractmethod
    def update(self, bot: Bot) -> None:
        pass

    @abstractmethod
    def find_prompt_template_by_id_and_bot_id(
        self,
        bot_id: Id,
        bot_prompt_template_id: PromptTemplateId,
    ) -> PromptTemplate:
        pass

    @abstractmethod
    def find_prompt_templates_by_bot_id(
        self,
        bot_id: Id,
    ) -> list[PromptTemplate]:
        pass

    @abstractmethod
    def create_prompt_template(
        self,
        bot_id: Id,
        prompt_template: PromptTemplateForCreate,
    ) -> PromptTemplate:
        pass

    @abstractmethod
    def update_prompt_template(
        self,
        bot_id: Id,
        prompt_template: PromptTemplate,
    ) -> None:
        pass

    @abstractmethod
    def delete_prompt_templates(
        self,
        bot_id: Id,
        bot_prompt_template_ids: list[PromptTemplateId],
    ) -> None:
        pass

    @abstractmethod
    def delete_prompt_templates_by_bot_id(self, bot_id: Id) -> None:
        pass

    @abstractmethod
    def add_liked_bot(self, tenant_id: TenantId, bot_id: Id, user_id: UserId) -> None:
        pass

    @abstractmethod
    def remove_liked_bot(self, bot_id: Id, user_id: UserId) -> None:
        pass

    @abstractmethod
    def find_liked_bot_ids_by_user_id(self, user_id: UserId) -> list[Id]:
        pass

    @abstractmethod
    def find_by_group_id(
        self, tenant_id: TenantId, group_id: GroupId, statuses: list[Status] | None = None
    ) -> list[Bot]:
        pass

    @abstractmethod
    def update_bot_group(self, bot_id: Id, group_id: GroupId) -> None:
        pass
