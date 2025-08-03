from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from api.domain.models.bot_template import (
    Approach,
    BotTemplate,
    BotTemplateForCreate,
    BotTemplateForUpdate,
    Description,
    DocumentLimit,
    EnableFollowUpQuestions,
    EnableWebBrowsing,
    IconColor,
    Id,
    IsPublic,
    Name,
    ResponseSystemPrompt,
)
from api.domain.models.bot_template.icon_url import IconUrl
from api.domain.models.llm.model import ModelFamily
from api.domain.models.llm.pdf_parser import PdfParser
from api.usecase.bot_template.bot_template import (
    BotTemplateUseCase,
    UploadBotTemplateIconInput,
)


class TestBotTemplateUseCase:
    @pytest.fixture
    def setup(self):
        self.bot_template_repo = Mock()
        self.blob_storage_service = Mock()
        self.bot_template_usecase = BotTemplateUseCase(self.bot_template_repo, self.blob_storage_service)

    def test_find_all_bot_templates(self, setup):
        """bot テンプレート取得テスト"""
        want = [
            BotTemplate(
                id=Id(root=uuid4()),
                name=Name(root="test-name"),
                description=Description(root="test-description"),
                approach=Approach("neollm"),
                response_generator_model_family=ModelFamily.GPT_35_TURBO,
                pdf_parser=PdfParser("pypdf"),
                enable_web_browsing=EnableWebBrowsing(root=True),
                enable_follow_up_questions=EnableFollowUpQuestions(root=True),
                response_system_prompt=ResponseSystemPrompt(root="test-response-system-prompt"),
                document_limit=DocumentLimit(root=5),
                is_public=IsPublic(root=False),
                icon_color=IconColor(root="#000000"),
            ),
            BotTemplate(
                id=Id(root=uuid4()),
                name=Name(root="test-name"),
                description=Description(root="test-description"),
                approach=Approach("neollm"),
                response_generator_model_family=ModelFamily.GPT_35_TURBO,
                pdf_parser=PdfParser("pypdf"),
                enable_web_browsing=EnableWebBrowsing(root=True),
                enable_follow_up_questions=EnableFollowUpQuestions(root=True),
                response_system_prompt=ResponseSystemPrompt(root="test-response-system-prompt"),
                document_limit=DocumentLimit(root=5),
                is_public=IsPublic(root=True),
                icon_color=IconColor(root="#000000"),
            ),
        ]

        self.bot_template_usecase.bot_template_repo.find_all.return_value = want
        got = self.bot_template_usecase.find_all_bot_templates()
        self.bot_template_usecase.bot_template_repo.find_all.assert_called_once()
        assert got == want

    def test_find_bot_template_by_id(self, setup):
        """bot テンプレート取得テスト"""
        want = BotTemplate(
            id=Id(root=uuid4()),
            name=Name(root="test-name"),
            description=Description(root="test-description"),
            approach=Approach("neollm"),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=PdfParser("pypdf"),
            enable_web_browsing=EnableWebBrowsing(root=True),
            enable_follow_up_questions=EnableFollowUpQuestions(root=True),
            response_system_prompt=ResponseSystemPrompt(root="test-response-system-prompt"),
            document_limit=DocumentLimit(root=5),
            is_public=IsPublic(root=False),
            icon_color=IconColor(root="#000000"),
        )
        self.bot_template_usecase.bot_template_repo.find_by_id.return_value = want
        got = self.bot_template_usecase.find_bot_template_by_id(id=want.id)
        self.bot_template_usecase.bot_template_repo.find_by_id.assert_called_once_with(id=want.id)
        assert got == want

    def test_find_public_bot_templates(self, setup):
        """bot テンプレート取得テスト"""
        want = [
            BotTemplate(
                id=Id(root=uuid4()),
                name=Name(root="test-name"),
                description=Description(root="test-description"),
                approach=Approach("neollm"),
                response_generator_model_family=ModelFamily.GPT_35_TURBO,
                pdf_parser=PdfParser("pypdf"),
                enable_web_browsing=EnableWebBrowsing(root=True),
                enable_follow_up_questions=EnableFollowUpQuestions(root=True),
                response_system_prompt=ResponseSystemPrompt(root="test-response-system-prompt"),
                document_limit=DocumentLimit(root=5),
                is_public=IsPublic(root=True),
                icon_color=IconColor(root="#000000"),
            ),
        ]
        self.bot_template_usecase.bot_template_repo.find_public.return_value = want
        got = self.bot_template_usecase.find_public_bot_templates()
        self.bot_template_usecase.bot_template_repo.find_public.assert_called_once()
        assert got == want

    def test_find_public_bot_templates_empty(self, setup):
        """bot テンプレート取得テスト"""
        self.bot_template_usecase.bot_template_repo.find_public.return_value = []
        got = self.bot_template_usecase.find_public_bot_templates()
        self.bot_template_usecase.bot_template_repo.find_public.assert_called_once()
        assert got == []

    def test_create_bot_template(self, setup):
        """bot テンプレート作成テスト"""
        bot_template_for_create = BotTemplateForCreate(
            name=Name(root="test-name"),
            description=Description(root="test-description"),
            approach=Approach("neollm"),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=PdfParser("pypdf"),
            enable_web_browsing=EnableWebBrowsing(root=True),
            enable_follow_up_questions=EnableFollowUpQuestions(root=True),
            response_system_prompt=ResponseSystemPrompt(root="test-response-system-prompt"),
            document_limit=DocumentLimit(root=5),
            is_public=IsPublic(root=False),
            icon_color=IconColor(root="#000000"),
        )
        want = BotTemplate(
            id=bot_template_for_create.id,
            name=bot_template_for_create.name,
            description=bot_template_for_create.description,
            approach=bot_template_for_create.approach,
            response_generator_model_family=bot_template_for_create.response_generator_model_family,
            pdf_parser=bot_template_for_create.pdf_parser,
            enable_web_browsing=bot_template_for_create.enable_web_browsing,
            enable_follow_up_questions=bot_template_for_create.enable_follow_up_questions,
            response_system_prompt=bot_template_for_create.response_system_prompt,
            document_limit=DocumentLimit(root=5),
            is_public=bot_template_for_create.is_public,
            icon_color=bot_template_for_create.icon_color,
        )
        self.bot_template_usecase.bot_template_repo.create.return_value = want
        got = self.bot_template_usecase.create_bot_template(bot_template=bot_template_for_create)

        self.bot_template_usecase.bot_template_repo.create.assert_called_once_with(
            bot_template=bot_template_for_create
        )
        assert want == got

    def test_update_bot_template(self, setup):
        """bot テンプレート更新テスト"""

        bot_template_id = Id(root=uuid4())
        bot_template_for_update = BotTemplateForUpdate(
            name=Name(root="test-name"),
            description=Description(root="test-description"),
            approach=Approach("neollm"),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=PdfParser("pypdf"),
            enable_web_browsing=EnableWebBrowsing(root=True),
            enable_follow_up_questions=EnableFollowUpQuestions(root=True),
            response_system_prompt=ResponseSystemPrompt(root="test-response-system-prompt"),
            document_limit=DocumentLimit(root=5),
            is_public=IsPublic(root=False),
            icon_color=IconColor(root="#000000"),
        )

        bot_template = BotTemplate(
            id=bot_template_id,
            name=bot_template_for_update.name,
            description=bot_template_for_update.description,
            approach=bot_template_for_update.approach,
            response_generator_model_family=bot_template_for_update.response_generator_model_family,
            pdf_parser=bot_template_for_update.pdf_parser,
            enable_web_browsing=bot_template_for_update.enable_web_browsing,
            enable_follow_up_questions=bot_template_for_update.enable_follow_up_questions,
            response_system_prompt=bot_template_for_update.response_system_prompt,
            document_limit=DocumentLimit(root=5),
            is_public=bot_template_for_update.is_public,
            icon_color=bot_template_for_update.icon_color,
        )

        self.bot_template_usecase.bot_template_repo.find_by_id.return_value = bot_template
        self.bot_template_usecase.bot_template_repo.update.return_value = None
        self.bot_template_usecase.update_bot_template(id=bot_template_id, bot_template=bot_template_for_update)
        self.bot_template_usecase.bot_template_repo.find_by_id.assert_called_once_with(id=bot_template_id)
        self.bot_template_usecase.bot_template_repo.update.assert_called_once_with(bot_template=bot_template)

    def test_delete_bot_template(self, setup):
        """bot テンプレート削除テスト"""
        bot_template = BotTemplate(
            id=Id(root=uuid4()),
            name=Name(root="test-name"),
            description=Description(root="test-description"),
            approach=Approach("neollm"),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=PdfParser("pypdf"),
            enable_web_browsing=EnableWebBrowsing(root=True),
            enable_follow_up_questions=EnableFollowUpQuestions(root=True),
            response_system_prompt=ResponseSystemPrompt(root="test-response-system-prompt"),
            document_limit=DocumentLimit(root=5),
            is_public=IsPublic(root=False),
            icon_color=IconColor(root="#000000"),
        )
        self.bot_template_usecase.delete_bot_template(id=bot_template.id)
        self.bot_template_usecase.bot_template_repo.delete.assert_called_once_with(id=bot_template.id)

    def test_upload_bot_template_icon(self, setup):
        """bot テンプレート iconのアップロード"""
        bot_template_id = Id(root=uuid4())
        input = UploadBotTemplateIconInput(file=b"test-data", extension="png")
        bot_template = BotTemplate(
            id=bot_template_id,
            name=Name(root="test-name"),
            description=Description(root="test-description"),
            approach=Approach("neollm"),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=PdfParser("pypdf"),
            enable_web_browsing=EnableWebBrowsing(root=True),
            enable_follow_up_questions=EnableFollowUpQuestions(root=True),
            response_system_prompt=ResponseSystemPrompt(root="test-response-system-prompt"),
            document_limit=DocumentLimit(root=5),
            is_public=IsPublic(root=False),
            icon_color=IconColor(root="#000000"),
        )

        self.blob_storage_service.upload_bot_template_icon.return_value = "test-icon-url"
        mock_uuid = uuid4()
        with patch("uuid.uuid4", return_value=mock_uuid):
            filepath = f"bot-templates/{bot_template_id.root}/icons/{mock_uuid}.{input.extension}"
            self.bot_template_usecase.bot_template_repo.find_by_id.return_value = bot_template
            bot_template.update_icon_url(IconUrl(root="test-icon-url"))
            self.bot_template_usecase.upload_bot_template_icon(bot_template_id, input)
        self.bot_template_usecase.blob_storage_service.upload_bot_template_icon.assert_called_once_with(
            filepath,
            input.file,
        )
        self.bot_template_usecase.bot_template_repo.update.assert_called_once_with(bot_template)

    def test_delete_bot_template_icon(self, setup):
        """bot テンプレート iconの削除"""
        bot_template_id = Id(root=uuid4())
        icon_url = IconUrl(root="test-icon-url")
        bot_template_to_icon_delete = BotTemplate(
            id=bot_template_id,
            name=Name(root="test-name"),
            description=Description(root="test-description"),
            approach=Approach("neollm"),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=PdfParser("pypdf"),
            enable_web_browsing=EnableWebBrowsing(root=True),
            enable_follow_up_questions=EnableFollowUpQuestions(root=True),
            response_system_prompt=ResponseSystemPrompt(root="test-response-system-prompt"),
            document_limit=DocumentLimit(root=5),
            is_public=IsPublic(root=False),
            icon_url=icon_url,
            icon_color=IconColor(root="#000000"),
        )
        self.bot_template_usecase.bot_template_repo.find_by_id.return_value = bot_template_to_icon_delete
        self.bot_template_usecase.delete_bot_template_icon(
            bot_template_id,
        )
        bot_template_to_icon_delete.update_icon_url(None)
        self.bot_template_usecase.blob_storage_service.delete_bot_template_icon.assert_called_once_with(
            bot_template_id, icon_url
        )
        self.bot_template_usecase.bot_template_repo.update.assert_called_once_with(bot_template_to_icon_delete)
