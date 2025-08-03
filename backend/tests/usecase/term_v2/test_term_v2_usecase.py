from datetime import datetime
from unittest.mock import Mock
import uuid

import pytest

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    term as term_domain,
)
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import IndexName
from api.domain.models.storage import ContainerName
from api.libs.exceptions import Conflict, NotFound
from api.usecase.term_v2 import TermUseCase


class TestTermUseCase:
    @pytest.fixture
    def setup(self):
        self.bot_repo = Mock()
        self.term_repo = Mock()
        self.term_usecase = TermUseCase(
            bot_repo=self.bot_repo,
            term_repo=self.term_repo,
        )

    def dummy_bot(self, bot_id: bot_domain.Id):
        return bot_domain.Bot(
            id=bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=IndexName(root="test-index"),
            container_name=ContainerName(root="test-container"),
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.BM25,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=bot_domain.Status.ACTIVE,
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def test_find_terms_by_bot_id(self, setup):
        """ボットIDによる用語取得テスト"""
        bot_id = bot_domain.Id(value=1)
        dummy_terms = [
            term_domain.TermV2(
                id=term_domain.IdV2(root=uuid.uuid4()),
                names=[term_domain.NameV2(root="test"), term_domain.NameV2(root="test_array")],
                description=term_domain.DescriptionV2(root="test"),
            ),
            term_domain.TermV2(
                id=term_domain.IdV2(root=uuid.uuid4()),
                names=[term_domain.NameV2(root="test2")],
                description=term_domain.DescriptionV2(root="test2"),
            ),
        ]

        self.term_usecase.bot_repo.find_by_id.return_value = self.dummy_bot(bot_id)
        self.term_usecase.term_repo.find_by_bot_id.return_value = dummy_terms

        terms = self.term_usecase.find_terms_by_bot_id(bot_id)

        self.term_usecase.bot_repo.find_by_id.assert_called_once_with(bot_id)
        self.term_usecase.term_repo.find_by_bot_id.assert_called_once_with(bot_id=bot_id)
        assert terms == dummy_terms

    def test_create_term_success(self, setup):
        """用語が正常に作成されるかのテスト"""
        bot_id = bot_domain.Id(value=1)
        term_for_create = term_domain.TermForCreateV2(
            names=[term_domain.NameV2(root="test"), term_domain.NameV2(root="test_array")],
            description=term_domain.DescriptionV2(root="test"),
        )
        expected_term = term_domain.TermV2(
            id=term_for_create.id,
            names=term_for_create.names,
            description=term_for_create.description,
        )

        self.term_usecase.term_repo.find_by_bot_id_and_description.side_effect = NotFound("Not Found")
        self.term_usecase.term_repo.find_by_bot_id_and_name.return_value = []
        self.term_usecase.term_repo.create.return_value = expected_term

        result = self.term_usecase.create_term(bot_id, term_for_create)

        self.term_usecase.bot_repo.find_by_id.assert_called_once_with(bot_id)
        self.term_usecase.term_repo.find_by_bot_id_and_description.assert_called_once_with(
            bot_id=bot_id, term_description=term_for_create.description
        )
        self.term_usecase.term_repo.create.assert_called_once_with(bot_id=bot_id, term=term_for_create)
        assert result == expected_term

    def test_create_term_duplicate_description(self, setup):
        """同一の説明を持つ用語が既に存在する場合のテスト"""
        bot_id = bot_domain.Id(value=1)
        term_for_create = term_domain.TermForCreateV2(
            names=[term_domain.NameV2(root="test"), term_domain.NameV2(root="test_array")],
            description=term_domain.DescriptionV2(root="test"),
        )

        self.term_usecase.term_repo.find_by_bot_id_and_description.return_value = Mock()

        with pytest.raises(Conflict, match="同一の説明を持つ用語が既に存在します"):
            self.term_usecase.create_term(bot_id, term_for_create)

        self.term_usecase.term_repo.find_by_bot_id_and_description.assert_called_once_with(
            bot_id=bot_id, term_description=term_for_create.description
        )

    def test_create_term_duplicate_name(self, setup):
        """同一の名前を持つ用語が既に存在する場合のテスト"""
        bot_id = bot_domain.Id(value=1)
        term_for_create = term_domain.TermForCreateV2(
            names=[term_domain.NameV2(root="test"), term_domain.NameV2(root="test_array")],
            description=term_domain.DescriptionV2(root="test"),
        )

        self.term_usecase.term_repo.find_by_bot_id_and_description.side_effect = NotFound("Not Found")
        self.term_usecase.term_repo.find_by_bot_id_and_name.return_value = [Mock()]

        with pytest.raises(Conflict, match="同一の用語が既に存在します"):
            self.term_usecase.create_term(bot_id, term_for_create)

        self.term_usecase.term_repo.find_by_bot_id_and_description.assert_called_once_with(
            bot_id=bot_id, term_description=term_for_create.description
        )
        self.term_usecase.term_repo.find_by_bot_id_and_name.assert_called_once_with(
            bot_id=bot_id, term_name=term_for_create.names
        )

    def test_update_term(self, setup):
        """用語の更新テスト"""
        bot_id = bot_domain.Id(value=1)
        term_id = term_domain.IdV2(root=uuid.uuid4())
        term_for_update = term_domain.TermForUpdateV2(
            names=[term_domain.NameV2(root="test"), term_domain.NameV2(root="test_array")],
            description=term_domain.DescriptionV2(root="test"),
        )

        term = term_domain.TermV2(
            id=term_id,
            names=term_for_update.names,
            description=term_for_update.description,
        )

        self.term_usecase.term_repo.find_by_bot_id_and_term_id.return_value = term
        self.term_usecase.term_repo.find_by_bot_id_and_description.return_value = term
        self.term_usecase.term_repo.find_by_bot_id_and_name.return_value = []
        self.term_usecase.term_repo.update.return_value = None
        self.term_usecase.update_term(bot_id, term_id, term_for_update)
        self.term_usecase.term_repo.find_by_bot_id_and_term_id.assert_called_once_with(bot_id=bot_id, term_id=term_id)
        self.term_usecase.term_repo.update.assert_called_once_with(term=term)
        self.term_usecase.term_repo.find_by_bot_id_and_description.assert_called_once_with(
            bot_id=bot_id, term_description=term_for_update.description
        )

    def test_update_term_duplicate_name(self, setup):
        """同一の名前を持つ用語が既に存在する場合のテスト"""
        bot_id = bot_domain.Id(value=1)
        term_id = term_domain.IdV2(root=uuid.uuid4())
        term_for_update = term_domain.TermForUpdateV2(
            names=[term_domain.NameV2(root="test"), term_domain.NameV2(root="test_array")],
            description=term_domain.DescriptionV2(root="test"),
        )

        term = term_domain.TermV2(
            id=term_id,
            names=term_for_update.names,
            description=term_for_update.description,
        )

        self.term_usecase.term_repo.find_by_bot_id_and_description.side_effect = NotFound("Not Found")
        self.term_usecase.term_repo.find_by_bot_id_and_name.return_value = [Mock()]
        self.term_usecase.term_repo.find_by_bot_id_and_term_id.return_value = term

        with pytest.raises(Conflict, match="同一の用語が既に存在します"):
            self.term_usecase.update_term(bot_id, term_id, term_for_update)

        self.term_usecase.term_repo.find_by_bot_id_and_name.assert_called_once_with(
            bot_id=bot_id, term_name=term_for_update.names
        )

    def test_delete_terms_by_ids_and_bot_id(self, setup):
        """ボットIDと用語IDによる用語削除テスト"""
        bot_id = bot_domain.Id(value=1)
        term_ids = [term_domain.IdV2(root=uuid.uuid4())]

        self.term_usecase.bot_repo.find_by_id.return_value = self.dummy_bot(bot_id)
        self.term_usecase.term_repo.delete_by_term_ids_and_bot_id.return_value = None

        self.term_usecase.delete_terms_by_term_ids_and_bot_id(bot_id, term_ids)

        self.term_usecase.bot_repo.find_by_id.assert_called_once_with(bot_id)
        self.term_usecase.term_repo.delete_by_term_ids_and_bot_id.assert_called_once_with(
            bot_id=bot_id, term_ids=term_ids
        )
