from abc import ABC, abstractmethod
from typing import Optional

from injector import inject
from pydantic import BaseModel

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    policy as policy_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.services.auth0 import IAuth0Service
from api.domain.services.blob_storage import IBlobStorageService
from api.domain.services.msgraph.msgraph import IMsgraphService
from api.domain.services.queue_storage import IQueueStorageService
from api.libs.exceptions import BadRequest, Conflict, NotFound


class UpdateUserPolicyInputData(BaseModel):
    bot_id: bot_domain.Id
    action: Optional[policy_domain.Action]
    delete: bool


# ユーザーの一括作成・更新のための入力データ
class UserForBulkCreateOrUpdate(BaseModel):
    name: user_domain.Name
    email: user_domain.Email
    roles: list[user_domain.Role]
    group_names: list[group_domain.Name]


class BulkCreateUsersInputData(BaseModel):
    tenant_id: tenant_domain.Id
    users: list[UserForBulkCreateOrUpdate]
    file: bytes
    filename: str


class BulkUpdateUsersInputData(BaseModel):
    tenant_id: tenant_domain.Id
    users: list[UserForBulkCreateOrUpdate]


class UserForDownload(user_domain.UserProps):
    roles: list[user_domain.Role]
    group_names: list[group_domain.Name]


class GetUsersForDownloadOutputData(BaseModel):
    users: list[UserForDownload]


class IUserUseCase(ABC):
    @abstractmethod
    def get_user_info(self, token: str) -> user_domain.UserInfoWithGroupsAndPolicies:
        pass

    @abstractmethod
    def get_users_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[user_domain.User]:
        pass

    @abstractmethod
    def get_users_by_tenant_id_and_group_id(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id
    ) -> list[user_domain.UserWithGroupRole]:
        pass

    @abstractmethod
    def get_user_by_id_and_tenant_id(
        self,
        user_id: user_domain.Id,
        tenant_id: tenant_domain.Id,
    ) -> user_domain.User:
        pass

    @abstractmethod
    def create_user(
        self,
        tenant_id: tenant_domain.Id,
        user_for_create: user_domain.UserForCreate,
    ) -> None:
        pass

    @abstractmethod
    def update_user_policy(
        self, tenant_id: tenant_domain.Id, user_id: user_domain.Id, input: UpdateUserPolicyInputData
    ) -> None:
        pass

    @abstractmethod
    def add_user_roles(
        self,
        tenant_id: tenant_domain.Id,
        user_id: user_domain.Id,
        roles: list[user_domain.Role],
    ) -> None:
        pass

    @abstractmethod
    def delete_user_role(
        self,
        tenant_id: tenant_domain.Id,
        user_id: user_domain.Id,
        role: user_domain.Role,
    ) -> None:
        pass

    @abstractmethod
    def delete_user_from_tenant(
        self,
        tenant_id: tenant_domain.Id,
        user_id: user_domain.Id,
    ) -> None:
        pass

    @abstractmethod
    def update_user(self, tenant_id: tenant_domain.Id, user_id: user_domain.Id, name: user_domain.Name) -> None:
        pass

    @abstractmethod
    def bulk_create_users(self, input: BulkCreateUsersInputData) -> None:
        pass

    @abstractmethod
    def bulk_update_users(self, input: BulkUpdateUsersInputData) -> None:
        pass

    @abstractmethod
    def get_users_for_download(self, tenant_id: tenant_domain.Id) -> GetUsersForDownloadOutputData:
        pass

    @abstractmethod
    def get_administrators(self) -> list[user_domain.Administrator]:
        pass


