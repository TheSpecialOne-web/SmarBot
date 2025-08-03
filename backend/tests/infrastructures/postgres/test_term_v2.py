from uuid import uuid4

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    bot as bot_domain,
    term as term_domain,
)
from api.domain.models.term.term import TermForCreateV2
from api.infrastructures.postgres.models.term_v2 import TermV2
from api.infrastructures.postgres.term_v2 import TermV2Repository
from api.libs.exceptions import NotFound
from tests.conftest import BotsSeed

TermSeed = tuple[list[term_domain.TermV2], bot_domain.Id]


class TestTermRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.term_repo = TermV2Repository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_find_by_bot_id(self, term_v2_seed: TermSeed):
        """存在するbot_id"""
        new_terms, bot_id = term_v2_seed

        terms = self.term_repo.find_by_bot_id(bot_id=bot_id)

        # sort by id
        terms = sorted(terms, key=lambda x: x.id.root)
        new_terms = sorted(new_terms, key=lambda x: x.id.root)
        assert terms == new_terms

    def test_find_by_bot_id_not_found(self):
        """存在しないbot_id"""
        non_existent_bot_id = bot_domain.Id(value=9999)

        terms = self.term_repo.find_by_bot_id(bot_id=non_existent_bot_id)

        assert terms == []

    def test_find_by_bot_id_and_description(self, term_v2_seed: TermSeed):
        """存在するbot_idと同一のdescription"""
        new_terms, bot_id = term_v2_seed

        term = self.term_repo.find_by_bot_id_and_description(
            bot_id=bot_id, term_description=term_domain.DescriptionV2(root="テスト用語の説明")
        )

        assert term == new_terms[0]

    def test_find_by_bot_id_and_description_not_found(self, term_v2_seed: TermSeed):
        """存在するbot_idと異なるdescription"""
        _, bot_id = term_v2_seed
        non_existent_description = term_domain.DescriptionV2(root="non_existent_description")

        with pytest.raises(NotFound):
            self.term_repo.find_by_bot_id_and_description(bot_id=bot_id, term_description=non_existent_description)

    def test_find_by_bot_id_and_name(self, term_v2_seed: TermSeed):
        """存在するbot_idと同一のname"""
        new_terms, bot_id = term_v2_seed

        terms = self.term_repo.find_by_bot_id_and_name(bot_id=bot_id, term_name=[term_domain.NameV2(root="test")])

        assert terms[0] == new_terms[0]

    def test_find_by_bot_id_and_name_not_found(self, term_v2_seed: TermSeed):
        """存在するbot_idと異なるname"""
        _, bot_id = term_v2_seed
        non_existent_name = term_domain.NameV2(root="non_existent_name")

        result = self.term_repo.find_by_bot_id_and_name(bot_id=bot_id, term_name=[non_existent_name])

        assert result == []

    def test_find_by_bot_id_and_term_id(self, term_v2_seed: TermSeed):
        """存在するbot_idとterm_id"""
        new_terms, bot_id = term_v2_seed

        term = self.term_repo.find_by_bot_id_and_term_id(bot_id=bot_id, term_id=new_terms[0].id)

        assert term == new_terms[0]

    def test_find_by_bot_id_and_term_id_not_found(self, term_v2_seed: TermSeed):
        """存在するbot_idと異なるterm_id"""
        _, bot_id = term_v2_seed
        non_existent_term_id = term_domain.IdV2(root=uuid4())

        with pytest.raises(NotFound):
            self.term_repo.find_by_bot_id_and_term_id(bot_id=bot_id, term_id=non_existent_term_id)

    def test_create_term(
        self,
        bots_seed: BotsSeed,
    ):
        """新しい用語を作成するテスト"""
        bots, _, _, _ = bots_seed
        bot_id = bots[0].id
        new_term_for_create = TermForCreateV2(
            names=[term_domain.NameV2(root="test")],
            description=term_domain.DescriptionV2(root="test"),
        )

        got = self.term_repo.create(
            bot_id=bot_id,
            term=new_term_for_create,
        )
        assert got == term_domain.TermV2(
            id=new_term_for_create.id,
            names=new_term_for_create.names,
            description=new_term_for_create.description,
        )

        created_term = (
            self.session.execute(
                select(TermV2).where(TermV2.bot_id == bot_id.value).where(TermV2.id == new_term_for_create.id.root)
            )
            .scalars()
            .first()
        )
        assert created_term is not None
        assert created_term.id == new_term_for_create.id.root

    def test_update_term(self, term_v2_seed: TermSeed):
        """用語を更新するテスト"""
        new_terms, bot_id = term_v2_seed
        target = new_terms[0]
        term_for_update = term_domain.TermForUpdateV2(
            names=[term_domain.NameV2(root="test_updated")],
            description=term_domain.DescriptionV2(root="test_updated"),
        )

        target.update(term_for_update)

        self.term_repo.update(term=target)

        updated = self.term_repo.find_by_bot_id_and_term_id(bot_id=bot_id, term_id=target.id)

        assert updated == term_domain.TermV2(
            id=target.id,
            names=term_for_update.names,
            description=term_for_update.description,
        )

        updated_term = (
            self.session.execute(
                select(TermV2).where(TermV2.bot_id == bot_id.value).where(TermV2.id == target.id.root)
            )
            .scalars()
            .first()
        )
        assert updated_term is not None
        assert updated_term.bot_id == bot_id.value

    def test_delete_by_ids_and_bot_id(self, term_v2_seed: TermSeed):
        """特定のbot_idとidに基づいて用語を削除するテスト。"""
        new_terms, bot_id = term_v2_seed

        # テスト用のデータをセットアップ
        term_ids = [term.id for term in new_terms]

        # 検索メソッドの実行
        self.term_repo.delete_by_term_ids_and_bot_id(bot_id=bot_id, term_ids=term_ids)

        # 期待される用語が取得できているか確認
        terms = self.term_repo.find_by_bot_id(bot_id=bot_id)
        assert len(terms) == 0

    def test_delete_by_bot_id(self, term_v2_seed: TermSeed):
        _, bot_id = term_v2_seed

        self.term_repo.delete_by_bot_id(bot_id=bot_id)

        terms = self.term_repo.find_by_bot_id(bot_id=bot_id)
        assert len(terms) == 0

    def test_hard_delete_by_bot_ids(self, term_v2_seed: TermSeed):
        _, bot_id = term_v2_seed

        self.term_repo.delete_by_bot_id(bot_id=bot_id)
        self.term_repo.hard_delete_by_bot_ids([bot_id])

        terms = (
            self.session.execute(
                select(TermV2).where(TermV2.bot_id == bot_id.value).execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )
        assert len(terms) == 0
