import datetime
import uuid

import pytest

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
)
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search.index_name import IndexName
from api.domain.models.storage import ContainerName
from api.domain.models.tenant.alias import Alias
from api.domain.models.text_2_image_model.model import Text2ImageModelFamily
from api.libs.exceptions import BadRequest


def dummy_bot(
    bot_id: bot_domain.Id,
    approach: bot_domain.Approach,
    index_name: IndexName | None,
    pdf_parser: llm_domain.PdfParser = llm_domain.PdfParser.PYPDF,
    image_generator_model_family: Text2ImageModelFamily | None = None,
    search_method: bot_domain.SearchMethod | None = None,
    enable_web_browsing: bot_domain.EnableWebBrowsing | None = None,
    response_generator_model_family: ModelFamily = ModelFamily.GPT_35_TURBO,
):
    return bot_domain.Bot(
        id=bot_id,
        group_id=group_domain.Id(value=1),
        name=bot_domain.Name(value="Test Bot"),
        description=bot_domain.Description(value="This is a test bot."),
        created_at=bot_domain.CreatedAt(root=datetime.datetime.now(datetime.timezone.utc)),
        index_name=index_name,
        container_name=ContainerName(root="test-container"),
        approach=approach,
        pdf_parser=pdf_parser,
        example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
        search_method=search_method,
        response_generator_model_family=response_generator_model_family,
        image_generator_model_family=image_generator_model_family,
        approach_variables=[],
        enable_web_browsing=enable_web_browsing
        if enable_web_browsing is not None
        else bot_domain.EnableWebBrowsing(root=False),
        enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
        status=bot_domain.Status.ACTIVE,
        icon_url=bot_domain.IconUrl(
            root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
        ),
        icon_color=bot_domain.IconColor(root="#AA68FF"),
        endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
        max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
    )


class TestBot:
    def test_validate_allowed_model_families(self):
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            search_method=None,
            index_name=None,
        )
        allowed_model_families: list[ModelFamily | Text2ImageModelFamily] = [
            ModelFamily.GPT_35_TURBO,
            ModelFamily.GPT_4,
        ]

        assert bot.validate_allowed_model_families(allowed_model_families) is None

        bot = dummy_bot(
            bot_id=bot_domain.Id(value=3),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            search_method=None,
            index_name=None,
            response_generator_model_family=ModelFamily.GPT_4,
        )
        allowed_model_families: list[ModelFamily | Text2ImageModelFamily] = [
            ModelFamily.GPT_35_TURBO,
        ]
        with pytest.raises(BadRequest):
            bot.validate_allowed_model_families(allowed_model_families)

    def test_invalid_search_method(self):
        ursa_bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.URSA,
            search_method=bot_domain.SearchMethod.URSA_SEMANTIC,
            index_name=IndexName(root="test-index"),
        )
        with pytest.raises(BadRequest):
            ursa_bot.update(
                bot_domain.BotForUpdate(
                    name=ursa_bot.name,
                    description=ursa_bot.description,
                    index_name=ursa_bot.index_name,
                    container_name=ursa_bot.container_name,
                    approach=ursa_bot.approach,
                    pdf_parser=ursa_bot.pdf_parser,
                    example_questions=ursa_bot.example_questions,
                    search_method=bot_domain.SearchMethod.BM25,  # 変更されたsearch_method
                    response_generator_model_family=ursa_bot.response_generator_model_family,
                    image_generator_model_family=ursa_bot.image_generator_model_family,
                    approach_variables=ursa_bot.approach_variables,
                    enable_web_browsing=ursa_bot.enable_web_browsing,
                    enable_follow_up_questions=ursa_bot.enable_follow_up_questions,
                    icon_url=ursa_bot.icon_url,
                    icon_color=ursa_bot.icon_color,
                    max_conversation_turns=ursa_bot.max_conversation_turns,
                )
            )

    def test_archive_bot(self):
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            index_name=None,
        )
        bot.archive()
        assert bot.status == bot_domain.Status.ARCHIVED

    def test_fail_archive_bot(self):
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            index_name=None,
        )
        bot.archive()
        with pytest.raises(BadRequest):
            bot.archive()

    def test_restore_bot(self):
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            index_name=None,
        )
        bot.archive()
        bot.restore()
        assert bot.status == bot_domain.Status.ACTIVE

    def test_fail_restore_bot(self):
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            index_name=None,
        )
        with pytest.raises(BadRequest):
            bot.restore()

    def test_delete_basic_ai(self):
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.CHAT_GPT_DEFAULT,
            search_method=None,
            index_name=None,
        )
        bot.delete_basic_ai()
        assert bot.status == bot_domain.Status.BASIC_AI_DELETED

    def test_fail_delete_basic_ai(self):
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.SEMANTIC_HYBRID,
            index_name=None,
        )
        with pytest.raises(BadRequest):
            bot.delete_basic_ai()


