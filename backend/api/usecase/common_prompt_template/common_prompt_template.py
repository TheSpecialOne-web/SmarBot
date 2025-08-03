from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot_template as bt_domain,
    common_prompt_template as cpt_domain,
)


class ICommonPromptTemplateUseCase(ABC):
    @abstractmethod
    def find_common_prompt_templates_by_bot_template_id(
        self,
        bot_template_id: bt_domain.Id,
    ) -> list[cpt_domain.CommonPromptTemplate]:
        pass

    @abstractmethod
    def create_common_prompt_template(
        self,
        bot_template_id: bt_domain.Id,
        common_prompt_template: cpt_domain.CommonPromptTemplateForCreate,
    ) -> cpt_domain.CommonPromptTemplate:
        pass

    @abstractmethod
    def update_common_prompt_template(
        self,
        bot_template_id: bt_domain.Id,
        id: cpt_domain.Id,
        common_prompt_template: cpt_domain.CommonPromptTemplateForUpdate,
    ) -> None:
        pass

    @abstractmethod
    def delete_common_prompt_templates(
        self,
        bot_template_id: bt_domain.Id,
        ids: list[cpt_domain.Id],
    ) -> None:
        pass


class CommonPromptTemplateUseCase(ICommonPromptTemplateUseCase):
    @inject
    def __init__(
        self,
        common_prompt_template_repo: cpt_domain.ICommonPromptTemplateRepository,
        bot_template_repo: bt_domain.IBotTemplateRepository,
    ):
        self.common_prompt_template_repo = common_prompt_template_repo
        self.bot_template_repo = bot_template_repo

    def find_common_prompt_templates_by_bot_template_id(
        self,
        bot_template_id: bt_domain.Id,
    ) -> list[cpt_domain.CommonPromptTemplate]:
        return self.common_prompt_template_repo.find_by_bot_template_id(
            bot_template_id=bot_template_id,
        )

    def create_common_prompt_template(
        self,
        bot_template_id: bt_domain.Id,
        common_prompt_template: cpt_domain.CommonPromptTemplateForCreate,
    ) -> cpt_domain.CommonPromptTemplate:
        return self.common_prompt_template_repo.create(
            bot_template_id=bot_template_id,
            common_prompt_template=common_prompt_template,
        )

    def update_common_prompt_template(
        self,
        bot_template_id: bt_domain.Id,
        id: cpt_domain.Id,
        common_prompt_template: cpt_domain.CommonPromptTemplateForUpdate,
    ) -> None:
        current = self.common_prompt_template_repo.find_by_id(
            id=id,
            bot_template_id=bot_template_id,
        )
        current.update(common_prompt_template)
        return self.common_prompt_template_repo.update(
            bot_template_id=bot_template_id,
            common_prompt_template=current,
        )

    def delete_common_prompt_templates(
        self,
        bot_template_id: bt_domain.Id,
        ids: list[cpt_domain.Id],
    ) -> None:
        return self.common_prompt_template_repo.delete_by_ids_and_bot_template_id(
            ids=ids,
            bot_template_id=bot_template_id,
        )
