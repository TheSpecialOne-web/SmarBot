from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    prompt_template as domain,
    tenant as tenant_domain,
)


class IPromptTemplateUseCase(ABC):
    @abstractmethod
    def bulk_create_prompt_templates(
        self,
        tenant_id: tenant_domain.Id,
        prompt_templates: list[domain.PromptTemplateForCreate],
    ) -> list[domain.PromptTemplate]:
        pass

    @abstractmethod
    def find_prompt_templates_by_tenant_id(
        self,
        tenant_id: tenant_domain.Id,
    ) -> list[domain.PromptTemplate]:
        pass

    @abstractmethod
    def update_prompt_template(
        self,
        tenant_id: tenant_domain.Id,
        id: domain.Id,
        prompt_template: domain.PromptTemplateForUpdate,
    ) -> None:
        pass

    @abstractmethod
    def delete_prompt_templates(
        self,
        tenant_id: tenant_domain.Id,
        ids: list[domain.Id],
    ) -> None:
        pass


class PromptTemplateUseCase(IPromptTemplateUseCase):
    @inject
    def __init__(self, prompt_template_repo: domain.IPromptTemplateRepository):
        self.prompt_template_repo = prompt_template_repo

    def bulk_create_prompt_templates(
        self,
        tenant_id: tenant_domain.Id,
        prompt_templates: list[domain.PromptTemplateForCreate],
    ) -> list[domain.PromptTemplate]:
        return self.prompt_template_repo.bulk_create(
            tenant_id=tenant_id,
            prompt_templates=prompt_templates,
        )

    def find_prompt_templates_by_tenant_id(
        self,
        tenant_id: tenant_domain.Id,
    ) -> list[domain.PromptTemplate]:
        return self.prompt_template_repo.find_by_tenant_id(
            tenant_id=tenant_id,
        )

    def update_prompt_template(
        self,
        tenant_id: tenant_domain.Id,
        id: domain.Id,
        prompt_template: domain.PromptTemplateForUpdate,
    ) -> None:
        current = self.prompt_template_repo.find_by_id_and_tenant_id(
            id=id,
            tenant_id=tenant_id,
        )
        current.update(prompt_template)
        return self.prompt_template_repo.update(current)

    def delete_prompt_templates(
        self,
        tenant_id: tenant_domain.Id,
        ids: list[domain.Id],
    ) -> None:
        return self.prompt_template_repo.delete_by_ids_and_tenant_id(
            tenant_id=tenant_id,
            ids=ids,
        )
