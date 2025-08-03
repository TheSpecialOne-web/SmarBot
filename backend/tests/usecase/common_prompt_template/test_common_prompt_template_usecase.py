from unittest.mock import Mock
import uuid

import pytest

from api.domain.models import (
    bot_template as bot_template_domain,
    common_prompt_template as cpt_domain,
)
from api.usecase.common_prompt_template.common_prompt_template import (
    CommonPromptTemplateUseCase,
)


class TestCommonPromptTemplateUsecase:
    @pytest.fixture
    def setup(self):
        self.common_prompt_template_repo = Mock()
        self.bot_template_repo = Mock()
        self.common_prompt_template_usecase = CommonPromptTemplateUseCase(
            self.common_prompt_template_repo, self.bot_template_repo
        )

    def test_find_common_prompt_templates_by_bot_template_id(self, setup):
        bot_template_id = bot_template_domain.Id(root=uuid.uuid4())
        want = [
            cpt_domain.CommonPromptTemplate(
                id=cpt_domain.Id(root=uuid.uuid4()),
                title=cpt_domain.Title(root="title"),
                prompt=cpt_domain.Prompt(root="prompt"),
            ),
            cpt_domain.CommonPromptTemplate(
                id=cpt_domain.Id(root=uuid.uuid4()),
                title=cpt_domain.Title(root="title2"),
                prompt=cpt_domain.Prompt(root="prompt2"),
            ),
        ]
        self.common_prompt_template_usecase.common_prompt_template_repo.find_by_bot_template_id.return_value = want
        got = self.common_prompt_template_usecase.find_common_prompt_templates_by_bot_template_id(
            bot_template_id=bot_template_id
        )
        self.common_prompt_template_usecase.common_prompt_template_repo.find_by_bot_template_id.assert_called_once_with(
            bot_template_id=bot_template_id
        )
        assert got == want

    def test_create_common_prompt_template(self, setup):
        bot_template_id = bot_template_domain.Id(root=uuid.uuid4())
        common_prompt_template_for_create = cpt_domain.CommonPromptTemplateForCreate(
            title=cpt_domain.Title(root="title"),
            prompt=cpt_domain.Prompt(root="prompt"),
        )
        want = cpt_domain.CommonPromptTemplate(
            id=common_prompt_template_for_create.id,
            title=common_prompt_template_for_create.title,
            prompt=common_prompt_template_for_create.prompt,
        )
        self.common_prompt_template_usecase.common_prompt_template_repo.create.return_value = want

        got = self.common_prompt_template_usecase.create_common_prompt_template(
            bot_template_id=bot_template_id,
            common_prompt_template=common_prompt_template_for_create,
        )

        self.common_prompt_template_usecase.common_prompt_template_repo.create.assert_called_once_with(
            bot_template_id=bot_template_id,
            common_prompt_template=common_prompt_template_for_create,
        )

        assert got == want

    def test_update_common_prompt_template(self, setup):
        bot_template_id = bot_template_domain.Id(root=uuid.uuid4())
        common_prompt_template_id = cpt_domain.Id(root=uuid.uuid4())
        common_prompt_template_for_update = cpt_domain.CommonPromptTemplateForUpdate(
            title=cpt_domain.Title(root="title"),
            prompt=cpt_domain.Prompt(root="prompt"),
        )

        common_prompt_template = cpt_domain.CommonPromptTemplate(
            id=common_prompt_template_id,
            title=common_prompt_template_for_update.title,
            prompt=common_prompt_template_for_update.prompt,
        )

        self.common_prompt_template_usecase.common_prompt_template_repo.find_by_id.return_value = (
            common_prompt_template
        )
        self.common_prompt_template_usecase.common_prompt_template_repo.update.return_value = None

        self.common_prompt_template_usecase.update_common_prompt_template(
            bot_template_id=bot_template_id,
            id=common_prompt_template_id,
            common_prompt_template=common_prompt_template_for_update,
        )

        self.common_prompt_template_usecase.common_prompt_template_repo.find_by_id.assert_called_once_with(
            bot_template_id=bot_template_id,
            id=common_prompt_template_id,
        )

        self.common_prompt_template_usecase.common_prompt_template_repo.update.assert_called_once_with(
            bot_template_id=bot_template_id, common_prompt_template=common_prompt_template
        )

    def test_delete_common_prompt_template(self, setup):
        bot_template_id = bot_template_domain.Id(root=uuid.uuid4())
        common_prompt_template_ids = [
            cpt_domain.Id(root=uuid.uuid4()),
            cpt_domain.Id(root=uuid.uuid4()),
        ]
        self.common_prompt_template_usecase.common_prompt_template_repo.delete_by_ids_and_bot_template_id.return_value = None
        self.common_prompt_template_usecase.delete_common_prompt_templates(
            bot_template_id=bot_template_id,
            ids=common_prompt_template_ids,
        )
        self.common_prompt_template_usecase.common_prompt_template_repo.delete_by_ids_and_bot_template_id.assert_called_once_with(
            bot_template_id=bot_template_id,
            ids=common_prompt_template_ids,
        )