class TestBotProps:
    def test_invalid_search_method(self):
        # neollmのボットの検索メソッドが不正
        for search_method in [
            bot_domain.SearchMethod.URSA,
            bot_domain.SearchMethod.URSA_SEMANTIC,
        ]:
            with pytest.raises(BadRequest):
                dummy_bot(
                    bot_id=bot_domain.Id(value=1),
                    approach=bot_domain.Approach.NEOLLM,
                    search_method=search_method,
                    index_name=None,
                )

        # 画像生成ボットのimage_generator_model_familyがNoneの場合にエラーが発生することを確認
        with pytest.raises(BadRequest):
            dummy_bot(
                bot_id=bot_domain.Id(value=1),
                approach=bot_domain.Approach.TEXT_2_IMAGE,
                image_generator_model_family=None,
                index_name=None,
            )

        # 画像生成ボットのenable_web_browsingがTrueの場合にエラーが発生することを確認
        with pytest.raises(BadRequest):
            dummy_bot(
                bot_id=bot_domain.Id(value=1),
                approach=bot_domain.Approach.TEXT_2_IMAGE,
                enable_web_browsing=bot_domain.EnableWebBrowsing(root=True),
                index_name=None,
            )

        # ursaのindex_nameがNoneの場合にエラーが発生することを確認
        with pytest.raises(BadRequest):
            dummy_bot(
                bot_id=bot_domain.Id(value=1),
                approach=bot_domain.Approach.URSA,
                index_name=None,
                search_method=bot_domain.SearchMethod.URSA_SEMANTIC,
            )

        # ursaのボットの検索メソッドが不正
        for search_method in [
            bot_domain.SearchMethod.BM25,
            bot_domain.SearchMethod.VECTOR,
            bot_domain.SearchMethod.HYBRID,
            bot_domain.SearchMethod.SEMANTIC_HYBRID,
        ]:
            with pytest.raises(BadRequest):
                dummy_bot(
                    bot_id=bot_domain.Id(value=1),
                    approach=bot_domain.Approach.URSA,
                    index_name=IndexName(root="test-index"),
                    search_method=search_method,
                )


