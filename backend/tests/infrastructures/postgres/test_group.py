from typing import Tuple
import uuid

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import IndexName
from api.domain.models.storage import ContainerName
from api.infrastructures.postgres.group import (
    Group as GroupModel,
    GroupRepository,
)
from api.infrastructures.postgres.user import UserRepository
from api.libs.exceptions import NotFound
from tests.conftest import GroupsSeed

TenantSeed = tenant_domain.Tenant
GroupSeed = Tuple[group_domain.Group, group_domain.Name, tenant_domain.Id]
UserSeed = Tuple[user_domain.Id, user_domain.UserForCreate, tenant_domain.Id, str, user_domain.Id]


class TestGroupRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.group_repo = GroupRepository(self.session)
        self.user_repo = UserRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def dummy_bot(self, bot_name: str) -> bot_domain.BotForCreate:
        return bot_domain.BotForCreate(
            name=bot_domain.Name(value=bot_name),
            description=bot_domain.Description(value="テストボット"),
            index_name=IndexName(root="test-bot"),
            container_name=ContainerName(root="test-bot"),
            approach=bot_domain.Approach("neollm"),
            example_questions=[bot_domain.ExampleQuestion(value="テストボット")],
            search_method=bot_domain.SearchMethod("default"),
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            pdf_parser=llm_domain.PdfParser("pypdf"),
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_url=bot_domain.IconUrl(
                root="https://neoscdevpublicstorage.blob.core.windows.net/common-container/neoai/0d9accfb-dc73-4dea-a358-9ab789cac7c0.png"
            ),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            endpoint_id=bot_domain.EndpointId(root=uuid.uuid4()),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            approach_variables=[],
        )

    def test_create_group(self, group_seed: GroupSeed):
        """新しいグループを作成するテスト"""
        new_group, group_for_create, tenant_id = group_seed
        want = group_domain.Group(
            id=new_group.id,
            name=group_for_create,
            created_at=new_group.created_at,
            is_general=new_group.is_general,
        )

        # 新しいグループが正しく作成されたことを確認
        assert new_group == want
        # データベースに新しいグループが保存されていることを確認
        saved_group = self.group_repo.get_group_by_id_and_tenant_id(new_group.id, tenant_id)
        assert saved_group == want

    def test_get_group_by_id_and_tenant_id(self, group_seed: GroupSeed):
        """存在するgroup.idとtenant.id"""
        new_group, _, tenant_id = group_seed

        group = self.group_repo.get_group_by_id_and_tenant_id(new_group.id, tenant_id)

        assert group == new_group

    def test_get_group_by_id_and_tenant_id_not_found(self):
        """存在しないgroup.idとtenant.id"""
        non_existent_group_id = group_domain.Id(value=9999)
        tenant_id = tenant_domain.Id(value=1)

        with pytest.raises(NotFound):
            self.group_repo.get_group_by_id_and_tenant_id(non_existent_group_id, tenant_id)

    def test_get_groups_by_tenant_id(self, group_seed: GroupSeed):
        """tenant_idがあるケース"""
        new_group, _, tenant_id = group_seed

        groups = self.group_repo.get_groups_by_tenant_id(tenant_id)
        # グループが存在することを確認
        assert groups == [
            group_domain.Group(
                id=new_group.id,
                name=new_group.name,
                created_at=new_group.created_at,
                is_general=new_group.is_general,
            )
        ]

    def test_get_groups_by_tenant_id_not_found(self):
        """tenant_idが見つからないケース"""
        non_existent_tenant_id = tenant_domain.Id(value=9999)

        groups = self.group_repo.get_groups_by_tenant_id(non_existent_tenant_id)
        assert groups == []

    def test_update_group(self, group_seed: GroupSeed):
        """グループ名を更新するテスト"""
        new_group, _, _ = group_seed
        new_name = group_domain.Name(value="新しいグループ名")

        updated_group = self.group_repo.update_group(new_group.id, new_name)

        assert updated_group is not None
        assert updated_group.name == new_name.value

    def test_delete_group(self, tenant_seed: TenantSeed):
        """グループを削除するテスト"""
        tenant = tenant_seed
        new_group = self.group_repo.create_group(
            tenant_id=tenant.id,
            name=group_domain.Name(value="テストグループ"),
        )

        self.group_repo.delete_group(tenant.id, new_group.id)

        with pytest.raises(NotFound):
            self.group_repo.get_group_by_id_and_tenant_id(new_group.id, tenant.id)

    def test_delete_group_not_found(self):
        """存在しないグループIDで削除を試みるテスト"""
        non_existent_group_id = group_domain.Id(value=9999)
        tenant_id = tenant_domain.Id(value=1)

        with pytest.raises(NotFound):
            self.group_repo.delete_group(tenant_id, non_existent_group_id)

    @pytest.mark.parametrize("group_seed", [{"cleanup_resources": False}], indirect=True)
    def test_delete_by_tenant_id(self, group_seed: GroupSeed):
        """グループを論理削除するテスト"""
        group, _, tenant_id = group_seed

        self.group_repo.delete_by_tenant_id(tenant_id)

        with pytest.raises(NotFound):
            self.group_repo.get_group_by_id_and_tenant_id(group.id, tenant_id)

    @pytest.mark.parametrize("group_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_tenant_id(self, group_seed: GroupSeed):
        """グループを物理削除するテスト"""
        group, _, tenant_id = group_seed

        self.group_repo.delete_group(tenant_id, group.id)
        self.group_repo.hard_delete_by_tenant_id(tenant_id)

        groups = (
            self.session.execute(
                select(GroupModel)
                .where(GroupModel.tenant_id == tenant_id.value)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )
        assert len(groups) == 0

    def test_add_users_to_group(self, group_seed: GroupSeed):
        """ユーザーをグループに追加するテスト"""
        new_group, _, tenant_id = group_seed

        # ユーザーの作成
        user_info = {
            "name": "テストユーザーingroup",
            "email": "testuseringroup@example.com",
            "auth0_id": "auth0|testuseringroup",
        }

        user_for_create = user_domain.UserForCreate(
            name=user_domain.Name(value=user_info["name"]),
            email=user_domain.Email(value=user_info["email"]),
            roles=[user_domain.Role("admin"), user_domain.Role("user")],
        )

        new_user_id = self.user_repo.create(tenant_id, user_for_create, user_info["auth0_id"])

        self.group_repo.add_users_to_group(tenant_id, new_group.id, [new_user_id], group_domain.GroupRole.GROUP_ADMIN)

        users = self.user_repo.find_by_tenant_id_and_group_id(tenant_id, new_group.id)

        assert users == [
            user_domain.UserWithGroupRole(
                id=new_user_id,
                name=user_for_create.name,
                email=user_for_create.email,
                roles=user_for_create.roles,
                group_role=group_domain.GroupRole.GROUP_ADMIN,
            )
        ]

    def test_delete_user_from_group(self, group_seed: GroupSeed, user_seed: UserSeed):
        """ユーザーをグループから削除するテスト"""

        new_group, _, tenant_id = group_seed
        new_user_id, _, _, _, _ = user_seed

        self.group_repo.add_users_to_group(tenant_id, new_group.id, [new_user_id])
        self.group_repo.delete_user_from_group(new_group.id, new_user_id)

        users = self.user_repo.find_by_tenant_id_and_group_id(tenant_id, new_group.id)

        assert users == []

    def test_delete_user_from_group_not_found(self, group_seed: GroupSeed):
        """存在しないユーザーIDを用いてグループからユーザーを削除するテスト"""
        new_group, _, _ = group_seed
        non_existent_user_id = user_domain.Id(value=9999)

        with pytest.raises(NotFound):
            self.group_repo.delete_user_from_group(new_group.id, non_existent_user_id)

    def test_delete_users_from_group(self, group_seed: GroupSeed, user_seed: UserSeed):
        """グループから複数のユーザーを削除するテスト"""

        new_group, _, tenant_id = group_seed
        new_user_id, _, _, _, new_user_id2 = user_seed
        new_user_ids = [new_user_id, new_user_id2]

        self.group_repo.add_users_to_group(tenant_id, new_group.id, new_user_ids)
        self.group_repo.delete_users_from_group(new_group.id, new_user_ids)

        users = self.user_repo.find_by_tenant_id_and_group_id(tenant_id, new_group.id)

        assert users == []

    def test_find_by_tenant_id_and_user_id(self, groups_seed: GroupsSeed, user_seed: UserSeed):
        """ユーザーが所属するグループを取得するテスト"""
        new_groups, tenant_id = groups_seed
        new_user_id, _, _, _, _ = user_seed
        for group in new_groups:
            self.group_repo.add_users_to_group(tenant_id, group.id, [new_user_id])

        groups = self.group_repo.find_by_tenant_id_and_user_id(tenant_id, new_user_id)
        # 順不同で比較
        assert sorted(groups, key=lambda x: x.id.value) == sorted(new_groups, key=lambda x: x.id.value)
