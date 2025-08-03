from typing import Tuple
from unittest.mock import Mock
from uuid import UUID

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    storage as storage_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.bot import (
    approach_variable as approach_variable_domain,
    prompt_template as bot_prompt_template_domain,
)
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import IndexName
from api.infrastructures.postgres.bot import BotRepository
from api.infrastructures.postgres.document_folder import DocumentFolderRepository
from api.infrastructures.postgres.models.approach_variable import ApproachVariable
from api.infrastructures.postgres.models.bot import Bot
from api.infrastructures.postgres.models.bot_prompt_template import BotPromptTemplate
from api.libs.exceptions import NotFound
from tests.conftest import BotsSeed

GroupSeed = Tuple[group_domain.Group, group_domain.Name, tenant_domain.Id]
TenantSeed = tenant_domain.Tenant
BasicAiSeed = Tuple[list[bot_domain.Bot], tenant_domain.Tenant, group_domain.Group]
BotPromptTemplateSeed = Tuple[bot_domain.Id, list[bot_prompt_template_domain.PromptTemplate]]
UserSeed = Tuple[user_domain.Id, user_domain.UserForCreate, tenant_domain.Id, str, user_domain.Id]


class TestBotRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.bot_repo = BotRepository(self.session)
        self.document_folder_repo = DocumentFolderRepository(self.session)

    def teardown_method(self):
        self.session.close()

    @pytest.fixture
    def mock_create_bot_prompt_template_id(self, monkeypatch):
        mock_create_bot_prompt_template_id = Mock(return_value=UUID("550e8400-e29b-41d4-a716-446655440002"))
        monkeypatch.setattr("api.domain.models.bot.prompt_template.id.uuid4", mock_create_bot_prompt_template_id)
        return mock_create_bot_prompt_template_id

    # テスト
    def test_create(self, bots_seed: BotsSeed):
        """新しいボットを作成するテスト"""
        new_bots, bot_infos, _, group = bots_seed

        for new_bot in new_bots:
            # bot_info = next(info for info in bot_infos if info["name"] == new_bot.name.value)
            bot_info = None
            for info in bot_infos:
                if info["name"] == new_bot.name.value:
                    bot_info = info
                    break
            if bot_info is None:
                raise ValueError("bot_info is None")
            if bot_info["enable_web_browsing"] == "true":
                enable_web_browsing = True
            else:
                enable_web_browsing = False
            assert new_bot == bot_domain.Bot(
                id=new_bot.id,
                group_id=group.id,
                name=bot_domain.Name(value=bot_info["name"]),
                description=bot_domain.Description(value=bot_info["description"]),
                created_at=new_bot.created_at,
                index_name=IndexName(root=bot_info["index_name"]),
                container_name=storage_domain.ContainerName(root=bot_info["container_name"]),
                approach=bot_info["approach"],
                pdf_parser=bot_info["pdf_parser"],
                example_questions=[bot_domain.ExampleQuestion(value=bot_info["example_question"])],
                search_method=bot_info["search_method"],
                response_generator_model_family=bot_info["response_generator_model_family"],
                approach_variables=(
                    [
                        approach_variable_domain.ApproachVariable(
                            name=approach_variable_domain.Name(value="response_system_prompt"),
                            value=approach_variable_domain.Value(value=bot_info["response_system_prompt"]),
                        )
                    ]
                    if bot_info.get("response_system_prompt")
                    else []
                ),
                enable_web_browsing=bot_domain.EnableWebBrowsing(root=enable_web_browsing),
                enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                status=bot_domain.Status.ACTIVE,
                icon_url=bot_domain.IconUrl(root=bot_info["icon_url"]),
                icon_color=bot_domain.IconColor(root=bot_info["icon_color"]),
                endpoint_id=new_bot.endpoint_id,
                max_conversation_turns=bot_domain.MaxConversationTurns(root=int(bot_info["max_conversation_turns"])),
            )

    def test_update(self, bots_seed: BotsSeed):
        """既存のボットを更新するテスト"""

        new_bots, _, _, _ = bots_seed
        new_bot = new_bots[0]

        update_bot = self.bot_repo.find_by_id(new_bot.id)
        update_bot.name = bot_domain.Name(value="UpdatedBot")
        update_bot.description = bot_domain.Description(value="UpdatedBot")

        self.bot_repo.update(update_bot)

        # 更新後のボットを取得して検証
        updated_bot = self.bot_repo.find_by_id(new_bot.id)
        assert updated_bot is not None
        assert updated_bot.name == update_bot.name
        assert updated_bot.description == update_bot.description

    def test_find_by_id(self, bots_seed: BotsSeed):
        """存在するbot.id"""
        new_bots, _, _, _ = bots_seed
        new_bot = new_bots[0]

        bot = self.bot_repo.find_by_id(new_bot.id)

        assert bot == new_bot

    def test_find_by_id_and_group_id(self, bots_seed: BotsSeed):
        """存在するbot.idとgroup.id"""
        new_bots, _, _, group = bots_seed
        new_bot = new_bots[0]

        bot = self.bot_repo.find_by_id_and_group_id(new_bot.id, group.id)

        assert bot == new_bot

    def test_find_by_id_not_found(self):
        """存在しないbot.id"""
        non_existent_bot_id = bot_domain.Id(value=9999)

        with pytest.raises(NotFound):
            self.bot_repo.find_by_id(non_existent_bot_id)

    def test_find_by_id_and_tenant_id(self, bots_seed: BotsSeed):
        """存在するbot.idとtenant.id"""
        new_bots, _, tenant, _ = bots_seed
        new_bot = new_bots[0]

        bot = self.bot_repo.find_by_id_and_tenant_id(new_bot.id, tenant.id)

        assert bot == new_bot

    def test_find_by_id_and_tenant_id_not_found(self):
        """存在しないbot.idとtenant.id"""
        non_existent_bot_id = bot_domain.Id(value=9999)
        non_existent_tenant_id = tenant_domain.Id(value=9999)

        with pytest.raises(NotFound):
            self.bot_repo.find_by_id_and_tenant_id(non_existent_bot_id, non_existent_tenant_id)

    def test_find_by_ids_and_tenant_id(self, bots_seed: BotsSeed):
        """存在するbot.idとtenant.id"""
        new_bots, _, tenant, _ = bots_seed

        bot_ids = [bot.id for bot in new_bots]
        bots = self.bot_repo.find_by_ids_and_tenant_id(bot_ids, tenant.id)

        assert len(bots) == len(new_bots)
        for bot in bots:
            for new_bot in new_bots:
                if bot.id == new_bot.id:
                    assert bot == new_bot

    def test_find_by_tenant_id(self, bots_seed: BotsSeed):
        """テナントIDがあるケース"""
        new_bots, _, tenant, _ = bots_seed

        bots = self.bot_repo.find_by_tenant_id(tenant.id, [bot_domain.Status.ACTIVE])
        assert len(bots) == len(new_bots)
        for bot in bots:
            for new_bot in new_bots:
                if bot.id == new_bot.id:
                    assert bot == new_bot

    def test_find_by_tenant_id_with_archived(self, bots_seed: BotsSeed):
        """テナントIDがあるケース"""
        _, _, tenant, _ = bots_seed

        bots = self.bot_repo.find_by_tenant_id(tenant.id, [bot_domain.Status.ARCHIVED])
        assert len(bots) == 0

    def test_find_all_by_tenant_id(self, bots_seed: BotsSeed):
        """テナントIDがあるケース"""
        new_bots, _, tenant, _ = bots_seed

        bots = self.bot_repo.find_all_by_tenant_id(tenant.id)
        assert len(bots) == len(new_bots)
        for bot in bots:
            for new_bot in new_bots:
                if bot.id == new_bot.id:
                    assert bot == new_bot

    def test_find_by_tenant_id_not_found(self):
        """テナントIDが見つからないケース"""
        non_existent_tenant_id = tenant_domain.Id(value=9999)

        bots = self.bot_repo.find_by_tenant_id(non_existent_tenant_id)
        assert bots == []

    def test_find_by_ids_and_group_id(self, bots_seed: BotsSeed, group_seed: GroupSeed):
        """特定のbot_idとtenant_idに基づいてボットを検索し、期待されるボットが取得できることを確認するテスト。"""
        new_bots, _, _, group = bots_seed
        new_bot = new_bots[0]

        # テスト用のデータをセットアップ
        bot_ids = [new_bot.id]
        group_id = group.id

        # 検索メソッドの実行
        bots = self.bot_repo.find_by_ids_and_group_id(bot_ids, group_id, [bot_domain.Status.ACTIVE])

        # 期待されるボットが取得できているか確認
        assert bots == [new_bot]

    def test_find_by_ids_and_group_id_with_archived(self, bots_seed: BotsSeed, group_seed: GroupSeed):
        """特定のbot_idとtenant_idに基づいてボットを検索し、期待されるボットが取得できることを確認するテスト。"""
        new_bots, _, _, group = bots_seed
        new_bot = new_bots[0]

        # テスト用のデータをセットアップ
        bot_ids = [new_bot.id]
        group_id = group.id

        # 検索メソッドの実行
        bots = self.bot_repo.find_by_ids_and_group_id(bot_ids, group_id, [bot_domain.Status.ARCHIVED])

        # 期待されるボットが取得できているか確認
        assert bots == []

    def test_find_by_tenant_id_and_approaches(self, bots_seed: BotsSeed):
        """
        特定のテナントIDとアプローチに基づいてボットを検索し、期待されるボットが取得できることを確認するテスト。
        """
        new_bots, _, tenant, _ = bots_seed
        new_bot = new_bots[0]

        # テスト用のデータをセットアップ
        tenant_id = tenant.id
        approaches = [new_bot.approach]  # 適切なアプローチを設定
        exclude_ids = [new_bots[1].id, new_bots[2].id, new_bots[3].id]  # 除外するIDのリスト

        # 検索メソッドの実行
        bots = self.bot_repo.find_by_tenant_id_and_approaches(
            tenant_id, approaches, exclude_ids, [bot_domain.Status.ACTIVE]
        )

        # 期待されるボットが取得できているか確認
        assert bots == [new_bot]

    def test_find_by_tenant_id_and_approaches_with_archived(self, bots_seed: BotsSeed):
        """
        特定のテナントIDとアプローチに基づいてボットを検索し、期待されるボットが取得できることを確認するテスト。
        """
        new_bots, _, tenant, _ = bots_seed
        new_bot = new_bots[0]

        # テスト用のデータをセットアップ
        tenant_id = tenant.id
        approaches = [new_bot.approach]
        exclude_ids = [new_bots[1].id, new_bots[2].id, new_bots[3].id]

        # 検索メソッドの実行
        bots = self.bot_repo.find_by_tenant_id_and_approaches(
            tenant_id, approaches, exclude_ids, [bot_domain.Status.ARCHIVED]
        )

        # 期待されるボットが取得できているか確認
        assert bots == []

    def test_find_by_group_id_and_name(self, bots_seed: BotsSeed):
        """
        特定のテナントIDと名前に基づいてボットを検索し、期待されるボットが取得できることを確認するテスト。
        """
        new_bots, bot_infos, tenant, group = bots_seed
        new_bot = new_bots[0]
        bot_name = bot_infos[0]["name"]

        # テスト用のデータをセットアップ
        name = bot_domain.Name(value=bot_name)

        # 検索メソッドの実行
        bot = self.bot_repo.find_by_group_id_and_name(group.id, name)

        # 期待されるボットが取得できているか確認
        assert bot == new_bot

    def test_find_by_group_id_and_name_not_found(self, bots_seed: BotsSeed):
        """
        特定のテナントIDと名前に基づいてボットを検索し、期待されるボットが取得できないことを確認するテスト。
        """
        _, _, _, group = bots_seed
        bot_name = "not_found"

        # テスト用のデータをセットアップ
        name = bot_domain.Name(value=bot_name)

        # 検索メソッドの実行
        with pytest.raises(NotFound):
            self.bot_repo.find_by_group_id_and_name(group.id, name)

    def test_create_approach_variable(self, bots_seed: BotsSeed):
        new_bots, _, _, _ = bots_seed
        new_bot = new_bots[0]

        bot_id = new_bot.id
        approach = approach_variable_domain.ApproachVariable(
            name=approach_variable_domain.Name(value="test_name"),
            value=approach_variable_domain.Value(value="test_value"),
        )

        # 関数を実行
        self.bot_repo._create_approach_variable(self.session, bot_id, approach)
        self.session.commit()

        # データベースに追加されたことを検証
        added_var = self.session.execute(select(ApproachVariable).filter_by(bot_id=bot_id.value)).scalars().first()
        print(added_var)
        assert added_var is not None
        assert added_var.name == approach.name.value

    def test_delete_approach_variable(self, bots_seed: BotsSeed):
        new_bots, _, _, _ = bots_seed
        new_bot = new_bots[0]

        bot_id = new_bot.id
        approach = approach_variable_domain.ApproachVariable(
            name=approach_variable_domain.Name(value="test_name2"),
            value=approach_variable_domain.Value(value="test_value2"),
        )

        # 関数を実行
        self.bot_repo._create_approach_variable(self.session, bot_id, approach)
        self.session.commit()
        self.bot_repo._delete_approach_variable(self.session, bot_id, approach.name)
        self.session.commit()

        # データベースに存在しないことを検証
        added_var = self.session.execute(select(ApproachVariable).filter_by(bot_id=bot_id.value)).scalars().first()
        assert added_var is None

    def test_delete(self, tenant_seed: TenantSeed):
        """delete関数を実行し、Botと関連エンティティが論理削除されているかを検証"""
        new_tenant = tenant_seed
        new_bot = self.bot_repo.create(
            tenant_id=new_tenant.id,
            group_id=group_domain.Id(value=1),
            bot=bot_domain.BotForCreate(
                name=bot_domain.Name(value="Test Bot"),
                description=bot_domain.Description(value="This is a test bot."),
                index_name=IndexName(root="test-index"),
                container_name=storage_domain.ContainerName(root="test-container"),
                approach=bot_domain.Approach.NEOLLM,
                pdf_parser=llm_domain.PdfParser.PYPDF,
                example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
                search_method=bot_domain.SearchMethod.BM25,
                response_generator_model_family=ModelFamily.GPT_35_TURBO,
                enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
                enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
                icon_url=bot_domain.IconUrl(
                    root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
                ),
                icon_color=bot_domain.IconColor(root="#AA68FF"),
                max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
                approach_variables=[],
            ),
        )
        bot_id = new_bot.id

        self.bot_repo.delete(bot_id)

        # Botが論理削除されたことを確認します。
        bot = self.session.execute(select(Bot).filter_by(id=bot_id.value)).scalars().first()
        assert bot is None

        # ApproachVariableが論理削除されたことを確認
        approach_variables = self.session.execute(select(ApproachVariable).filter_by(bot_id=bot_id.value)).all()
        for av in approach_variables:
            assert av.deleted_at is not None

    def test_delete_bot_not_found(self):
        """存在しないbot_idを渡すとNotFound例外が発生することをテスト"""
        invalid_bot_id = bot_domain.Id(value=9999)

        with pytest.raises(NotFound):
            self.bot_repo.delete(invalid_bot_id)

    def test_find_prompt_template_by_id_and_bot_id(
        self,
        bot_prompt_template_seed: Tuple[bot_domain.Id, list[bot_prompt_template_domain.PromptTemplate]],
    ):
        bot_id, prompt_templates = bot_prompt_template_seed

        targe_prompt_template_id = prompt_templates[0].id.root

        bot_prompt_template = (
            self.session.execute(select(BotPromptTemplate).filter_by(bot_id=bot_id.value, id=targe_prompt_template_id))
            .scalars()
            .first()
        )

        assert bot_prompt_template is not None
        assert bot_prompt_template.id == targe_prompt_template_id

    def test_find_find_prompt_templates_by_bot_id(
        self, bot_prompt_template_seed: Tuple[bot_domain.Id, list[bot_prompt_template_domain.PromptTemplate]]
    ):
        bot_id, prompt_templates = bot_prompt_template_seed

        bot_prompt_templates = (
            self.session.execute(select(BotPromptTemplate).filter_by(bot_id=bot_id.value)).scalars().all()
        )

        assert all(
            bot_prompt_template.id in [prompt_template.id.root for prompt_template in prompt_templates]
            for bot_prompt_template in bot_prompt_templates
        )

    def test_create_prompt_template(self, mock_create_bot_prompt_template_id):
        # Given
        bot_id = bot_domain.Id(value=1)

        prompt_template_for_create = bot_prompt_template_domain.PromptTemplateForCreate(
            title=bot_prompt_template_domain.Title(root="test_name"),
            description=bot_prompt_template_domain.Description(root="test_description"),
            prompt=bot_prompt_template_domain.Prompt(root="test_prompt"),
        )
        self.bot_repo.create_prompt_template(bot_id, prompt_template_for_create)

        created_prompt_template = (
            self.session.execute(
                select(BotPromptTemplate)
                .filter_by(id=prompt_template_for_create.id.root)
                .filter_by(bot_id=bot_id.value)
            )
            .scalars()
            .first()
        )
        assert created_prompt_template is not None
        assert created_prompt_template.id == prompt_template_for_create.id.root
        assert created_prompt_template.title == prompt_template_for_create.title.root
        assert created_prompt_template.description == prompt_template_for_create.description.root
        assert created_prompt_template.prompt == prompt_template_for_create.prompt.root

        # テスト後処理
        self.session.delete(created_prompt_template)
        self.session.commit()

    def test_update_prompt_template(
        self, bot_prompt_template_seed: Tuple[bot_domain.Id, list[bot_prompt_template_domain.PromptTemplate]]
    ):
        # Given
        bot_id, prompt_templates = bot_prompt_template_seed
        target_prompt_template = prompt_templates[0]

        prompt_template_for_update = bot_prompt_template_domain.PromptTemplate(
            id=target_prompt_template.id,
            title=bot_prompt_template_domain.Title(root="updated_name"),
            description=bot_prompt_template_domain.Description(root="updated_description"),
            prompt=bot_prompt_template_domain.Prompt(root="updated_prompt"),
        )
        self.bot_repo.update_prompt_template(bot_id=bot_id, prompt_template=prompt_template_for_update)

        # When
        updated_prompt_template = (
            self.session.execute(
                select(BotPromptTemplate).filter_by(id=target_prompt_template.id.root).filter_by(bot_id=bot_id.value)
            )
            .scalars()
            .first()
        )

        # Then
        assert updated_prompt_template is not None
        assert updated_prompt_template.id == target_prompt_template.id.root
        assert updated_prompt_template.title == "updated_name"
        assert updated_prompt_template.description == "updated_description"
        assert updated_prompt_template.prompt == "updated_prompt"

    def test_delete_prompt_templates(
        self, bot_prompt_template_seed: Tuple[bot_domain.Id, list[bot_prompt_template_domain.PromptTemplate]]
    ):
        # Given
        bot_id, prompt_templates = bot_prompt_template_seed
        target_prompt_template_ids = [prompt_template.id for prompt_template in prompt_templates]
        # When
        self.bot_repo.delete_prompt_templates(bot_id=bot_id, bot_prompt_template_ids=target_prompt_template_ids)

        # Then
        str_prompt_template_ids = [
            bot_prompt_template_id.root for bot_prompt_template_id in target_prompt_template_ids
        ]
        deleted_prompt_template = (
            self.session.execute(
                select(BotPromptTemplate)
                .filter_by(bot_id=bot_id.value)
                .where(BotPromptTemplate.id.in_(str_prompt_template_ids))
            )
            .scalars()
            .all()
        )
        assert len(deleted_prompt_template) == 0

    @pytest.mark.parametrize("bot_prompt_template_seed", [{"cleanup_resources": False}], indirect=True)
    def test_delete_prompt_templates_by_bot_id(self, bot_prompt_template_seed: BotPromptTemplateSeed):
        bot_id, _ = bot_prompt_template_seed

        self.bot_repo.delete_prompt_templates_by_bot_id(bot_id)

        prompt_templates = self.bot_repo.find_prompt_templates_by_bot_id(bot_id)
        assert len(prompt_templates) == 0

    @pytest.mark.parametrize("bots_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_tenant_id(self, bots_seed: BotsSeed):
        bots, _, tenant, _ = bots_seed

        for bot in bots:
            self.document_folder_repo.delete_by_bot_id(bot.id)
        self.document_folder_repo.hard_delete_by_bot_ids([bot.id for bot in bots])
        for bot in bots:
            self.bot_repo.delete(bot.id)
        self.bot_repo.hard_delete_by_tenant_id(tenant.id)

        found_bots = self.bot_repo.find_all_by_tenant_id(tenant.id, include_deleted=True)
        assert len(found_bots) == 0

    def test_find_basic_ai_by_response_generator_model_family(self, basic_ai_seed: BasicAiSeed):
        """特定のテナントIDとモデルファミリーに基づいてボットを検索し、期待されるボットが取得できることを確認するテスト。"""
        basic_ais, tenant, group = basic_ai_seed
        basic_ai = basic_ais[0]

        bot_id = basic_ai.id
        model_family = basic_ai.response_generator_model_family

        bot = self.bot_repo.find_basic_ai_by_response_generator_model_family(
            tenant.id, group.id, model_family, [bot_domain.Status.ACTIVE, bot_domain.Status.ARCHIVED]
        )

        assert bot is not None
        assert bot.id == bot_id
        assert bot.response_generator_model_family == model_family

    def test_find_basic_ai_by_image_generator_model_family(self, basic_ai_seed: BasicAiSeed):
        """特定のテナントIDとモデルファミリーに基づいてボットを検索し、期待されるボットが取得できることを確認するテスト。"""
        basic_ais, tenant, group = basic_ai_seed
        text2_image_basic_ai = basic_ais[1]

        bot_id = text2_image_basic_ai.id
        model_family = text2_image_basic_ai.image_generator_model_family
        if model_family is None:
            raise ValueError("model_family is None")

        bot = self.bot_repo.find_basic_ai_by_image_generator_model_family(
            tenant.id, group.id, model_family, [bot_domain.Status.ACTIVE, bot_domain.Status.ARCHIVED]
        )

        assert bot is not None
        assert bot.id == bot_id
        assert bot.image_generator_model_family == model_family

    def test_add_liked_bot(self, bots_seed: BotsSeed, user_seed: UserSeed):
        """お気に入りボットを追加するテスト"""
        bots, _, tenant, _ = bots_seed
        user_id, _, _, _, _ = user_seed

        bot_id = bots[0].id
        tenant_id = tenant.id

        # お気に入りのボットを追加
        self.bot_repo.add_liked_bot(
            tenant_id=tenant_id,
            bot_id=bot_id,
            user_id=user_id,
        )

        # 正常に追加されたか確認
        liked_bots = self.bot_repo.find_liked_bot_ids_by_user_id(user_id)
        assert liked_bots[0] == bot_id

    def test_remove_liked_bot(self, bots_seed: BotsSeed, user_seed: UserSeed):
        """お気に入りボットを削除するテスト"""
        bots, _, tenant, _ = bots_seed
        user_id, _, _, _, _ = user_seed

        bot_id = bots[0].id
        tenant_id = tenant.id

        # お気に入りのボットを追加
        self.bot_repo.add_liked_bot(
            tenant_id=tenant_id,
            bot_id=bot_id,
            user_id=user_id,
        )

        # お気に入りのボットを削除
        self.bot_repo.remove_liked_bot(
            bot_id=bot_id,
            user_id=user_id,
        )

        # 正常に削除されたか確認
        liked_bots = self.bot_repo.find_liked_bot_ids_by_user_id(user_id)
        assert liked_bots == []

    def test_find_by_group_id(self, bots_seed: BotsSeed):
        """特定のグループIDに基づいてボットを検索し、期待されるボットが取得できることを確認するテスト。"""
        new_bots, _, tenant, group = bots_seed

        group_id = group.id

        bots = self.bot_repo.find_by_group_id(tenant.id, group_id, [bot_domain.Status.ACTIVE])

        assert sorted(bots, key=lambda x: x.id.value) == sorted(new_bots, key=lambda x: x.id.value)

    def test_find_with_groups_by_tenant_id(self, bots_seed: BotsSeed):
        new_bots, _, tenant, group = bots_seed

        want = [
            bot_domain.BotWithGroupName(
                **bot.model_dump(),
                group_name=group.name,
            )
            for bot in new_bots
        ]

        got = self.bot_repo.find_with_groups_by_tenant_id(tenant.id, [bot_domain.Status.ACTIVE])

        assert sorted(got, key=lambda x: x.id.value) == sorted(want, key=lambda x: x.id.value)

    def test_find_with_groups_by_ids_and_tenant_id(self, bots_seed: BotsSeed):
        new_bots, _, tenant, group = bots_seed

        bot_ids = [bot.id for bot in new_bots]
        want = [
            bot_domain.BotWithGroupName(
                **bot.model_dump(),
                group_name=group.name,
            )
            for bot in new_bots
        ]

        got = self.bot_repo.find_with_groups_by_ids_and_tenant_id(bot_ids, tenant.id)

        assert sorted(got, key=lambda x: x.id.value) == sorted(want, key=lambda x: x.id.value)
