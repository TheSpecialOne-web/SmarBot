from typing import Tuple

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    prompt_template as domain,
    tenant as tenant_domain,
)
from api.infrastructures.postgres.prompt_template import (
    PromptTemplate as PromptTemplateModel,
    PromptTemplateRepository,
)

TenantSeed = tenant_domain.Tenant
PromptTemplatesSeed = Tuple[tenant_domain.Id, list[domain.PromptTemplate]]


class TestPromptTemplateRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.prompt_template_repo = PromptTemplateRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_bulk_create(self, tenant_seed: TenantSeed):
        tenant = tenant_seed
        prompt_templates_for_create = [
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
        got = self.prompt_template_repo.bulk_create(
            tenant_id=tenant.id,
            prompt_templates=prompt_templates_for_create,
        )
        assert [pt.model_dump(exclude={"id"}) for pt in got] == [pt.model_dump() for pt in prompt_templates_for_create]

    def test_find_by_tenant_id(self, prompt_templates_seed: PromptTemplatesSeed):
        tenant_id, prompt_templates = prompt_templates_seed
        got = self.prompt_template_repo.find_by_tenant_id(
            tenant_id=tenant_id,
        )
        assert got == prompt_templates

    def test_find_by_id_and_tenant_id(self, prompt_templates_seed: PromptTemplatesSeed):
        tenant_id, prompt_templates = prompt_templates_seed
        got = self.prompt_template_repo.find_by_id_and_tenant_id(
            id=prompt_templates[0].id,
            tenant_id=tenant_id,
        )
        assert got == prompt_templates[0]

    def test_update(self, prompt_templates_seed: PromptTemplatesSeed):
        tenant_id, prompt_templates = prompt_templates_seed
        prompt_template = prompt_templates[0]
        prompt_template.update(
            domain.PromptTemplateForUpdate(
                title=domain.Title(value="title1_updated"),
                description=domain.Description(value="description1_updated"),
                prompt=domain.Prompt(value="prompt1_updated"),
            )
        )
        self.prompt_template_repo.update(
            prompt_template=prompt_template,
        )
        got = self.prompt_template_repo.find_by_id_and_tenant_id(
            id=prompt_template.id,
            tenant_id=tenant_id,
        )
        assert got == prompt_template

    def test_delete_by_ids_and_tenant_id(self):
        tenant_id = tenant_domain.Id(value=1)
        prompt_templates_for_create = [
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
        prompt_templates = self.prompt_template_repo.bulk_create(
            tenant_id=tenant_id,
            prompt_templates=prompt_templates_for_create,
        )
        ids = [pt.id for pt in prompt_templates]
        self.prompt_template_repo.delete_by_ids_and_tenant_id(
            ids=ids,
            tenant_id=tenant_id,
        )
        got = self.prompt_template_repo.find_by_tenant_id(
            tenant_id=tenant_id,
        )
        assert got == []

    @pytest.mark.parametrize("prompt_templates_seed", [{"cleanup_resources": False}], indirect=True)
    def test_delete_by_tenant_id(self, prompt_templates_seed: PromptTemplatesSeed):
        tenant_id, _ = prompt_templates_seed

        self.prompt_template_repo.delete_by_tenant_id(tenant_id)

        prompt_templates = self.prompt_template_repo.find_by_tenant_id(tenant_id)
        assert len(prompt_templates) == 0

    @pytest.mark.parametrize("prompt_templates_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_tenant_id(self, prompt_templates_seed: PromptTemplatesSeed):
        tenant_id, _ = prompt_templates_seed

        self.prompt_template_repo.delete_by_tenant_id(tenant_id)
        self.prompt_template_repo.hard_delete_by_tenant_id(tenant_id)

        prompt_templates = (
            self.session.execute(
                select(PromptTemplateModel)
                .where(PromptTemplateModel.tenant_id == tenant_id.value)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )
        assert len(prompt_templates) == 0
