from typing import Tuple
import uuid

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    bot_template as bot_template_domain,
    common_prompt_template as cpt_domain,
)
from api.infrastructures.postgres.common_prompt_template import (
    CommonPromptTemplateRepository,
)
from api.infrastructures.postgres.models.common_prompt_template import (
    CommonPromptTemplate,
)
from api.libs.exceptions import NotFound


class TestCommonPromptTemplateRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.common_prompt_template_repo = CommonPromptTemplateRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_find_by_bot_template_id(
        self,
        common_prompt_templates_seed: Tuple[bot_template_domain.Id, list[cpt_domain.CommonPromptTemplate]],
    ):
        bot_template_id, common_prompt_templates = common_prompt_templates_seed
        common_prompt_templates_in_db = self.common_prompt_template_repo.find_by_bot_template_id(
            bot_template_id=bot_template_id
        )
        assert common_prompt_templates == common_prompt_templates_in_db

    def test_find_by_id(
        self,
        common_prompt_templates_seed: Tuple[bot_template_domain.Id, list[cpt_domain.CommonPromptTemplate]],
    ):
        bot_template_id, common_prompt_templates = common_prompt_templates_seed
        common_prompt_template = self.common_prompt_template_repo.find_by_id(
            bot_template_id=bot_template_id,
            id=common_prompt_templates[0].id,
        )
        assert common_prompt_template == common_prompt_templates[0]

    def test_find_by_id_not_found(self):
        with pytest.raises(NotFound):
            self.common_prompt_template_repo.find_by_id(
                bot_template_id=bot_template_domain.Id(root=uuid.uuid4()),
                id=cpt_domain.Id(root=uuid.uuid4()),
            )

    def test_create(self, bot_templates_seed: list[bot_template_domain.BotTemplate]):
        bot_template_id = bot_templates_seed[0].id
        common_prompt_template_for_create = cpt_domain.CommonPromptTemplateForCreate(
            title=cpt_domain.Title(root="test"),
            prompt=cpt_domain.Prompt(root="test"),
        )

        want = cpt_domain.CommonPromptTemplate(
            id=common_prompt_template_for_create.id,
            title=common_prompt_template_for_create.title,
            prompt=common_prompt_template_for_create.prompt,
        )

        self.common_prompt_template_repo.create(
            bot_template_id=bot_template_id,
            common_prompt_template=common_prompt_template_for_create,
        )

        created_common_prompt_template = self.session.execute(
            select(CommonPromptTemplate)
            .where(CommonPromptTemplate.bot_template_id == bot_template_id.root)
            .where(CommonPromptTemplate.id == want.id.root)
        ).scalar_one()
        assert created_common_prompt_template is not None
        assert created_common_prompt_template.id == want.id.root
        assert created_common_prompt_template.title == want.title.root
        assert created_common_prompt_template.prompt == want.prompt.root

    def test_update(
        self,
        common_prompt_templates_seed: Tuple[bot_template_domain.Id, list[cpt_domain.CommonPromptTemplate]],
    ):
        bot_template_id, common_prompt_templates = common_prompt_templates_seed
        target = common_prompt_templates[0]
        target.update(
            cpt_domain.CommonPromptTemplateForUpdate(
                title=cpt_domain.Title(root="updated"),
                prompt=cpt_domain.Prompt(root="updated"),
            )
        )
        self.common_prompt_template_repo.update(
            bot_template_id=bot_template_id,
            common_prompt_template=target,
        )

        updated_common_prompt_template = self.session.execute(
            select(CommonPromptTemplate)
            .where(CommonPromptTemplate.id == target.id.root)
            .where(CommonPromptTemplate.bot_template_id == bot_template_id.root)
        ).scalar_one()
        assert updated_common_prompt_template.id == target.id.root
        assert updated_common_prompt_template.title == target.title.root
        assert updated_common_prompt_template.prompt == target.prompt.root

    def test_delete_by_ids_and_bot_template_id(
        self,
        common_prompt_templates_seed: Tuple[bot_template_domain.Id, list[cpt_domain.CommonPromptTemplate]],
    ):
        bot_template_id, _ = common_prompt_templates_seed

        common_prompt_templates_for_create = [
            cpt_domain.CommonPromptTemplateForCreate(
                title=cpt_domain.Title(root="test"),
                prompt=cpt_domain.Prompt(root="test"),
            )
            for _ in range(3)
        ]
        # Create new common prompt templates for testing
        for i in range(len(common_prompt_templates_for_create)):
            new_prompt_template = CommonPromptTemplate(
                id=common_prompt_templates_for_create[i].id.root,
                bot_template_id=bot_template_id.root,
                title=common_prompt_templates_for_create[i].title.root,
                prompt=common_prompt_templates_for_create[i].prompt.root,
            )
            self.session.add(new_prompt_template)
        self.session.commit()

        # Delete common prompt templates by IDs and bot template ID
        self.common_prompt_template_repo.delete_by_ids_and_bot_template_id(
            ids=[cpt.id for cpt in common_prompt_templates_for_create],
            bot_template_id=bot_template_id,
        )

        # Check if common prompt templates are deleted
        deleted_common_prompt_templates = (
            self.session.execute(
                select(CommonPromptTemplate)
                .where(CommonPromptTemplate.bot_template_id == bot_template_id.root)
                .where(CommonPromptTemplate.id.in_([cpt.id.root for cpt in common_prompt_templates_for_create]))
            )
            .scalars()
            .all()
        )
        assert len(deleted_common_prompt_templates) == 0