class TestBotForCreate:
    def dummy_bot_for_create(
        self,
        pdf_parser: llm_domain.PdfParser = llm_domain.PdfParser.PYPDF,
        search_method: bot_domain.SearchMethod = bot_domain.SearchMethod.BM25,
        approach: bot_domain.Approach = bot_domain.Approach.NEOLLM,
        response_generator_model_family: ModelFamily = ModelFamily.GPT_35_TURBO,
    ):
        return bot_domain.BotForCreate(
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
            approach=approach,
            pdf_parser=pdf_parser,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=search_method,
            response_generator_model_family=response_generator_model_family,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            approach_variables=[],
        )

    def test_valid_bot_for_create(self):
        self.dummy_bot_for_create()

    def test_invalid_model_family(self):
        legacy_model_families = [model_family for model_family in ModelFamily if model_family.is_legacy()]
        for legacy_mf in legacy_model_families:
            with pytest.raises(BadRequest):
                self.dummy_bot_for_create(
                    response_generator_model_family=legacy_mf,
                )

    def test_invalid_create_custom_gpt(self):
        with pytest.raises(BadRequest):
            bot_domain.BotForCreate.create_custom_gpt(
                tenant_alias=Alias(root="test-tenant"),
                name=bot_domain.Name(value="Test Bot"),
                description=bot_domain.Description(value="This is a test bot."),
                example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
                response_generator_model_family=ModelFamily.GPT_35_TURBO,
                response_system_prompt=bot_domain.ResponseSystemPrompt(root="This is a test bot."),
                document_limit=bot_domain.DocumentLimit(root=1),
                pdf_parser=llm_domain.PdfParser.AI_VISION,
                enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
                icon_color=bot_domain.IconColor(root="#AA68FF"),
                max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            )

    def test_invalid_search_method_create_neollm(self):
        # neollmのボットの検索メソッドが不正
        for search_method in [
            bot_domain.SearchMethod.HYBRID,
            bot_domain.SearchMethod.VECTOR,
            bot_domain.SearchMethod.URSA,
            bot_domain.SearchMethod.URSA_SEMANTIC,
        ]:
            with pytest.raises(BadRequest):
                bot_domain.BotForCreate.create_neollm(
                    tenant_alias=Alias(root="test-tenant"),
                    name=bot_domain.Name(value="Test Bot"),
                    description=bot_domain.Description(value="This is a test bot."),
                    example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
                    search_method=search_method,
                    response_generator_model_family=ModelFamily.GPT_35_TURBO,
                    response_system_prompt=bot_domain.ResponseSystemPrompt(root="This is a test bot."),
                    document_limit=bot_domain.DocumentLimit(root=1),
                    pdf_parser=llm_domain.PdfParser.PYPDF,
                    enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
                    enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                    icon_color=bot_domain.IconColor(root="#AA68FF"),
                    max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
                )


class TestBotForUpdate:
    def dummy_bot_for_update(self):
        return bot_domain.BotForUpdate(
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.BM25,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=llm_domain.PdfParser.AI_VISION,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.NEOLLM,
            approach_variables=[],
        )

    def test_valid_bot_for_update(self):
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.BM25,
            index_name=None,
        )
        bot.update(self.dummy_bot_for_update())

    def test_invalid_approach(self):
        # 更新不可なアプローチの場合はエラーが発生することを確認
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.BM25,
            index_name=None,
        )
        for approach in [
            bot_domain.Approach.CHAT_GPT_DEFAULT,
            bot_domain.Approach.TEXT_2_IMAGE,
            bot_domain.Approach.URSA,
        ]:
            with pytest.raises(BadRequest):
                bot_domain.BotForUpdate.by_user(
                    current=bot,
                    name=bot_domain.Name(value="Test Bot"),
                    description=bot_domain.Description(value="This is a test bot."),
                    example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
                    search_method=bot_domain.SearchMethod.BM25,
                    approach=approach,
                    response_generator_model_family=ModelFamily.GPT_35_TURBO,
                    response_system_prompt=bot_domain.ResponseSystemPrompt(root="This is a test bot."),
                    document_limit=bot_domain.DocumentLimit(root=1),
                    pdf_parser=llm_domain.PdfParser.PYPDF,
                    enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
                    enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                    icon_color=bot_domain.IconColor(root="#AA68FF"),
                    max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
                )

    def test_invalid_pdf_parser(self):
        bot = dummy_bot(
            bot_id=bot_domain.Id(value=1),
            pdf_parser=llm_domain.PdfParser.AI_VISION,
            approach=bot_domain.Approach.NEOLLM,
            search_method=bot_domain.SearchMethod.BM25,
            index_name=None,
        )

        with pytest.raises(BadRequest):
            bot_domain.BotForUpdate.by_user(
                current=bot,
                name=bot_domain.Name(value="Test Bot"),
                description=bot_domain.Description(value="This is a test bot."),
                example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
                search_method=bot_domain.SearchMethod.BM25,
                approach=bot_domain.Approach.NEOLLM,
                response_generator_model_family=ModelFamily.GPT_35_TURBO,
                response_system_prompt=bot_domain.ResponseSystemPrompt(root="This is a test bot."),
                document_limit=bot_domain.DocumentLimit(root=1),
                pdf_parser=llm_domain.PdfParser.PYPDF,
                enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
                enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                icon_color=bot_domain.IconColor(root="#AA68FF"),
                max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            )
