from unittest.mock import Mock

import pytest

from api.domain.models import (
    prompt_template as domain,
    tenant as tenant_domain,
)
from api.usecase.prompt_template.prompt_template import PromptTemplateUseCase


class TestPromptTemplateUseCase:
    @pytest.fixture
    def setup(self):
        self.prompt_template_repo = Mock()
        self.prompt_template_usecase = PromptTemplateUseCase(
            prompt_template_repo=self.prompt_template_repo,
        )

    def test_bulk_create_prompt_templates(self, setup):
        want = [
            domain.PromptTemplate(
                id=domain.Id(value=1),
                title=domain.Title(value="title1"),
                description=domain.Description(value="description1"),
                prompt=domain.Prompt(value="prompt1"),
            ),
            domain.PromptTemplate(
                id=domain.Id(value=2),
                title=domain.Title(value="title2"),
                description=domain.Description(value="description2"),
                prompt=domain.Prompt(value="prompt2"),
            ),
        ]
        self.prompt_template_usecase.prompt_template_repo.bulk_create.return_value = want

        tenant_id = tenant_domain.Id(value=1)
        pts_for_create = [
            domain.PromptTemplateForCreate(
                title=domain.Title(value="title1"),
                description=domain.Description(value="description1"),
                prompt=domain.Prompt(value="prompt1"),
            ),
            domain.PromptTemplateForCreate(
                title=domain.Title(value="title2"),
                description=domain.Description(value="description2"),
                prompt=domain.Prompt(value="prompt2"),
            ),
        ]
        got = self.prompt_template_usecase.bulk_create_prompt_templates(
            tenant_id=tenant_id,
            prompt_templates=pts_for_create,
        )

        assert got == want
        self.prompt_template_usecase.prompt_template_repo.bulk_create.assert_called_once_with(
            tenant_id=tenant_id,
            prompt_templates=pts_for_create,
        )

    def test_find_prompt_templates_by_tenant_id(self, setup):
        want = [
            domain.PromptTemplate(
                id=domain.Id(value=1),
                title=domain.Title(value="title1"),
                description=domain.Description(value="description1"),
                prompt=domain.Prompt(value="prompt1"),
            ),
            domain.PromptTemplate(
                id=domain.Id(value=2),
                title=domain.Title(value="title2"),
                description=domain.Description(value="description2"),
                prompt=domain.Prompt(value="prompt2"),
            ),
        ]

        self.prompt_template_usecase.prompt_template_repo.find_by_tenant_id.return_value = want

        tenant_id = tenant_domain.Id(value=1)
        got = self.prompt_template_usecase.find_prompt_templates_by_tenant_id(
            tenant_id=tenant_id,
        )

        assert got == want
        self.prompt_template_usecase.prompt_template_repo.find_by_tenant_id.assert_called_once_with(
            tenant_id=tenant_id,
        )

    def test_update_prompt_template(self, setup):
        tenant_id = tenant_domain.Id(value=1)
        id = domain.Id(value=1)
        prompt_template_for_update = domain.PromptTemplateForUpdate(
            title=domain.Title(value="title1_updated"),
            description=domain.Description(value="description1_updated"),
            prompt=domain.Prompt(value="prompt1_updated"),
        )

        self.prompt_template_usecase.prompt_template_repo.find_by_id_and_tenant_id.return_value = (
            domain.PromptTemplate(
                id=id,
                title=domain.Title(value="title1"),
                description=domain.Description(value="description1"),
                prompt=domain.Prompt(value="prompt1"),
            )
        )

        self.prompt_template_usecase.update_prompt_template(
            tenant_id=tenant_id,
            id=id,
            prompt_template=prompt_template_for_update,
        )

        self.prompt_template_usecase.prompt_template_repo.find_by_id_and_tenant_id.assert_called_once_with(
            id=id,
            tenant_id=tenant_id,
        )
        self.prompt_template_usecase.prompt_template_repo.update.assert_called_once_with(
            domain.PromptTemplate(
                id=id,
                title=domain.Title(value="title1_updated"),
                description=domain.Description(value="description1_updated"),
                prompt=domain.Prompt(value="prompt1_updated"),
            ),
        )

    def test_delete_prompt_templates(self, setup):
        tenant_id = tenant_domain.Id(value=1)
        ids = [domain.Id(value=1), domain.Id(value=2)]

        self.prompt_template_usecase.delete_prompt_templates(
            tenant_id=tenant_id,
            ids=ids,
        )

        self.prompt_template_usecase.prompt_template_repo.delete_by_ids_and_tenant_id.assert_called_once_with(
            tenant_id=tenant_id,
            ids=ids,
        )
