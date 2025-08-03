from datetime import datetime
from unittest.mock import MagicMock

import pytest

from api.domain.models import (
    group as group_domain,
    storage as storage_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm import AllowForeignRegion, BasicAiPdfParser, ModelFamily
from api.domain.models.search import Endpoint, IndexName
from api.domain.models.storage import ContainerName
from api.infrastructures.auth0.auth0 import IAuth0Service
from api.infrastructures.blob_storage.blob_storage import IBlobStorageService
from api.usecase.job.import_users import BulkCreateUserInput, ImportUsersUseCase


class TestJobCImportUsersUseCase:
    @pytest.fixture
    def setup(self):
        self.tenant_repo_mock = MagicMock(spec=tenant_domain.ITenantRepository)
        self.group_repo_mock = MagicMock(spec=group_domain.IGroupRepository)
        self.user_repo_mock = MagicMock(spec=user_domain.IUserRepository)
        self.blob_storage_service_mock = MagicMock(spec=IBlobStorageService)
        self.auth0_service_mock = MagicMock(spec=IAuth0Service)

        self.use_case = ImportUsersUseCase(
            self.tenant_repo_mock,
            self.group_repo_mock,
            self.user_repo_mock,
            self.blob_storage_service_mock,
            self.auth0_service_mock,
        )

        # Mock data
        self.tenant_id = tenant_domain.Id(value=1)
        self.tenant = tenant_domain.Tenant(
            id=tenant_domain.Id(value=1),
            name=tenant_domain.Name(value="test"),
            status=tenant_domain.Status.TRIAL,
            allowed_ips=tenant_domain.AllowedIPs(root=[]),
            alias=tenant_domain.Alias(root="test-alias"),
            search_service_endpoint=Endpoint(root="https://test-search-service-endpoint.com"),
            index_name=IndexName(root="test"),
            is_sensitive_masked=tenant_domain.IsSensitiveMasked(root=False),
            allow_foreign_region=AllowForeignRegion(root=False),
            additional_platforms=tenant_domain.AdditionalPlatformList(root=[]),
            enable_document_intelligence=tenant_domain.EnableDocumentIntelligence(root=True),
            enable_url_scraping=tenant_domain.EnableUrlScraping(root=False),
            enable_llm_document_reader=tenant_domain.EnableLLMDocumentReader(root=False),
            usage_limit=tenant_domain.UsageLimit.from_optional(),
            container_name=ContainerName(root="test"),
            enable_api_integrations=tenant_domain.EnableApiIntegrations(root=False),
            enable_basic_ai_web_browsing=tenant_domain.EnableBasicAiWebBrowsing(root=True),
            basic_ai_pdf_parser=BasicAiPdfParser.PYPDF,
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=8000),
            allowed_model_families=[ModelFamily.GPT_35_TURBO],
            basic_ai_max_conversation_turns=tenant_domain.BasicAiMaxConversationTurns(root=5),
            enable_external_data_integrations=tenant_domain.EnableExternalDataIntegrations(root=False),
        )

        self.group = group_domain.Group(
            id=group_domain.Id(value=1),
            name=group_domain.Name(value="test"),
            created_at=group_domain.CreatedAt(value=datetime.now()),
            is_general=group_domain.IsGeneral(root=False),
        )
        self.general_group = group_domain.Group(
            id=group_domain.Id(value=2),
            name=group_domain.Name(value="general"),
            created_at=group_domain.CreatedAt(value=datetime.now()),
            is_general=group_domain.IsGeneral(root=True),
        )
        self.user_with_group_ids = [
            user_domain.UserWithGroupIds(
                id=user_domain.Id(value=1),
                name=user_domain.Name(value="test1"),
                email=user_domain.Email(value="test1@example.com"),
                roles=[user_domain.Role.ADMIN],
                group_ids=[group_domain.Id(value=2)],
            ),
            user_domain.UserWithGroupIds(
                id=user_domain.Id(value=2),
                name=user_domain.Name(value="test2"),
                email=user_domain.Email(value="test2@example.com"),
                roles=[user_domain.Role.ADMIN],
                group_ids=[group_domain.Id(value=1)],
            ),
        ]
        self.auth0_users = [
            user_domain.IdpUser.from_id_and_email(id="email|1", email="test1@example.com"),
            user_domain.IdpUser.from_id_and_email(id="email|2", email="test2@example.com"),
        ]

    def test_import_user_success(self, setup):
        self.tenant_repo_mock.find_by_id.return_value = self.tenant
        self.blob_storage_service_mock.get_csv_from_blob_storage.return_value = b"mock_csv_file"
        self.use_case._get_users_from_csv = MagicMock()
        self.use_case._get_users_from_csv.return_value = [
            BulkCreateUserInput(
                name=user.name,
                email=user.email,
                roles=user.roles,
                group_names=[self.group.name],
            )
            for user in self.user_with_group_ids
        ]
        self.group_repo_mock.get_groups_by_tenant_id.return_value = [self.group]
        self.group_repo_mock.find_general_group_by_tenant_id.return_value = self.general_group
        self.user_repo_mock.find_by_tenant_id_and_emails.return_value = []
        self.auth0_service_mock.find_by_emails.return_value = []
        self.auth0_service_mock.bulk_create_auth0_users.return_value = self.auth0_users

        self.use_case.import_users(self.tenant_id, storage_domain.BlobName(root="test.csv"))

        self.tenant_repo_mock.find_by_id.assert_called_once_with(self.tenant_id)
        self.auth0_service_mock.bulk_create_auth0_users.assert_called_once_with(
            emails=[user.email for user in self.user_with_group_ids]
        )
        self.user_repo_mock.bulk_create_users.assert_called_once_with(
            self.tenant_id,
            [
                user_domain.UserForBulkCreate(
                    name=user.name,
                    tenant_id=self.tenant_id,
                    email=user.email,
                    roles=user.roles,
                    auth0_id=auth0_user.id.root,
                    groups=[
                        group_domain.GroupWithRole(
                            id=self.general_group.id,
                            name=self.general_group.name,
                            created_at=self.general_group.created_at,
                            is_general=self.general_group.is_general,
                            role=group_domain.GroupRole.GROUP_VIEWER,
                        ),
                        group_domain.GroupWithRole(
                            id=self.group.id,
                            name=self.group.name,
                            created_at=self.group.created_at,
                            is_general=self.group.is_general,
                            role=group_domain.GroupRole.GROUP_VIEWER,
                        ),
                    ],
                )
                for user, auth0_user in zip(self.user_with_group_ids, self.auth0_users)
            ],
        )
