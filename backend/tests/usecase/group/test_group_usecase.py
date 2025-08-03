from datetime import datetime
from unittest.mock import Mock
from uuid import UUID

import pytest

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.storage.container_name import ContainerName
from api.libs.exceptions import BadRequest
from api.usecase.group import GroupUseCase


class TestGroupUseCase:
    @pytest.fixture
    def setup(self):
        self.group_repo = Mock()
        self.user_repo = Mock()
        self.bot_repo = Mock()
        self.group_usecase = GroupUseCase(
            group_repo=self.group_repo,
            user_repo=self.user_repo,
            bot_repo=self.bot_repo,
        )

    def dummy_bot(
        self,
        bot_id: bot_domain.Id,
        approach: bot_domain.Approach = bot_domain.Approach.CHAT_GPT_DEFAULT,
        search_method: bot_domain.SearchMethod | None = None,
        status: bot_domain.Status = bot_domain.Status.ACTIVE,
    ):
        return bot_domain.Bot(
            id=bot_id,
            group_id=group_domain.Id(value=1),
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            created_at=bot_domain.CreatedAt(root=datetime.now()),
            index_name=None,
            container_name=ContainerName(root="test-container"),
            approach=approach,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=search_method,
            response_generator_model_family=llm_domain.ModelFamily.GPT_35_TURBO,
            approach_variables=[],
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            status=status,
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#000000"),
            endpoint_id=bot_domain.EndpointId(root=UUID("81e418a2-820b-4059-82ee-3e90174ee5f5")),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
        )

    def test_get_groups_by_tenant_id(self, setup):
        """テナントIDによるグループ取得テスト"""
        tenant_id = tenant_domain.Id(value=1)
        want = [
            group_domain.Group(
                id=group_domain.Id(value=1),
                name=group_domain.Name(value="test"),
                is_general=group_domain.IsGeneral(root=False),
                created_at=group_domain.CreatedAt(value=datetime.now()),
            )
        ]

        self.group_usecase.group_repo.get_groups_by_tenant_id.return_value = want

        got = self.group_usecase.get_groups_by_tenant_id(tenant_id)

        assert got == want
        self.group_usecase.group_repo.get_groups_by_tenant_id.assert_called_once_with(tenant_id)

    def test_get_group_by_id_and_tenant_id(self, setup):
        """グループIDとテナントIDによるグループ取得テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)
        group = group_domain.Group(
            id=group_domain.Id(value=1),
            name=group_domain.Name(value="test"),
            created_at=group_domain.CreatedAt(value=datetime.now()),
            is_general=group_domain.IsGeneral(root=False),
        )

        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.return_value = group

        got = self.group_usecase.get_group_by_id_and_tenant_id(group_id, tenant_id)

        assert got == group
        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.assert_called_once_with(group_id, tenant_id)

    def test_create_group(self, setup):
        """グループ作成テスト"""
        tenant_id = tenant_domain.Id(value=1)
        name = group_domain.Name(value="test")
        group_admin_user_id = user_domain.Id(value=1)

        self.group_usecase.group_repo.find_by_tenant_id_and_name.return_value = None
        self.group_usecase.group_repo.create_group.return_value = group_domain.Group(
            id=group_domain.Id(value=1),
            name=name,
            is_general=group_domain.IsGeneral(root=False),
            created_at=group_domain.CreatedAt(value=datetime.now()),
        )

        self.group_usecase.create_group(tenant_id, name, group_admin_user_id)

        self.group_usecase.group_repo.create_group.assert_called_once_with(tenant_id, name)

    def test_create_group_already_exists(self, setup):
        """グループ作成テスト（グループが既に存在する場合）"""
        tenant_id = tenant_domain.Id(value=1)
        name = group_domain.Name(value="test")
        group_admin_user_id = user_domain.Id(value=1)
        self.group_usecase.group_repo.find_by_tenant_id_and_name.return_value = group_domain.Group(
            id=group_domain.Id(value=1),
            name=group_domain.Name(value="test"),
            is_general=group_domain.IsGeneral(root=False),
            created_at=group_domain.CreatedAt(value=datetime.now()),
        )

        with pytest.raises(BadRequest):
            self.group_usecase.create_group(tenant_id, name, group_admin_user_id)

    def test_update_group(self, setup):
        """グループ更新テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)
        name = group_domain.Name(value="test")

        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.return_value = group_domain.Group(
            id=group_id,
            name=group_domain.Name(value="test"),
            is_general=group_domain.IsGeneral(root=False),
            created_at=group_domain.CreatedAt(value=datetime.now()),
        )
        self.group_usecase.group_repo.update_group.return_value = None

        self.group_usecase.update_group(tenant_id, group_id, name)

        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.assert_called_once_with(group_id, tenant_id)
        self.group_usecase.group_repo.update_group.assert_called_once_with(group_id, name)

    def test_delete_group(self, setup):
        """グループ削除テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)

        self.group_usecase.bot_repo.find_by_group_id.return_value = []
        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.return_value = group_domain.Group(
            id=group_id,
            name=group_domain.Name(value="test"),
            is_general=group_domain.IsGeneral(root=False),
            created_at=group_domain.CreatedAt(value=datetime.now()),
        )
        self.group_usecase.group_repo.delete_group.return_value = None

        self.group_usecase.delete_group(tenant_id, group_id)

        self.group_usecase.bot_repo.find_by_group_id.assert_called_once_with(
            tenant_id,
            group_id,
            statuses=[bot_domain.Status.ACTIVE, bot_domain.Status.ARCHIVED, bot_domain.Status.DELETING],
        )
        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.assert_called_once_with(group_id, tenant_id)
        self.group_usecase.group_repo.delete_group.assert_called_once_with(tenant_id, group_id)

    def test_delete_group_with_bots(self, setup):
        """グループ削除テスト（グループに所属するボットが存在する場合）"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)

        self.group_usecase.bot_repo.find_by_group_id.return_value = [self.dummy_bot(bot_id=bot_domain.Id(value=1))]
        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.return_value = group_domain.Group(
            id=group_id,
            name=group_domain.Name(value="test"),
            is_general=group_domain.IsGeneral(root=False),
            created_at=group_domain.CreatedAt(value=datetime.now()),
        )

        with pytest.raises(BadRequest):
            self.group_usecase.delete_group(tenant_id, group_id)

    def test_delete_general_group(self, setup):
        """グループ削除テスト（Allグループは削除不可）"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)

        self.group_usecase.bot_repo.find_by_group_id.return_value = []
        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.return_value = group_domain.Group(
            id=group_id,
            name=group_domain.Name(value="test"),
            is_general=group_domain.IsGeneral(root=True),
            created_at=group_domain.CreatedAt(value=datetime.now()),
        )

        with pytest.raises(BadRequest):
            self.group_usecase.delete_group(tenant_id, group_id)

    def test_add_users_to_group(self, setup):
        """グループにユーザー追加テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)
        user_ids = [user_domain.Id(value=1)]

        self.group_usecase.user_repo.get_existing_user_ids.return_value = [user_domain.Id(value=1)]
        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.return_value = group_domain.Group(
            id=group_id,
            name=group_domain.Name(value="test"),
            is_general=group_domain.IsGeneral(root=False),
            created_at=group_domain.CreatedAt(value=datetime.now()),
        )
        self.group_usecase.group_repo.add_users_to_group.return_value = None

        self.group_usecase.add_users_to_group(tenant_id, group_id, user_ids)

        self.group_usecase.user_repo.get_existing_user_ids.assert_called_once_with(tenant_id, user_ids)
        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.assert_called_once_with(group_id, tenant_id)
        self.group_usecase.group_repo.add_users_to_group.assert_called_once_with(
            tenant_id=tenant_id, group_id=group_id, user_ids=[user_domain.Id(value=1)]
        )

    def test_delete_user_from_group(self, setup):
        """グループからユーザー削除テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)
        user_id = user_domain.Id(value=1)

        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.return_value = group_domain.Group(
            id=group_id,
            name=group_domain.Name(value="test"),
            is_general=group_domain.IsGeneral(root=False),
            created_at=group_domain.CreatedAt(value=datetime.now()),
        )
        self.group_usecase.group_repo.delete_user_from_group.return_value = None

        self.group_usecase.delete_user_from_group(tenant_id, group_id, user_id)

        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.assert_called_once_with(group_id, tenant_id)
        self.group_usecase.group_repo.delete_user_from_group.assert_called_once_with(group_id, user_id)

    def test_delete_users_from_group(self, setup):
        """グループからユーザー削除テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)
        user_ids = [user_domain.Id(value=1)]

        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.return_value = group_domain.Group(
            id=group_id,
            name=group_domain.Name(value="test"),
            is_general=group_domain.IsGeneral(root=False),
            created_at=group_domain.CreatedAt(value=datetime.now()),
        )
        self.group_usecase.group_repo.delete_users_from_group.return_value = None

        self.group_usecase.delete_users_from_group(tenant_id, group_id, user_ids)

        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.assert_called_once_with(group_id, tenant_id)
        self.group_usecase.group_repo.delete_users_from_group.assert_called_once_with(group_id, user_ids)

    def test_update_group_role(self, setup):
        """グループ権限更新テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        role = group_domain.GroupRole.GROUP_ADMIN

        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.return_value = []
        self.group_usecase.user_repo.update_group_role.return_value = None

        self.group_usecase.update_group_role(tenant_id, group_id, user_id, role)

        self.group_usecase.group_repo.get_group_by_id_and_tenant_id.assert_called_once_with(group_id, tenant_id)
        self.group_usecase.user_repo.update_group_role.assert_called_once_with(user_id, group_id, role)
