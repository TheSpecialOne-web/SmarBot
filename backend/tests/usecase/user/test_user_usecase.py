import datetime
from unittest.mock import Mock, call

import pytest

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    policy as policy_domain,
    search as search_domain,
    storage as storage_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm import AllowForeignRegion
from api.domain.models.llm.model import ModelFamily
from api.domain.models.tenant import statistics as tenant_statistics_domain
from api.domain.models.user import administrator as administrator_domain
from api.libs.exceptions import BadRequest, NotFound
from api.usecase.user import (
    BulkCreateUsersInputData,
    UpdateUserPolicyInputData,
    UserForBulkCreateOrUpdate,
    UserForDownload,
    UserUseCase,
)
from api.usecase.user.user import BulkUpdateUsersInputData


class TestUserUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo = Mock()
        self.user_repo = Mock()
        self.auth0_service = Mock()
        self.group_repo = Mock()
        self.blob_storage_service = Mock()
        self.queue_storage_service = Mock()
        self.msgraph_service = Mock()
        self.user_usecase = UserUseCase(
            tenant_repo=self.tenant_repo,
            user_repo=self.user_repo,
            auth0_service=self.auth0_service,
            group_repo=self.group_repo,
            blob_storage_service=self.blob_storage_service,
            queue_storage_service=self.queue_storage_service,
            msgraph_service=self.msgraph_service,
        )

    @pytest.fixture
    def mock_get_feature_flag(self, monkeypatch):
        mock_get_feature_flag = Mock()
        monkeypatch.setattr("api.usecase.user.user.get_feature_flag", mock_get_feature_flag)
        return mock_get_feature_flag

    def dummy_user_info(self) -> user_domain.UserInfoWithGroupsAndPolicies:
        return user_domain.UserInfoWithGroupsAndPolicies(
            id=user_domain.Id(value=1),
            name=user_domain.Name(value="test"),
            email=user_domain.Email(value="test@example.com"),
            tenant=tenant_domain.Tenant(
                id=tenant_domain.Id(value=1),
                name=tenant_domain.Name(value="test"),
                alias=tenant_domain.Alias(root="test"),
                status=tenant_domain.Status.TRIAL,
                search_service_endpoint=search_domain.Endpoint(root="https://test-search-service-endpoint.com"),
                index_name=search_domain.IndexName(root="test"),
                container_name=storage_domain.ContainerName(root="test"),
                allowed_ips=tenant_domain.AllowedIPs(root=[]),
                is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
                allow_foreign_region=AllowForeignRegion(root=False),
                additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
                enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=False),
                enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
                enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
                usage_limit=tenant_domain.UsageLimit(
                    free_user_seat=50,
                    additional_user_seat=10,
                    free_token=10000000,
                    additional_token=0,
                    free_storage=1000000000,
                    additional_storage=0,
                    document_intelligence_page=8000,
                ),
                enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
                enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
                basic_ai_pdf_parser=llm_domain.BasicAiPdfParser(llm_domain.BasicAiPdfParser.PYPDF),
                max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
                allowed_model_families=[ModelFamily.GPT_35_TURBO],
                basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
                enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
            ),
            roles=[user_domain.Role.ADMIN],
            policies=[],
            groups=[],
            is_administrator=user_domain.IsAdministrator(value=True),
            liked_bot_ids=[],
        )

    def test_get_user_info_email_connection(self, setup):
        """ユーザー情報取得テスト"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        auth0_user_id = user_domain.ExternalUserId.from_string("email|test_auth0_user_id")
        want = self.dummy_user_info()

        self.user_usecase.auth0_service.validate_token = Mock(return_value=auth0_user_id)
        self.user_usecase.user_repo.get_user_info_with_groups_and_policies_by_external_id = Mock(return_value=want)

        got = self.user_usecase.get_user_info(token)

        self.user_usecase.auth0_service.validate_token.assert_called_once_with(token)
        self.user_usecase.user_repo.get_user_info_with_groups_and_policies_by_external_id.assert_called_once_with(
            auth0_user_id
        )
        assert got == want

    def test_get_user_info_entra_id(self, setup):
        """ユーザー情報取得テスト"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        auth0_user_id = user_domain.ExternalUserId.from_string("waad|test_auth0_user_id")
        want = self.dummy_user_info()

        self.user_usecase.auth0_service.validate_token = Mock(return_value=auth0_user_id)
        self.user_usecase.auth0_service.find_by_id = Mock(
            return_value=user_domain.IdpUser.from_id_and_email(id=auth0_user_id.root, email=want.email.value)
        )
        self.user_usecase.user_repo.get_user_info_with_groups_and_policies_by_email = Mock(return_value=want)

        got = self.user_usecase.get_user_info(token)

        self.user_usecase.auth0_service.validate_token.assert_called_once_with(token)
        self.user_usecase.auth0_service.find_by_id.assert_called_once_with(auth0_user_id)
        self.user_usecase.user_repo.get_user_info_with_groups_and_policies_by_email.assert_called_once_with(want.email)
        assert got == want

    def test_get_users_by_tenant_id(self, setup):
        """テナントIDによるユーザー取得テスト"""
        tenant_id = tenant_domain.Id(value=1)
        want = [
            user_domain.User(
                id=user_domain.Id(value=1),
                name=user_domain.Name(value="test"),
                email=user_domain.Email(value="test@example.com"),
                roles=[user_domain.Role.ADMIN],
                policies=[],
            ),
            user_domain.User(
                id=user_domain.Id(value=2),
                name=user_domain.Name(value="test2"),
                email=user_domain.Email(value="test2@example.com"),
                roles=[user_domain.Role.USER],
                policies=[],
            ),
        ]

        self.user_usecase.user_repo.find_by_tenant_id.return_value = want

        got = self.user_usecase.get_users_by_tenant_id(tenant_id)

        self.user_usecase.user_repo.find_by_tenant_id.assert_called_once_with(tenant_id)
        assert got == want

    def test_get_users_by_tenant_id_and_group_id(self, setup):
        """テナントIDとグループIDによるユーザー取得テスト"""
        tenant_id = tenant_domain.Id(value=1)
        group_id = group_domain.Id(value=1)
        want = [
            user_domain.UserWithGroupRole(
                id=user_domain.Id(value=1),
                name=user_domain.Name(value="test"),
                email=user_domain.Email(value="test@example.com"),
                roles=[user_domain.Role.ADMIN],
                policies=[],
                group_role=group_domain.GroupRole.GROUP_ADMIN,
            ),
            user_domain.UserWithGroupRole(
                id=user_domain.Id(value=2),
                name=user_domain.Name(value="test2"),
                email=user_domain.Email(value="test2@example.com"),
                roles=[user_domain.Role.USER],
                policies=[],
                group_role=group_domain.GroupRole.GROUP_VIEWER,
            ),
        ]

        self.user_usecase.user_repo.find_by_tenant_id_and_group_id = Mock(return_value=want)

        got = self.user_usecase.get_users_by_tenant_id_and_group_id(tenant_id, group_id)

        self.user_usecase.user_repo.find_by_tenant_id_and_group_id.assert_called_once_with(tenant_id, group_id)
        assert got == want

    def test_get_user_by_id_and_tenant_id(self, setup):
        """ユーザーIDとテナントIDによるユーザー取得テスト"""
        user_id = user_domain.Id(value=1)
        tenant_id = tenant_domain.Id(value=1)
        want = user_domain.User(
            id=user_domain.Id(value=1),
            name=user_domain.Name(value="test"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )

        self.user_usecase.user_repo.find_by_id_and_tenant_id.return_value = want

        got = self.user_usecase.get_user_by_id_and_tenant_id(user_id, tenant_id)

        self.user_usecase.user_repo.find_by_id_and_tenant_id.assert_called_once_with(user_id, tenant_id)
        assert got == want

    def test_create_user(self, setup):
        """ユーザー作成テスト"""
        tenant_id = tenant_domain.Id(value=1)
        user_for_create = user_domain.UserForCreate(
            name=user_domain.Name(value="test"),
            email=user_domain.Email(value="testcreateuser@example.com"),
            roles=[user_domain.Role.ADMIN],
        )
        auth0_user_id = "test_auth0_user_id"
        general_group_id = group_domain.Id(value=1)
        created_user_id = user_domain.Id(value=1)
        self.user_usecase.user_repo.find_by_email.return_value = None
        self.user_usecase.user_repo.find_by_tenant_id_and_email.return_value = None
        self.user_usecase.auth0_service.find_by_emails.return_value = []
        self.user_usecase.auth0_service.create_user.return_value = auth0_user_id
        self.user_usecase.user_repo.create.return_value = created_user_id
        self.user_usecase.tenant_repo.get_user_count.return_value = tenant_statistics_domain.UserCount(root=0)
        self.user_usecase.tenant_repo.get_usage_limit.return_value = tenant_domain.UsageLimit.from_optional(
            free_user_seat=50,
            additional_user_seat=10,
        )
        self.user_usecase.group_repo.find_general_group_by_tenant_id.return_value = group_domain.Group(
            id=general_group_id,
            name=group_domain.Name(value="test_tenant All"),
            created_at=group_domain.CreatedAt(value=datetime.datetime.now()),
            is_general=group_domain.IsGeneral(root=True),
        )

        self.user_usecase.create_user(tenant_id, user_for_create)

        self.user_usecase.user_repo.find_by_email.assert_called_once_with(user_for_create.email)
        self.user_usecase.user_repo.find_by_tenant_id_and_email.assert_called_once_with(
            tenant_id, user_for_create.email
        )
        self.user_usecase.auth0_service.create_user.assert_called_once_with(user_for_create.email)
        self.user_usecase.user_repo.create.assert_called_once_with(
            tenant_id=tenant_id,
            user=user_for_create,
            auth0_id=auth0_user_id,
        )
        self.user_usecase.msgraph_service.send_create_user_email.assert_called_once_with(
            name=user_for_create.name,
            email=user_for_create.email,
        )
        self.user_usecase.group_repo.find_general_group_by_tenant_id.assert_called_once_with(tenant_id)
        self.user_usecase.group_repo.add_users_to_group.assert_called_once_with(
            tenant_id=tenant_id,
            group_id=general_group_id,
            user_ids=[created_user_id],
        )

    def test_create_user_when_user_limit_reached(self, setup):
        """ユーザー数上限到達時のテスト"""
        tenant_id = tenant_domain.Id(value=1)
        user_for_create = user_domain.UserForCreate(
            name=user_domain.Name(value="test"),
            email=user_domain.Email(value="testcreateuser@example.com"),
            roles=[user_domain.Role.ADMIN],
        )

        self.user_usecase.user_repo.find_by_email.return_value = None
        self.user_usecase.user_repo.find_by_tenant_id_and_email.return_value = None
        self.user_usecase.auth0_service.find_by_emails.return_value = []

        # ユーザー数が上限に達している
        self.user_usecase.tenant_repo.get_user_count.return_value = tenant_statistics_domain.UserCount(root=10)
        self.user_usecase.tenant_repo.get_usage_limit.return_value = tenant_domain.UsageLimit.from_optional(
            free_user_seat=8, additional_user_seat=2
        )

        with pytest.raises(BadRequest, match="ユーザー数の上限に達しています"):
            self.user_usecase.create_user(tenant_id, user_for_create)

        self.user_usecase.tenant_repo.get_user_count.assert_called_once_with(tenant_id)
        self.user_usecase.tenant_repo.get_usage_limit.assert_called_once_with(tenant_id)

    def test_update_user_policy(self, setup):
        """ユーザーポリシー更新テスト"""
        tenant_id = tenant_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        bot_id = bot_domain.Id(value=1)

        self.user_usecase.user_repo.find_by_id_and_tenant_id.return_value = user_domain.User(
            id=user_id,
            name=user_domain.Name(value="test"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )
        self.user_usecase.user_repo.update_user_policy.return_value = None

        input = UpdateUserPolicyInputData(
            bot_id=bot_id,
            action=policy_domain.Action(root=policy_domain.ActionEnum.READ),
            delete=False,
        )
        self.user_usecase.update_user_policy(tenant_id, user_id, input)

        self.user_usecase.user_repo.find_by_id_and_tenant_id.assert_called_once_with(user_id, tenant_id)
        self.user_usecase.user_repo.update_user_policy.assert_called_once_with(
            user_id,
            tenant_id,
            policy_domain.Policy(
                bot_id=bot_id,
                action=policy_domain.Action(root=policy_domain.ActionEnum.READ),
            ),
        )

    def test_add_user_roles(self, setup):
        """ユーザーロール追加テスト"""
        tenant_id = tenant_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        roles = [user_domain.Role.ADMIN]

        self.user_usecase.user_repo.find_by_id_and_tenant_id.return_value = user_domain.User(
            id=user_id,
            name=user_domain.Name(value="test"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )
        self.user_usecase.user_repo.add_roles.return_value = None

        self.user_usecase.add_user_roles(tenant_id, user_id, roles)

        self.user_usecase.user_repo.find_by_id_and_tenant_id.assert_called_once_with(user_id, tenant_id)
        self.user_usecase.user_repo.add_roles.assert_called_once_with(user_id, tenant_id, roles)

    def test_delete_user_role(self, setup):
        """ユーザーロール削除テスト"""
        tenant_id = tenant_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        role = user_domain.Role.ADMIN

        self.user_usecase.user_repo.find_by_id_and_tenant_id.return_value = user_domain.User(
            id=user_id,
            name=user_domain.Name(value="test"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )
        self.user_usecase.user_repo.delete_role.return_value = None

        self.user_usecase.delete_user_role(tenant_id, user_id, role)

        self.user_usecase.user_repo.find_by_id_and_tenant_id.assert_called_once_with(user_id, tenant_id)
        self.user_usecase.user_repo.delete_role.assert_called_once_with(user_id, tenant_id, role)

    def test_delete_user_from_tenant(self, setup):
        """テナントからユーザー削除テスト"""

        tenant_id = tenant_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        email = user_domain.Email(value="test@example.com")

        self.user_usecase.user_repo.find_by_id_and_tenant_id.return_value = user_domain.User(
            id=user_id,
            name=user_domain.Name(value="test"),
            email=email,
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )
        self.user_usecase.user_repo.delete_by_id_and_tenant_id.return_value = None

        self.user_usecase.delete_user_from_tenant(tenant_id, user_id)

        self.user_usecase.user_repo.find_by_id_and_tenant_id.assert_called_once_with(user_id, tenant_id)
        self.user_usecase.user_repo.delete_by_id_and_tenant_id.assert_called_once_with(user_id, tenant_id)
        self.user_usecase.auth0_service.delete_user.assert_called_once_with(email)

    def test_update_user(self, setup):
        """ユーザー更新テスト"""
        tenant_id = tenant_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        name = user_domain.Name(value="test")

        self.user_usecase.user_repo.find_by_id_and_tenant_id.return_value = user_domain.User(
            id=user_id,
            name=user_domain.Name(value="test"),
            email=user_domain.Email(value="test@example.com"),
            roles=[user_domain.Role.ADMIN],
            policies=[],
        )
        self.user_usecase.user_repo.update.return_value = None

        self.user_usecase.update_user(tenant_id, user_id, name)

        self.user_usecase.user_repo.find_by_id_and_tenant_id.assert_called_once_with(user_id, tenant_id)
        self.user_usecase.user_repo.update.assert_called_once_with(user_id, name)

    def test_update_user_with_invalid_tenant(self, setup):
        """ユーザー更新テスト(テナントが存在しない場合)"""
        tenant_id = tenant_domain.Id(value=1)
        user_id = user_domain.Id(value=1)
        name = user_domain.Name(value="test")

        self.user_usecase.user_repo.find_by_id_and_tenant_id.side_effect = NotFound("Not Found")

        with pytest.raises(NotFound):
            self.user_usecase.update_user(tenant_id, user_id, name)

    def test_bulk_create_users(self, setup):
        """ユーザー一括作成または更新テスト"""

        input = BulkCreateUsersInputData(
            tenant_id=tenant_domain.Id(value=1),
            users=[
                UserForBulkCreateOrUpdate(
                    name=user_domain.Name(value="test"),
                    email=user_domain.Email(value="test1@example.com"),
                    roles=[user_domain.Role.ADMIN],
                    group_names=[group_domain.Name(value="test")],
                ),
                UserForBulkCreateOrUpdate(
                    name=user_domain.Name(value="test2"),
                    email=user_domain.Email(value="test2@example.com"),
                    roles=[user_domain.Role.USER],
                    group_names=[group_domain.Name(value="test")],
                ),
            ],
            file=b"test",
            filename="test.csv",
        )
        self.user_usecase.user_repo.find_by_emails.return_value = []
        self.user_usecase.auth0_service.find_by_emails.return_value = []
        self.user_usecase.group_repo.get_groups_by_tenant_id.return_value = [
            group_domain.Group(
                id=group_domain.Id(value=1),
                name=group_domain.Name(value="test"),
                created_at=group_domain.CreatedAt(value=datetime.datetime.now()),
                is_general=group_domain.IsGeneral(root=False),
            )
        ]
        self.user_usecase.blob_storage_service.upload_users_import_csv.return_value = None
        self.user_usecase.queue_storage_service.send_message_to_users_import_queue.return_value = None
        self.user_usecase.tenant_repo.get_user_count.return_value = tenant_statistics_domain.UserCount(root=0)
        self.user_usecase.tenant_repo.get_usage_limit.return_value = tenant_domain.UsageLimit.from_optional(
            free_user_seat=50,
            additional_user_seat=10,
        )

        self.user_usecase.bulk_create_users(input)

        self.user_usecase.group_repo.get_groups_by_tenant_id.assert_called_once_with(input.tenant_id)
        self.user_usecase.blob_storage_service.upload_users_import_csv.assert_called_once_with(
            file=input.file,
            filename=input.filename,
        )
        self.user_usecase.queue_storage_service.send_message_to_users_import_queue.assert_called_once_with(
            input.tenant_id,
            input.filename,
        )

    def test_bulk_create_users_group_not_found(self, setup):
        """ユーザー一括作成または更新テスト(グループが存在しない場合)"""

        input = BulkCreateUsersInputData(
            tenant_id=tenant_domain.Id(value=1),
            users=[
                UserForBulkCreateOrUpdate(
                    name=user_domain.Name(value="test"),
                    email=user_domain.Email(value="test@example.com"),
                    roles=[user_domain.Role.ADMIN],
                    group_names=[group_domain.Name(value="test")],
                ),
            ],
            file=b"test",
            filename="test.csv",
        )

        self.user_usecase.user_repo.find_by_emails.return_value = []
        self.user_usecase.auth0_service.find_by_emails.return_value = []
        self.user_usecase.tenant_repo.get_user_count.return_value = tenant_statistics_domain.UserCount(root=0)
        self.user_usecase.tenant_repo.get_usage_limit.return_value = tenant_domain.UsageLimit.from_optional(
            free_user_seat=50,
            additional_user_seat=10,
        )
        self.user_usecase.group_repo.get_groups_by_tenant_id.return_value = [
            group_domain.Group(
                id=group_domain.Id(value=1),
                name=group_domain.Name(value="test2"),
                created_at=group_domain.CreatedAt(value=datetime.datetime.now()),
                is_general=group_domain.IsGeneral(root=False),
            )
        ]

        with pytest.raises(BadRequest):
            self.user_usecase.bulk_create_users(input)

    def test_bulk_create_users_user_limit_reached(self, setup):
        """ユーザー一括作成または更新テスト(ユーザー数上限到達時)"""

        input = BulkCreateUsersInputData(
            tenant_id=tenant_domain.Id(value=1),
            users=[
                UserForBulkCreateOrUpdate(
                    name=user_domain.Name(value="test"),
                    email=user_domain.Email(value="test1@example.com"),
                    roles=[user_domain.Role.ADMIN],
                    group_names=[group_domain.Name(value="test")],
                ),
                UserForBulkCreateOrUpdate(
                    name=user_domain.Name(value="test2"),
                    email=user_domain.Email(value="test2@example.com"),
                    roles=[user_domain.Role.USER],
                    group_names=[group_domain.Name(value="test")],
                ),
            ],
            file=b"test",
            filename="test.csv",
        )
        self.user_usecase.user_repo.find_by_emails.return_value = []
        self.user_usecase.auth0_service.find_by_emails.return_value = []
        self.user_usecase.group_repo.get_groups_by_tenant_id.return_value = [
            group_domain.Group(
                id=group_domain.Id(value=1),
                name=group_domain.Name(value="test"),
                created_at=group_domain.CreatedAt(value=datetime.datetime.now()),
                is_general=group_domain.IsGeneral(root=False),
            )
        ]
        self.user_usecase.blob_storage_service.upload_users_import_csv.return_value = None
        self.user_usecase.queue_storage_service.send_message_to_users_import_queue.return_value = None
        self.user_usecase.tenant_repo.get_user_count.return_value = tenant_statistics_domain.UserCount(root=10)
        self.user_usecase.tenant_repo.get_usage_limit.return_value = tenant_domain.UsageLimit.from_optional(
            free_user_seat=7,
            additional_user_seat=2,
        )

        with pytest.raises(BadRequest, match="ユーザー数の上限に達しています"):
            self.user_usecase.bulk_create_users(input)

        self.user_usecase.tenant_repo.get_user_count.assert_called_once_with(input.tenant_id)
        self.user_usecase.tenant_repo.get_usage_limit.assert_called_once_with(input.tenant_id)

    def test_get_users_for_download(self, setup):
        """ユーザーダウンロードテスト"""
        tenant_id = tenant_domain.Id(value=1)
        want = [
            UserForDownload(
                id=user_domain.Id(value=1),
                name=user_domain.Name(value="test"),
                email=user_domain.Email(value="test@example.com"),
                roles=[user_domain.Role.ADMIN],
                group_names=[group_domain.Name(value="test")],
            ),
            UserForDownload(
                id=user_domain.Id(value=2),
                name=user_domain.Name(value="test2"),
                email=user_domain.Email(value="test2@example.com"),
                roles=[user_domain.Role.USER],
                group_names=[group_domain.Name(value="test2")],
            ),
        ]

        self.user_usecase.user_repo.get_users_with_group_ids.return_value = [
            user_domain.UserWithGroupIds(
                id=user_domain.Id(value=1),
                name=user_domain.Name(value="test"),
                email=user_domain.Email(value="test@example.com"),
                roles=[user_domain.Role.ADMIN],
                group_ids=[group_domain.Id(value=1)],
            ),
            user_domain.UserWithGroupIds(
                id=user_domain.Id(value=2),
                name=user_domain.Name(value="test2"),
                email=user_domain.Email(value="test2@example.com"),
                roles=[user_domain.Role.USER],
                group_ids=[group_domain.Id(value=2)],
            ),
        ]
        self.user_usecase.group_repo.get_groups_by_tenant_id.return_value = [
            group_domain.Group(
                id=group_domain.Id(value=1),
                name=group_domain.Name(value="test"),
                created_at=group_domain.CreatedAt(value=datetime.datetime.now()),
                is_general=group_domain.IsGeneral(root=False),
            ),
            group_domain.Group(
                id=group_domain.Id(value=2),
                name=group_domain.Name(value="test2"),
                created_at=group_domain.CreatedAt(value=datetime.datetime.now()),
                is_general=group_domain.IsGeneral(root=False),
            ),
        ]

        got = self.user_usecase.get_users_for_download(tenant_id)

        self.user_usecase.user_repo.get_users_with_group_ids.assert_called_once_with(tenant_id)
        self.user_usecase.group_repo.get_groups_by_tenant_id.assert_called_once_with(tenant_id)
        assert got.users == want

    def test_bulk_update_users(self, setup):
        """ユーザー一括更新テスト"""
        self.user_usecase.group_repo.get_groups_by_tenant_id.return_value = [
            group_domain.Group(
                id=group_domain.Id(value=1),
                name=group_domain.Name(value="general"),
                created_at=group_domain.CreatedAt(value=datetime.datetime.now()),
                is_general=group_domain.IsGeneral(root=True),
            ),
            group_domain.Group(
                id=group_domain.Id(value=2),
                name=group_domain.Name(value="test2"),
                created_at=group_domain.CreatedAt(value=datetime.datetime.now()),
                is_general=group_domain.IsGeneral(root=False),
            ),
            group_domain.Group(
                id=group_domain.Id(value=3),
                name=group_domain.Name(value="test3"),
                created_at=group_domain.CreatedAt(value=datetime.datetime.now()),
                is_general=group_domain.IsGeneral(root=False),
            ),
        ]

        # 現状
        self.user_usecase.user_repo.find_by_tenant_id_and_emails.return_value = [
            user_domain.UserWithGroupIds(
                id=user_domain.Id(value=1),
                name=user_domain.Name(value="test1"),
                email=user_domain.Email(value="test1@example.com"),
                roles=[user_domain.Role.ADMIN],
                group_ids=[group_domain.Id(value=1), group_domain.Id(value=2)],
            ),
            user_domain.UserWithGroupIds(
                id=user_domain.Id(value=2),
                name=user_domain.Name(value="test2"),
                email=user_domain.Email(value="test2@example.com"),
                roles=[user_domain.Role.ADMIN],
                group_ids=[group_domain.Id(value=1)],
            ),
        ]

        self.user_usecase.group_repo.delete_users_from_group.return_value = None
        self.user_usecase.group_repo.add_users_to_group.return_value = None
        self.user_usecase.user_repo.bulk_update.return_value = None

        # 更新対象
        input = BulkUpdateUsersInputData(
            tenant_id=tenant_domain.Id(value=1),
            users=[
                UserForBulkCreateOrUpdate(
                    name=user_domain.Name(value="test1-update"),
                    email=user_domain.Email(value="test1@example.com"),
                    roles=[user_domain.Role.ADMIN],
                    group_names=[group_domain.Name(value="general")],
                ),
                UserForBulkCreateOrUpdate(
                    name=user_domain.Name(value="test2-update"),
                    email=user_domain.Email(value="test2@example.com"),
                    roles=[user_domain.Role.USER],
                    group_names=[group_domain.Name(value="general"), group_domain.Name(value="test3")],
                ),
            ],
        )

        self.user_usecase.bulk_update_users(input)

        self.user_usecase.group_repo.get_groups_by_tenant_id.assert_called_once_with(input.tenant_id)
        self.user_usecase.user_repo.find_by_tenant_id_and_emails.assert_called_once_with(
            input.tenant_id, [user.email for user in input.users]
        )
        self.user_usecase.group_repo.delete_users_from_group.assert_has_calls(
            [
                call(
                    group_domain.Id(value=2),
                    [
                        user_domain.Id(value=1),
                    ],
                ),
            ]
        )
        self.user_usecase.group_repo.add_users_to_group.assert_has_calls(
            [
                call(
                    tenant_id=input.tenant_id,
                    group_id=group_domain.Id(value=3),
                    user_ids=[
                        user_domain.Id(value=2),
                    ],
                ),
            ]
        )
        self.user_usecase.user_repo.bulk_update.assert_called_once_with(
            tenant_id=input.tenant_id,
            users=[
                user_domain.UserForBulkUpdate(
                    id=user_domain.Id(value=1),
                    name=user_domain.Name(value="test1-update"),
                    roles=[user_domain.Role.ADMIN],
                ),
                user_domain.UserForBulkUpdate(
                    id=user_domain.Id(value=2),
                    name=user_domain.Name(value="test2-update"),
                    roles=[user_domain.Role.USER],
                ),
            ],
        )

    def test_find_administrators(self, setup):
        want = [
            user_domain.Administrator(
                id=user_domain.Id(value=1),
                name=user_domain.Name(value="test"),
                email=user_domain.Email(value="test@neoai.jp"),
                created_at=administrator_domain.CreatedAt(value=datetime.datetime.now()),
            ),
            user_domain.Administrator(
                id=user_domain.Id(value=2),
                name=user_domain.Name(value="test2"),
                email=user_domain.Email(value="test2@neoai.jp"),
                created_at=administrator_domain.CreatedAt(value=datetime.datetime.now()),
            ),
        ]
        self.user_usecase.user_repo.find_administrators.return_value = want
        administrators = self.user_usecase.get_administrators()
        self.user_usecase.user_repo.find_administrators.assert_called_once()
        assert administrators == want
