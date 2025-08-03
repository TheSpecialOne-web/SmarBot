from uuid import uuid4

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    bot_template as bot_template_domain,
    llm as llm_domain,
)
from api.domain.models.llm.model import ModelFamily
from api.infrastructures.postgres.bot_template import BotTemplateRepository
from api.infrastructures.postgres.models.bot_template import BotTemplate
from api.libs.exceptions import NotFound


class TestBotTemplateRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.bot_template_repo = BotTemplateRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_find_all(self, bot_templates_seed: list[bot_template_domain.BotTemplate]):
        want = bot_templates_seed
        got = self.bot_template_repo.find_all()
        assert got == want

    def test_find_by_id(self, bot_templates_seed: list[bot_template_domain.BotTemplate]):
        want = bot_templates_seed[0]
        got = self.bot_template_repo.find_by_id(want.id)
        assert got == want

    def test_find_by_id_notfound(self):
        absent_bot_template_id = bot_template_domain.Id(root=uuid4())
        with pytest.raises(NotFound):
            self.bot_template_repo.find_by_id(absent_bot_template_id)

    def test_find_public(self, bot_templates_seed: list[bot_template_domain.BotTemplate]):
        public_bot_templates = [bot_template for bot_template in bot_templates_seed if bot_template.is_public.root]
        got = self.bot_template_repo.find_public()
        assert got == public_bot_templates

    def test_create(self):
        bot_template_for_create = bot_template_domain.BotTemplateForCreate(
            name=bot_template_domain.Name(root="test-name"),
            description=bot_template_domain.Description(root="test-description"),
            approach=bot_template_domain.Approach(bot_template_domain.Approach.NEOLLM),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=llm_domain.PdfParser(llm_domain.PdfParser.PYPDF),
            enable_web_browsing=bot_template_domain.EnableWebBrowsing(root=True),
            enable_follow_up_questions=bot_template_domain.EnableFollowUpQuestions(root=True),
            response_system_prompt=bot_template_domain.ResponseSystemPrompt(root="test-response-system-prompt"),
            document_limit=bot_template_domain.DocumentLimit(root=5),
            is_public=bot_template_domain.IsPublic(root=True),
            icon_color=bot_template_domain.IconColor(root="#000000"),
        )
        want = bot_template_domain.BotTemplate(
            id=bot_template_for_create.id,
            name=bot_template_for_create.name,
            description=bot_template_for_create.description,
            approach=bot_template_for_create.approach,
            pdf_parser=bot_template_for_create.pdf_parser,
            response_generator_model_family=bot_template_for_create.response_generator_model_family,
            response_system_prompt=bot_template_for_create.response_system_prompt,
            document_limit=bot_template_domain.DocumentLimit(root=5),
            enable_web_browsing=bot_template_for_create.enable_web_browsing,
            enable_follow_up_questions=bot_template_for_create.enable_follow_up_questions,
            is_public=bot_template_for_create.is_public,
            icon_color=bot_template_for_create.icon_color,
        )
        self.bot_template_repo.create(bot_template_for_create)

        created_bot_template = self.session.execute(
            select(BotTemplate).where(BotTemplate.id == bot_template_for_create.id.root)
        ).scalar_one_or_none()
        assert created_bot_template is not None
        assert created_bot_template.id == want.id.root
        assert created_bot_template.name == want.name.root
        assert created_bot_template.description == want.description.root
        assert created_bot_template.approach == want.approach.value
        assert created_bot_template.pdf_parser == want.pdf_parser.value
        assert created_bot_template.response_generator_model_family == want.response_generator_model_family.value
        assert created_bot_template.response_system_prompt == want.response_system_prompt.root
        assert created_bot_template.enable_web_browsing == want.enable_web_browsing.root
        assert created_bot_template.enable_follow_up_questions == want.enable_follow_up_questions.root
        assert created_bot_template.is_public == want.is_public.root

    def test_update(self, bot_templates_seed: list[bot_template_domain.BotTemplate]):
        target = bot_templates_seed[0]
        bot_template_for_update = bot_template_domain.BotTemplateForUpdate(
            name=bot_template_domain.Name(root="test-name-updated"),
            description=bot_template_domain.Description(root="test-description-updated"),
            approach=bot_template_domain.Approach(bot_template_domain.Approach.NEOLLM),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            document_limit=bot_template_domain.DocumentLimit(root=5),
            pdf_parser=llm_domain.PdfParser(llm_domain.PdfParser.PYPDF),
            enable_web_browsing=bot_template_domain.EnableWebBrowsing(root=True),
            enable_follow_up_questions=bot_template_domain.EnableFollowUpQuestions(root=True),
            response_system_prompt=bot_template_domain.ResponseSystemPrompt(
                root="test-response-system-prompt-updated"
            ),
            icon_color=bot_template_domain.IconColor(root="#000000"),
            is_public=bot_template_domain.IsPublic(root=True),
        )

        target.update(bot_template_for_update)

        self.bot_template_repo.update(target)

        updated_bot_template = self.session.execute(
            select(BotTemplate).where(BotTemplate.id == target.id.root)
        ).scalar_one_or_none()
        assert updated_bot_template is not None
        assert updated_bot_template.name == bot_template_for_update.name.root
        assert updated_bot_template.description == bot_template_for_update.description.root
        assert updated_bot_template.approach == bot_template_for_update.approach.value
        assert updated_bot_template.pdf_parser == bot_template_for_update.pdf_parser.value
        assert (
            updated_bot_template.response_generator_model_family
            == bot_template_for_update.response_generator_model_family.value
        )
        assert updated_bot_template.response_system_prompt == bot_template_for_update.response_system_prompt.root
        assert updated_bot_template.enable_web_browsing == bot_template_for_update.enable_web_browsing.root
        assert (
            updated_bot_template.enable_follow_up_questions == bot_template_for_update.enable_follow_up_questions.root
        )
        assert updated_bot_template.is_public == bot_template_for_update.is_public.root

    def test_delete(self):
        bot_template_for_create = bot_template_domain.BotTemplateForCreate(
            name=bot_template_domain.Name(root="test-name"),
            description=bot_template_domain.Description(root="test-description"),
            approach=bot_template_domain.Approach(bot_template_domain.Approach.NEOLLM),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            document_limit=bot_template_domain.DocumentLimit(root=5),
            pdf_parser=llm_domain.PdfParser(llm_domain.PdfParser.PYPDF),
            enable_web_browsing=bot_template_domain.EnableWebBrowsing(root=True),
            enable_follow_up_questions=bot_template_domain.EnableFollowUpQuestions(root=True),
            response_system_prompt=bot_template_domain.ResponseSystemPrompt(root="test-response-system-prompt"),
            is_public=bot_template_domain.IsPublic(root=True),
            icon_color=bot_template_domain.IconColor(root="#000000"),
        )
        self.session.add(
            BotTemplate(
                id=bot_template_for_create.id.root,
                name=bot_template_for_create.name.root,
                description=bot_template_for_create.description.root,
                approach=bot_template_for_create.approach.value,
                pdf_parser=bot_template_for_create.pdf_parser.value,
                response_generator_model_family=bot_template_for_create.response_generator_model_family.value,
                response_system_prompt=bot_template_for_create.response_system_prompt.root,
                enable_web_browsing=bot_template_for_create.enable_web_browsing.root,
                enable_follow_up_questions=bot_template_for_create.enable_follow_up_questions.root,
                is_public=bot_template_for_create.is_public.root,
                icon_color=bot_template_for_create.icon_color.root,
            )
        )
        self.session.flush()
        self.bot_template_repo.delete(bot_template_for_create.id)
        deleted_bot_template = self.session.execute(
            select(BotTemplate).where(BotTemplate.id == bot_template_for_create.id.root)
        ).scalar_one_or_none()
        assert deleted_bot_template is None
