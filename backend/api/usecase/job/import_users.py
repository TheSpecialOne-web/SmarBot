from abc import ABC, abstractmethod
import os

from injector import inject
import pandas as pd
from pydantic import BaseModel

from api.domain.models import (
    document as document_domain,
    group as group_domain,
    storage as storage_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.services.auth0 import IAuth0Service
from api.domain.services.blob_storage import IBlobStorageService
from api.libs.csv import get_decoded_csv_file
from api.libs.logging import get_logger

CONTAINER_NAME = os.environ.get("AZURE_BLOB_STORAGE_USERS_IMPORT_CONTAINER") or "users-import-container"


class BulkCreateUserInput(BaseModel):
    name: user_domain.Name
    email: user_domain.Email
    roles: list[user_domain.Role]
    group_names: list[group_domain.Name]


class IImportUsersUseCase(ABC):
    @abstractmethod
    def import_users(self, tenant_id: tenant_domain.Id, filename: storage_domain.BlobName) -> None:
        pass


class ImportUsersUseCase(IImportUsersUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        group_repo: group_domain.IGroupRepository,
        user_repo: user_domain.IUserRepository,
        blob_storage_service: IBlobStorageService,
        auth0_service: IAuth0Service,
    ):
        self.logger = get_logger()
        self.tenant_repo = tenant_repo
        self.group_repo = group_repo
        self.user_repo = user_repo
        self.blob_storage_service = blob_storage_service
        self.auth0_service = auth0_service

    def import_users(self, tenant_id: tenant_domain.Id, filename: storage_domain.BlobName) -> None:
        self.logger.info(f"Start process import_users with tenant_id: {tenant_id}, filename: {filename}")
        tenant = self.tenant_repo.find_by_id(tenant_id)

        # get csv from blob_storage
        csv = self.blob_storage_service.get_csv_from_blob_storage(
            container_name=storage_domain.ContainerName(root=CONTAINER_NAME),
            blob_name=document_domain.BlobName(value=filename.root),
        )
        input_users = self._get_users_from_csv(csv)

        # テナントのグループを取得
        groups = self.group_repo.get_groups_by_tenant_id(tenant_id)
        general_group = self.group_repo.find_general_group_by_tenant_id(tenant_id)

        existing_users = self.user_repo.find_by_tenant_id_and_emails(
            tenant_id=tenant.id, emails=[user.email for user in input_users]
        )
        # 入力されたユーザーから、既存ユーザーを除外
        new_users: list[BulkCreateUserInput] = []
        for input_user in input_users:
            if input_user.email not in [existing_user.email for existing_user in existing_users]:
                new_users.append(input_user)

        # Auth0 にユーザーが存在するかを確認
        auth0_users = self.auth0_service.find_by_emails(
            emails=[user.email for user in new_users],
        )

        # Auth0 にユーザーを作成
        auth0_emails = {auth0_user.email.value for auth0_user in auth0_users}

        new_emails = [user.email for user in new_users if user.email.value not in auth0_emails]

        if len(new_emails) > 0:
            new_auth0_users = self.auth0_service.bulk_create_auth0_users(emails=new_emails)
            auth0_users.extend(new_auth0_users)

        # DB にユーザーを作成
        users_for_bulk_create: list[user_domain.UserForBulkCreate] = []
        existing_emails = {user.email.value for user in existing_users}
        auth0_map = {auth0_user.email.value: auth0_user.id for auth0_user in auth0_users}

        for user in new_users:
            if user.email.value in existing_emails:
                continue

            auth0_id = auth0_map.get(user.email.value)
            if not auth0_id:
                self.logger.warning(f"auth0_id not found for user: {user.email}")
                continue

            user_groups = [
                group_domain.GroupWithRole(
                    id=general_group.id,
                    name=general_group.name,
                    created_at=general_group.created_at,
                    is_general=general_group.is_general,
                    role=group_domain.GroupRole.GROUP_VIEWER,
                )
            ] + [
                group_domain.GroupWithRole(
                    id=group.id,
                    name=group.name,
                    created_at=group.created_at,
                    is_general=group.is_general,
                    role=group_domain.GroupRole.GROUP_VIEWER,
                )
                for group in groups
                if group.name in user.group_names and not group.is_general.root
            ]
            users_for_bulk_create.append(
                user_domain.UserForBulkCreate(
                    name=user.name,
                    tenant_id=tenant_id,
                    email=user.email,
                    auth0_id=auth0_id.root,
                    groups=user_groups,
                    roles=user.roles,
                )
            )

        if len(users_for_bulk_create) > 0:
            self.user_repo.bulk_create_users(tenant_id, users_for_bulk_create)

        self.logger.info(f"Completed process import_users with tenant_id: {tenant_id}, filename: {filename}")

    def _get_users_from_csv(self, file: bytes) -> list[BulkCreateUserInput]:
        df = self._process_csv_file(file=file)
        users: list[BulkCreateUserInput] = []
        for _, row in df.iterrows():
            group_names: list[group_domain.Name] = []
            for i in range(1, 101):
                try:
                    group_name = row[f"グループ{i}"]
                except KeyError:
                    break
                if pd.notna(group_name) and str(group_name) != "":
                    group_names.append(group_domain.Name(value=group_name))
            users.append(
                BulkCreateUserInput(
                    name=user_domain.Name(value=row["名前"]),
                    email=user_domain.Email(row["メールアドレス"]),
                    roles=[user_domain.Role.from_japanese(row["役割"])],
                    group_names=group_names,
                )
            )

        return users

    def _process_csv_file(self, file: bytes):
        allowed_columns = [
            "名前",
            "メールアドレス",
            "役割",
        ]
        for i in range(1, 101):
            allowed_columns.append(f"グループ{i}")

        df = get_decoded_csv_file(file)

        if not all(col in allowed_columns for col in df.columns):
            raise Exception("Invalid columns in CSV file.")

        return df