class UserUseCase(IUserUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        user_repo: user_domain.IUserRepository,
        auth0_service: IAuth0Service,
        group_repo: group_domain.IGroupRepository,
        blob_storage_service: IBlobStorageService,
        queue_storage_service: IQueueStorageService,
        msgraph_service: IMsgraphService,
    ) -> None:
        self.tenant_repo = tenant_repo
        self.user_repo = user_repo
        self.auth0_service = auth0_service
        self.group_repo = group_repo
        self.blob_storage_service = blob_storage_service
        self.queue_storage_service = queue_storage_service
        self.msgraph_service = msgraph_service

    def get_user_info(self, token: str) -> user_domain.UserInfoWithGroupsAndPolicies:
        external_user_id = self.auth0_service.validate_token(token)
        if external_user_id.is_email_connection():
            return self.user_repo.get_user_info_with_groups_and_policies_by_external_id(external_user_id)
        if external_user_id.is_entra_id():
            idp_user = self.auth0_service.find_by_id(external_user_id)
            return self.user_repo.get_user_info_with_groups_and_policies_by_email(idp_user.email)
        raise BadRequest("Invalid external_user_id")

    def get_users_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[user_domain.User]:
        return self.user_repo.find_by_tenant_id(tenant_id)

    def get_users_by_tenant_id_and_group_id(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id
    ) -> list[user_domain.UserWithGroupRole]:
        return self.user_repo.find_by_tenant_id_and_group_id(tenant_id, group_id)

    def get_user_by_id_and_tenant_id(
        self,
        user_id: user_domain.Id,
        tenant_id: tenant_domain.Id,
    ) -> user_domain.User:
        return self.user_repo.find_by_id_and_tenant_id(user_id, tenant_id)

    def create_user(
        self,
        tenant_id: tenant_domain.Id,
        user_for_create: user_domain.UserForCreate,
    ) -> None:
        try:
            user = self.user_repo.find_by_email(user_for_create.email)
            if user is not None:
                raise Conflict("ユーザーはすでに存在します")
        except NotFound:
            pass

        try:
            existing_user = self.user_repo.find_by_tenant_id_and_email(tenant_id, user_for_create.email)
            if existing_user is not None:
                raise Conflict("ユーザーはすでに存在します")
        except NotFound:
            pass

        users = self.auth0_service.find_by_emails([user_for_create.email])
        if len(users) > 0:
            raise BadRequest("ユーザーはすでに存在します")

        user_count = self.tenant_repo.get_user_count(tenant_id)
        usage_limit = self.tenant_repo.get_usage_limit(tenant_id)
        max_user_count = usage_limit.free_user_seat + usage_limit.additional_user_seat
        if user_count.root >= max_user_count:
            raise BadRequest("ユーザー数の上限に達しています")

        external_user_id = self.auth0_service.create_user(user_for_create.email)

        created_user_id = self.user_repo.create(
            tenant_id=tenant_id,
            user=user_for_create,
            auth0_id=external_user_id,
        )

        # Allグループに属させる
        general_group = self.group_repo.find_general_group_by_tenant_id(tenant_id)
        self.group_repo.add_users_to_group(tenant_id=tenant_id, group_id=general_group.id, user_ids=[created_user_id])

        # メールを送る
        self.msgraph_service.send_create_user_email(name=user_for_create.name, email=user_for_create.email)

    def update_user_policy(
        self,
        tenant_id: tenant_domain.Id,
        user_id: user_domain.Id,
        input: UpdateUserPolicyInputData,
    ) -> None:
        self.user_repo.find_by_id_and_tenant_id(user_id, tenant_id)

        if input.delete:
            self.user_repo.delete_user_policy(user_id, tenant_id, input.bot_id)
            return
        if input.action is None:
            raise BadRequest("action is required when delete is false")
        self.user_repo.update_user_policy(
            user_id,
            tenant_id,
            policy_domain.Policy(bot_id=input.bot_id, action=input.action),
        )
        return

    def add_user_roles(
        self,
        tenant_id: tenant_domain.Id,
        user_id: user_domain.Id,
        roles: list[user_domain.Role],
    ) -> None:
        self.user_repo.find_by_id_and_tenant_id(user_id, tenant_id)

        self.user_repo.add_roles(user_id, tenant_id, roles)
        return

    def delete_user_role(
        self,
        tenant_id: tenant_domain.Id,
        user_id: user_domain.Id,
        role: user_domain.Role,
    ) -> None:
        self.user_repo.find_by_id_and_tenant_id(user_id, tenant_id)

        self.user_repo.delete_role(user_id, tenant_id, role)
        return

    def delete_user_from_tenant(
        self,
        tenant_id: tenant_domain.Id,
        user_id: user_domain.Id,
    ) -> None:
        user = self.user_repo.find_by_id_and_tenant_id(user_id, tenant_id)

        self.user_repo.delete_by_id_and_tenant_id(user_id, tenant_id)

        self.auth0_service.delete_user(user.email)

    def update_user(self, tenant_id: tenant_domain.Id, user_id: user_domain.Id, name: user_domain.Name) -> None:
        # ユーザーが存在するか確認
        self.user_repo.find_by_id_and_tenant_id(user_id, tenant_id)

        self.user_repo.update(user_id, name)
        return

    def _validate_group_names(self, tenant_id: tenant_domain.Id, group_names: list[str]) -> list[group_domain.Group]:
        groups = self.group_repo.get_groups_by_tenant_id(tenant_id)
        for group_name in group_names:
            if group_name not in [group.name.value for group in groups]:
                raise BadRequest(f"存在しないグループ名が指定されています: {group_name}")
        return groups

    def bulk_create_users(self, input: BulkCreateUsersInputData) -> None:
        # すでに存在するユーザーが含まれている場合はエラー
        emails = [user.email for user in input.users]
        try:
            users_found_by_emails = self.user_repo.find_by_emails(emails)
            if len(users_found_by_emails) > 0:
                raise Conflict("すでに存在するユーザーが含まれています")
        except NotFound:
            pass

        users = self.auth0_service.find_by_emails(emails)
        if len(users) > 0:
            raise Conflict("すでに存在するユーザーが含まれています")

        user_count = self.tenant_repo.get_user_count(input.tenant_id)
        usage_limit = self.tenant_repo.get_usage_limit(input.tenant_id)
        max_user_count = usage_limit.free_user_seat + usage_limit.additional_user_seat
        if user_count.root + len(input.users) > max_user_count:
            raise BadRequest("ユーザー数の上限に達しています")

        group_names: list[str] = []
        for user in input.users:
            group_names.extend([group_name.value for group_name in user.group_names])

        self._validate_group_names(input.tenant_id, group_names)

        self.blob_storage_service.upload_users_import_csv(
            file=input.file,
            filename=input.filename,
        )

        self.queue_storage_service.send_message_to_users_import_queue(input.tenant_id, input.filename)

    def _get_user_ids_to_delete_from_group(
        self,
        group: group_domain.Group,
        current_users: list[user_domain.UserWithGroupIds],
        input_users: list[UserForBulkCreateOrUpdate],
    ) -> list[user_domain.Id]:
        user_ids_to_delete_from_group = []
        for current_user in current_users:
            # 既存ユーザーがグループに所属していない場合はスキップ
            if group.id.value not in [group_id.value for group_id in current_user.group_ids]:
                continue

            # 既存ユーザーがグループに所属しているが、入力データにグループが含まれていない場合は削除対象
            input_user = next((user for user in input_users if user.email.value == current_user.email.value), None)
            if not input_user:
                continue
            if group.name.value not in [group_name.value for group_name in input_user.group_names]:
                user_ids_to_delete_from_group.append(current_user.id)
        return user_ids_to_delete_from_group

    def _get_user_ids_to_add_to_group(
        self,
        group: group_domain.Group,
        current_users: list[user_domain.UserWithGroupIds],
        input_users: list[UserForBulkCreateOrUpdate],
    ) -> list[user_domain.Id]:
        user_ids_to_add_to_group = []
        for current_user in current_users:
            # 既存ユーザーがグループに所属している場合はスキップ
            if group.id.value in [group_id.value for group_id in current_user.group_ids]:
                continue

            # 既存ユーザーがグループに所属していないが、入力データにグループが含まれている場合は追加対象
            input_user = next((user for user in input_users if user.email.value == current_user.email.value), None)
            if not input_user:
                continue
            if group.name.value in [group_name.value for group_name in input_user.group_names]:
                user_ids_to_add_to_group.append(current_user.id)
        return user_ids_to_add_to_group

    def bulk_update_users(self, input: BulkUpdateUsersInputData) -> None:
        group_names: list[str] = []
        for user in input.users:
            group_names.extend([group_name.value for group_name in user.group_names])
        groups = self._validate_group_names(input.tenant_id, group_names)

        current_users = self.user_repo.find_by_tenant_id_and_emails(
            input.tenant_id, [user.email for user in input.users]
        )

        # グループごとにユーザーの追加・削除を行う
        for group in groups:
            user_ids_to_delete = self._get_user_ids_to_delete_from_group(group, current_users, input.users)
            if len(user_ids_to_delete) > 0:
                if group.is_general.root:
                    raise BadRequest("Allグループからユーザーを削除することはできません")
                self.group_repo.delete_users_from_group(group.id, user_ids_to_delete)

            user_ids_to_add = self._get_user_ids_to_add_to_group(group, current_users, input.users)
            if len(user_ids_to_add) > 0:
                self.group_repo.add_users_to_group(
                    tenant_id=input.tenant_id, group_id=group.id, user_ids=user_ids_to_add
                )

        # ユーザー情報の一括更新
        users_for_bulk_update: list[user_domain.UserForBulkUpdate] = []
        for current_user in current_users:
            input_user = next((user for user in input.users if user.email.value == current_user.email.value), None)
            if not input_user:
                continue
            users_for_bulk_update.append(
                user_domain.UserForBulkUpdate(
                    id=current_user.id,
                    name=input_user.name,
                    roles=input_user.roles,
                )
            )
        if len(users_for_bulk_update) > 0:
            self.user_repo.bulk_update(tenant_id=input.tenant_id, users=users_for_bulk_update)

    def get_users_for_download(self, tenant_id: tenant_domain.Id) -> GetUsersForDownloadOutputData:
        users = self.user_repo.get_users_with_group_ids(tenant_id)
        groups = self.group_repo.get_groups_by_tenant_id(tenant_id)

        # グループIDからグループ名への変換用辞書
        group_dict = {}
        for group in groups:
            group_dict[group.id.value] = group.name

        users_for_download: list[UserForDownload] = []
        for user in users:
            group_names = [group_dict[group_id.value] for group_id in user.group_ids if group_id.value in group_dict]
            users_for_download.append(
                UserForDownload(
                    id=user.id,
                    name=user.name,
                    email=user.email,
                    roles=user.roles,
                    group_names=group_names,
                )
            )
        return GetUsersForDownloadOutputData(users=users_for_download)

    def get_administrators(self) -> list[user_domain.Administrator]:
        return self.user_repo.find_administrators()
