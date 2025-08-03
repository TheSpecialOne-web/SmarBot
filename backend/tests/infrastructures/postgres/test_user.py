from typing import Tuple

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    policy as policy_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import IndexName
from api.domain.models.storage import ContainerName
from api.infrastructures.postgres.bot import BotRepository
from api.infrastructures.postgres.group import GroupRepository
from api.infrastructures.postgres.user import (
    User as UserModel,
    UserRepository,
)
from api.libs.exceptions import NotFound

UserSeed = Tuple[
    user_domain.Id, user_domain.UserForCreate, tenant_domain.Id, user_domain.ExternalUserId, user_domain.Id
]
TenantSeed = tenant_domain.Tenant
GroupSeed = Tuple[group_domain.Group, group_domain.Name, tenant_domain.Id]
BotsSeed = Tuple[list[bot_domain.Bot], list[dict], tenant_domain.Tenant, group_domain.Group]


class TestUserRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.user_repo = UserRepository(self.session)
        self.group_repo = GroupRepository(self.session)
        self.bot_repo = BotRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def dummy_bot_for_create(self):
        return bot_domain.BotForCreate(
            name=bot_domain.Name(value="Test Bot"),
            description=bot_domain.Description(value="This is a test bot."),
            index_name=None,
            container_name=None,
            approach=bot_domain.Approach.NEOLLM,
            pdf_parser=llm_domain.PdfParser.PYPDF,
            example_questions=[bot_domain.ExampleQuestion(value="Example question.")],
            search_method=bot_domain.SearchMethod.BM25,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            enable_web_browsing=bot_domain.EnableWebBrowsing(root=False),
            enable_follow_up_questions=bot_domain.EnableFollowUpQuestions(root=False),
            icon_color=bot_domain.IconColor(root="#AA68FF"),
            max_conversation_turns=bot_domain.MaxConversationTurns(root=5),
            approach_variables=[],
        )

    def test_get_user_info_by_external_id(self, user_seed: UserSeed):
        """auth0_idによるユーザー検索のテスト"""
        new_user_id, user_for_create, _, auth0_id, _ = user_seed

        user = self.user_repo.get_user_info_by_external_id(auth0_id)

        # ユーザーが正しく取得できたことを確認
        assert user is not None
        assert user.id.value == new_user_id.value
        assert user.name.value == user_for_create.name.value
        assert user.email.value == user_for_create.email.value

    def test_get_user_info_by_external_id_not_found(self):
        """存在しないauth0_idでの検索テスト"""
        non_existent_auth0_id = "email|9999999999"

        with pytest.raises(NotFound):
            self.user_repo.get_user_info_by_external_id(user_domain.ExternalUserId.from_string(non_existent_auth0_id))

    def test_get_user_info_by_email(self, user_seed: UserSeed):
        """emailによるユーザー検索のテスト"""
        new_user_id, user_for_create, _, _, _ = user_seed

        user = self.user_repo.get_user_info_by_email(user_for_create.email)

        # ユーザーが正しく取得できたことを確認
        assert user is not None
        assert user.id.value == new_user_id.value
        assert user.name.value == user_for_create.name.value
        assert user.email.value == user_for_create.email.value

    def test_get_user_info_by_email_not_found(self, user_seed: UserSeed):
        """存在しないemailでの検索テスト"""
        non_existent_email = "test@example.com"

        with pytest.raises(NotFound):
            self.user_repo.get_user_info_by_email(user_domain.Email(value=non_existent_email))

    def test_find_by_tenant_id(self, user_seed: UserSeed):
        """tenant_idによるユーザー検索のテスト"""

        new_user_id, user_for_create, tenant_id, _, _ = user_seed

        users = self.user_repo.find_by_tenant_id(tenant_id)

        # ユーザーが正しく取得できたことを確認
        assert len(users) > 0
        for user in users:
            if user.id.value == new_user_id.value:
                assert user.name.value == user_for_create.name.value
                assert user.email.value == user_for_create.email.value
                assert user.roles == user_for_create.roles
                assert user.policies == []

    def test_find_by_tenant_id_not_found(self):
        """存在しないtenant_idでの検索テスト"""

        non_existent_tenant_id = tenant_domain.Id(value=9999)

        users = self.user_repo.find_by_tenant_id(non_existent_tenant_id)

        assert len(users) == 0

    def test_find_by_tenant_id_and_email(self, user_seed: UserSeed):
        """tenant_idとemailによるユーザー検索のテスト"""

        new_user_id, user_for_create, tenant_id, _, _ = user_seed

        user = self.user_repo.find_by_tenant_id_and_email(tenant_id, user_for_create.email)

        # ユーザーが正しく取得できたことを確認
        assert user is not None
        assert user.id.value == new_user_id.value
        assert user.name.value == user_for_create.name.value
        assert user.email.value == user_for_create.email.value
        assert user.roles == user_for_create.roles
        assert user.policies == []

    def test_find_by_tenant_id_and_email_not_found(self, user_seed: UserSeed):
        """存在しないtenant_idとemailでの検索テスト"""

        _, _, tenant_id, _, _ = user_seed
        non_existent_email = user_domain.Email(value="notexist@example.com")

        with pytest.raises(NotFound):
            self.user_repo.find_by_tenant_id_and_email(tenant_id, non_existent_email)

    def test_find_by_id_and_tenant_id(self, user_seed: UserSeed):
        """idとtenant_idによるユーザー検索のテスト"""

        new_user_id, user_for_create, tenant_id, _, _ = user_seed

        user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)

        # ユーザーが正しく取得できたことを確認
        assert user is not None
        assert user.id.value == new_user_id.value
        assert user.name.value == user_for_create.name.value
        assert user.email.value == user_for_create.email.value
        assert user.roles == user_for_create.roles
        assert user.policies == []

    def test_find_by_id_and_tenant_id_not_found(self, user_seed: UserSeed):
        """存在しないidとtenant_idでの検索テスト"""

        _, _, tenant_id, _, _ = user_seed
        non_existent_user_id = user_domain.Id(value=9999)

        with pytest.raises(NotFound):
            self.user_repo.find_by_id_and_tenant_id(non_existent_user_id, tenant_id)

    def test_find_by_email(self, user_seed: UserSeed):
        """emailによるユーザー検索のテスト"""

        new_user_id, user_for_create, _, _, _ = user_seed

        user = self.user_repo.find_by_email(user_for_create.email)

        # ユーザーが正しく取得できたことを確認
        assert user is not None
        assert user.id.value == new_user_id.value
        assert user.name.value == user_for_create.name.value
        assert user.email.value == user_for_create.email.value
        assert user.roles == user_for_create.roles
        assert user.policies == []

    def test_find_by_email_not_found(self, user_seed: UserSeed):
        """存在しないemailでの検索テスト"""

        non_existent_email = user_domain.Email(value="notfounduser@example.com")

        with pytest.raises(NotFound):
            self.user_repo.find_by_email(non_existent_email)

    def test_find_by_emails(self, user_seed: UserSeed):
        """emailリストによるユーザー検索のテスト"""

        new_user_id, user_for_create, _, _, _ = user_seed

        user_ids = self.user_repo.find_by_emails([user_for_create.email])

        # ユーザーが正しく取得できたことを確認
        assert len(user_ids) == 1
        assert user_ids[0].value == new_user_id.value

    def test_find_by_emails_not_found(self, user_seed: UserSeed):
        """存在しないemailリストでの検索テスト"""

        non_existent_emails = [user_domain.Email(value="notfounduser@example.com")]

        with pytest.raises(NotFound):
            self.user_repo.find_by_emails(non_existent_emails)

    def test_find_by_tenant_id_and_group_id(self, group_seed: GroupSeed):
        """tenant_idとgroup_idによるユーザー検索のテスト"""

        new_group, _, tenant_id = group_seed

        user_for_create = user_domain.UserForCreate(
            name=user_domain.Name(value="テストユーザー"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role("admin"), user_domain.Role("user")],
        )
        new_user_id = self.user_repo.create(
            tenant_id,
            user_for_create,
            auth0_id="auth0|abcdefghijk",
        )

        self.group_repo.add_users_to_group(tenant_id, new_group.id, [new_user_id])

        users = self.user_repo.find_by_tenant_id_and_group_id(tenant_id, new_group.id)

        assert users == [
            user_domain.UserWithGroupRole(
                id=new_user_id,
                name=user_for_create.name,
                email=user_for_create.email,
                roles=user_for_create.roles,
                group_role=group_domain.GroupRole.GROUP_VIEWER,
            )
        ]

        self.user_repo.delete_by_id_and_tenant_id(new_user_id, tenant_id)

    def test_get_existing_user_ids(self, user_seed: UserSeed):
        """既存のユーザーIDを取得するテスト"""

        new_user_id, _, tenant_id, _, _ = user_seed
        existing_user_ids = [new_user_id]

        user_ids = self.user_repo.get_existing_user_ids(tenant_id, existing_user_ids)

        assert len(user_ids) == 1
        assert user_ids[0].value == new_user_id.value

    def test_get_existing_user_ids_not_found(self, user_seed: UserSeed):
        """存在しないユーザーIDを取得するテスト"""

        _, _, tenant_id, _, _ = user_seed
        non_existent_user_ids = [user_domain.Id(value=9999)]

        user_ids = self.user_repo.get_existing_user_ids(tenant_id, non_existent_user_ids)

        assert len(user_ids) == 0

    def test_get_users_with_group_ids(self, group_seed: GroupSeed):
        """グループに所属するユーザーを取得するテスト"""

        new_group, _, tenant_id = group_seed

        user_for_create = user_domain.UserForCreate(
            name=user_domain.Name(value="テストユーザー"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role("admin"), user_domain.Role("user")],
        )
        new_user_id = self.user_repo.create(
            tenant_id,
            user_for_create,
            auth0_id="auth0|getuserswithgroupids",
        )

        self.group_repo.add_users_to_group(tenant_id, new_group.id, [new_user_id])

        users = self.user_repo.get_users_with_group_ids(tenant_id)

        assert len(users) == 1
        for user in users:
            assert user.id.value == new_user_id.value
            assert user.name.value == user_for_create.name.value
            assert user.email.value == user_for_create.email.value
            assert user.roles == user_for_create.roles
            assert user.group_ids == [new_group.id]

        self.user_repo.delete_by_id_and_tenant_id(new_user_id, tenant_id)

    def test_get_users_with_group_ids_without_groups(self, tenant_seed: TenantSeed):
        """グループに所属しないユーザーを取得するテスト"""

        tenant_id = tenant_seed.id

        user_for_create = user_domain.UserForCreate(
            name=user_domain.Name(value="テストユーザー"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role("admin"), user_domain.Role("user")],
        )
        new_user_id = self.user_repo.create(
            tenant_id,
            user_for_create,
            auth0_id="auth0|getuserswithgroupidswithoutgroups",
        )

        users = self.user_repo.get_users_with_group_ids(tenant_id)

        assert len(users) == 1
        for user in users:
            assert user.id.value == new_user_id.value
            assert user.name.value == user_for_create.name.value
            assert user.email.value == user_for_create.email.value
            assert user.roles == user_for_create.roles
            assert user.group_ids == []

        self.user_repo.delete_by_id_and_tenant_id(new_user_id, tenant_id)

    def test_update_group_role(self, group_seed: GroupSeed, user_seed: UserSeed):
        """グループ権限を更新するテスト"""

        new_group, _, tenant_id = group_seed
        new_user_id, _, _, _, _ = user_seed

        self.group_repo.add_users_to_group(tenant_id, new_group.id, [new_user_id])

        self.user_repo.update_group_role(new_user_id, new_group.id, group_domain.GroupRole.GROUP_ADMIN)

        users = self.user_repo.find_by_tenant_id_and_group_id(tenant_id, new_group.id)
        user = next((u for u in users if u.id == new_user_id), None)

        assert user is not None
        assert user.group_role == group_domain.GroupRole.GROUP_ADMIN

    def test_create(self, user_seed: UserSeed):
        """新しいユーザーを作成するテスト"""

        _, _, tenant_id, _, _ = user_seed

        # ユーザーの作成
        new_user = user_domain.UserForCreate(
            name=user_domain.Name(value="テストユーザー"),
            email=user_domain.Email(value="test1@example.com"),
            roles=[user_domain.Role("admin"), user_domain.Role("user")],
        )

        new_user_id = self.user_repo.create(tenant_id, new_user, "auth0|0123456789")

        # 新しいユーザーが正しく作成されたことを確認
        assert new_user_id is not None
        assert new_user_id.value > 0
        # データベースに新しいユーザーが保存されていることを確認
        saved_user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)
        assert saved_user is not None
        assert saved_user.name.value == new_user.name.value
        assert saved_user.email.value == new_user.email.value
        assert saved_user.roles == new_user.roles
        assert saved_user.policies == []

    def test_update(self, user_seed: UserSeed):
        """既存のユーザーを更新するテスト"""

        new_user_id, _, tenant_id, _, _ = user_seed

        update_user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)
        update_user.name = user_domain.Name(value="UpdatedUser")

        self.user_repo.update(new_user_id, update_user.name)

        updated_user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)
        assert updated_user is not None
        assert updated_user.name == update_user.name

    def test_delete_by_id_and_tenant_id(self, tenant_seed: TenantSeed):
        """delete関数を実行し、ユーザーが論理削除されているかを検証"""

        tenant = tenant_seed
        tenant_id = tenant.id
        new_user_id = self.user_repo.create(
            tenant_id,
            user_domain.UserForCreate(
                name=user_domain.Name(value="テストユーザー"),
                email=user_domain.Email(value="testdeletebyidandtenantid@example.com"),
                roles=[user_domain.Role("admin"), user_domain.Role("user")],
            ),
            "auth0|testdeletebyidandtenantid",
        )

        self.user_repo.delete_by_id_and_tenant_id(new_user_id, tenant_id)

        # 削除後のユーザーを取得して検証
        with pytest.raises(NotFound):
            self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)

    @pytest.mark.parametrize("user_seed", [{"cleanup_resources": False}], indirect=True)
    def test_delete_by_tenant_id(self, user_seed: UserSeed):
        """テナントIDによるユーザーの論理削除テスト"""
        _, _, tenant_id, _, _ = user_seed

        self.user_repo.delete_by_tenant_id(tenant_id)

        users = self.user_repo.find_by_tenant_id(tenant_id)
        assert len(users) == 0

    @pytest.mark.parametrize("user_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_tenant_id(self, user_seed: UserSeed):
        """テナントIDによるユーザーの物理削除テスト"""
        _, _, tenant_id, _, _ = user_seed

        self.user_repo.delete_by_tenant_id(tenant_id)
        self.user_repo.hard_delete_by_tenant_id(tenant_id)

        users = (
            self.session.execute(
                select(UserModel).where(UserModel.tenant_id == tenant_id.value).execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )
        assert len(users) == 0

    def test_add_roles(self, user_seed: UserSeed):
        """ユーザーにロールを追加するテスト"""

        new_user_id, _, tenant_id, _, _ = user_seed

        # ロールの追加
        new_roles = [user_domain.Role("admin"), user_domain.Role("user")]
        self.user_repo.add_roles(new_user_id, tenant_id, new_roles)

        # ロールが正しく追加されたことを確認
        user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)
        assert user.roles == new_roles

    def test_delete_role(self, user_seed: UserSeed):
        """ユーザーのロールを削除するテスト"""

        new_user_id, _, tenant_id, _, _ = user_seed

        # ロールの削除
        delete_role = user_domain.Role("admin")
        self.user_repo.delete_role(new_user_id, tenant_id, delete_role)

        # ロールが正しく削除されたことを確認
        user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)
        assert delete_role not in user.roles

    def test_find_policy(self, user_seed: UserSeed):
        user_id, _, tenant_id, _, _ = user_seed
        group = self.group_repo.create_group(tenant_id, group_domain.Name(value="テストグループ"))
        self.group_repo.add_users_to_group(tenant_id, group.id, [user_id])
        self.user_repo.update_group_role(user_id, group.id, group_domain.GroupRole.GROUP_EDITOR)
        bot = self.bot_repo.create(
            tenant_id=tenant_id,
            group_id=group.id,
            bot=self.dummy_bot_for_create(),
        )
        self.user_repo.update_user_policy(
            user_id, tenant_id, policy_domain.Policy(bot_id=bot.id, action=policy_domain.Action.from_str("read"))
        )

        policy = self.user_repo.find_policy(user_id, tenant_id, bot.id)
        assert policy == policy_domain.Policy(bot_id=bot.id, action=policy_domain.Action.from_str("write"))

    def test_find_policy_with_no_user_policy(self, user_seed: UserSeed):
        user_id, _, tenant_id, _, _ = user_seed
        group = self.group_repo.create_group(tenant_id, group_domain.Name(value="テストグループ"))
        self.group_repo.add_users_to_group(tenant_id, group.id, [user_id])
        self.user_repo.update_group_role(user_id, group.id, group_domain.GroupRole.GROUP_EDITOR)
        bot = self.bot_repo.create(
            tenant_id=tenant_id,
            group_id=group.id,
            bot=self.dummy_bot_for_create(),
        )

        policy = self.user_repo.find_policy(user_id, tenant_id, bot.id)
        assert policy == policy_domain.Policy(bot_id=bot.id, action=policy_domain.Action.from_str("write"))

    def test_find_policy_with_no_group_role(self, user_seed: UserSeed):
        user_id, _, tenant_id, _, _ = user_seed
        group = self.group_repo.create_group(tenant_id, group_domain.Name(value="テストグループ"))
        bot = self.bot_repo.create(
            tenant_id=tenant_id,
            group_id=group.id,
            bot=self.dummy_bot_for_create(),
        )
        self.user_repo.update_user_policy(
            user_id, tenant_id, policy_domain.Policy(bot_id=bot.id, action=policy_domain.Action.from_str("read"))
        )

        policy = self.user_repo.find_policy(user_id, tenant_id, bot.id)
        assert policy == policy_domain.Policy(bot_id=bot.id, action=policy_domain.Action.from_str("read"))

    def test_find_policy_with_no_user_policy_and_group_role(self, user_seed: UserSeed):
        user_id, _, tenant_id, _, _ = user_seed
        group = self.group_repo.create_group(tenant_id, group_domain.Name(value="テストグループ"))
        bot = self.bot_repo.create(
            tenant_id=tenant_id,
            group_id=group.id,
            bot=self.dummy_bot_for_create(),
        )

        with pytest.raises(NotFound, match="ポリシーが見つかりませんでした。"):
            self.user_repo.find_policy(user_id, tenant_id, bot.id)

    def test_update_user_policy(self, user_seed: UserSeed):
        """ユーザーのポリシーを更新するテスト"""

        new_user_id, _, tenant_id, _, _ = user_seed
        group_id = group_domain.Id(value=1)

        new_bot = self.bot_repo.create(
            tenant_id=tenant_id,
            group_id=group_id,
            bot=bot_domain.BotForCreate(
                name=bot_domain.Name(value="テストボット"),
                description=bot_domain.Description(value="テストボット"),
                index_name=IndexName(root="test-bot"),
                container_name=ContainerName(root="test-bot"),
                approach=bot_domain.Approach("neollm"),
                example_questions=[bot_domain.ExampleQuestion(value="テストボット")],
                search_method=bot_domain.SearchMethod.BM25,
                response_generator_model_family=ModelFamily.GPT_35_TURBO,
                pdf_parser=llm_domain.PdfParser("pypdf"),
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

        # ポリシーの更新
        update_user_policy = policy_domain.Policy(
            bot_id=new_bot.id,
            action=policy_domain.Action(root=policy_domain.ActionEnum.READ),
        )
        self.user_repo.update_user_policy(new_user_id, tenant_id, update_user_policy)

        # ポリシーが正しく更新されたことを確認
        user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)
        assert user.policies == [update_user_policy]

    def test_delete_user_policy(self, user_seed: UserSeed):
        """ユーザーのポリシーを削除するテスト"""

        new_user_id, _, tenant_id, _, _ = user_seed

        new_bot = self.bot_repo.create(
            tenant_id=tenant_id,
            group_id=group_domain.Id(value=1),
            bot=bot_domain.BotForCreate(
                name=bot_domain.Name(value="テストボットfor delete policy"),
                description=bot_domain.Description(value="テストボット"),
                index_name=IndexName(root="test-bot"),
                container_name=ContainerName(root="test-bot"),
                approach=bot_domain.Approach("neollm"),
                example_questions=[bot_domain.ExampleQuestion(value="テストボット")],
                search_method=bot_domain.SearchMethod.BM25,
                response_generator_model_family=ModelFamily.GPT_35_TURBO,
                pdf_parser=llm_domain.PdfParser("pypdf"),
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

        # ポリシーの削除
        self.user_repo.delete_user_policy(new_user_id, tenant_id, bot_id=new_bot.id)

        # ポリシーが正しく削除されたことを確認
        user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)
        assert user.policies == []

    def test_find_by_tenant_id_and_emails(self, group_seed: GroupSeed):
        """tenant_idとemailリストによるユーザー検索のテスト"""

        new_group, _, tenant_id = group_seed

        user_for_create = user_domain.UserForCreate(
            name=user_domain.Name(value="テストユーザー"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role("admin"), user_domain.Role("user")],
        )
        new_user_id = self.user_repo.create(
            tenant_id,
            user_for_create,
            auth0_id="auth0|getuserswithgroupids",
        )

        self.group_repo.add_users_to_group(tenant_id, new_group.id, [new_user_id])

        users = self.user_repo.find_by_tenant_id_and_emails(tenant_id, [user_for_create.email])

        assert users == [
            user_domain.UserWithGroupIds(
                id=new_user_id,
                name=user_for_create.name,
                email=user_for_create.email,
                roles=user_for_create.roles,
                group_ids=[new_group.id],
            )
        ]

        self.user_repo.delete_by_id_and_tenant_id(new_user_id, tenant_id)

    def test_find_by_tenant_id_and_emails_without_groups(self, tenant_seed: TenantSeed):
        """tenant_idとemailリストによるユーザー検索のテスト(グループに所属していない)"""

        tenant_id = tenant_seed.id

        user_for_create = user_domain.UserForCreate(
            name=user_domain.Name(value="テストユーザー"),
            email=user_domain.Email(value="testtest@example.com"),
            roles=[user_domain.Role("admin"), user_domain.Role("user")],
        )
        new_user_id = self.user_repo.create(
            tenant_id,
            user_for_create,
            auth0_id="auth0|findbytenantidandemailwithoutgroups",
        )

        users = self.user_repo.find_by_tenant_id_and_emails(tenant_id, [user_for_create.email])

        assert users == [
            user_domain.UserWithGroupIds(
                id=new_user_id,
                name=user_for_create.name,
                email=user_for_create.email,
                roles=user_for_create.roles,
                group_ids=[],
            )
        ]
        self.user_repo.delete_by_id_and_tenant_id(new_user_id, tenant_id)

    def test_bulk_update(self, user_seed: UserSeed):
        """ユーザーの一括更新テスト"""

        new_user_id, user, tenant_id, _, _ = user_seed

        users_for_bulk_update = [
            user_domain.UserForBulkUpdate(
                id=new_user_id,
                name=user_domain.Name(value="BulkUpdatedUser"),
                roles=[user_domain.Role("admin")],
            )
        ]

        self.user_repo.bulk_update(tenant_id, users_for_bulk_update)

        updated_user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)

        assert updated_user == user_domain.User(
            id=new_user_id,
            name=users_for_bulk_update[0].name,
            email=user.email,
            roles=users_for_bulk_update[0].roles,
            policies=[],
        )

    def test_delete_user_policy_by_bot_id(self, user_seed: UserSeed, bots_seed: BotsSeed):
        """ユーザーポリシーを削除するテスト"""

        new_user_id, _, tenant_id, _, _ = user_seed
        new_bots, _, _, _ = bots_seed
        new_bot = new_bots[0]
        self.user_repo.update_user_policy(
            new_user_id,
            tenant_id,
            policy_domain.Policy(bot_id=new_bot.id, action=policy_domain.Action(root=policy_domain.ActionEnum.READ)),
        )

        self.user_repo.delete_user_policy_by_bot_id(new_bot.id)

        user = self.user_repo.find_by_id_and_tenant_id(new_user_id, tenant_id)
        assert user.policies == []
