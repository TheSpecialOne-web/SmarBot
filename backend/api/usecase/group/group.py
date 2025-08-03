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
from api.libs.exceptions import BadRequest, NotFound


class UpdateGroupPolicyInputData(BaseModel):
    bot_id: bot_domain.Id
    action: Optional[policy_domain.Action]
    delete: bool


class BotNameAndPolicy(BaseModel):
    bot_name: bot_domain.Name
    action: policy_domain.Action


class GroupForBulkCreateOrUpdate(BaseModel):
    name: group_domain.Name
    policies: list[BotNameAndPolicy]


class BulkCreateOrUpdateGroupsInputData(BaseModel):
    tenant_id: tenant_domain.Id
    groups: list[GroupForBulkCreateOrUpdate]


class GroupForDownload(BaseModel):
    id: group_domain.Id
    name: group_domain.Name
    policies: list[BotNameAndPolicy]


class GetGroupsForDownloadOutputData(BaseModel):
    groups: list[GroupForDownload]


class IGroupUseCase(ABC):
    @abstractmethod
    def get_groups_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[group_domain.Group]:
        pass

    @abstractmethod
    def get_group_by_id_and_tenant_id(
        self, group_id: group_domain.Id, tenant_id: tenant_domain.Id
    ) -> group_domain.Group:
        pass

    @abstractmethod
    def create_group(
        self, tenant_id: tenant_domain.Id, name: group_domain.Name, group_admin_user_id: user_domain.Id
    ) -> None:
        pass

    @abstractmethod
    def update_group(self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, name: group_domain.Name) -> None:
        pass

    @abstractmethod
    def delete_group(self, tenant_id: tenant_domain.Id, group_id: group_domain.Id) -> None:
        pass

    @abstractmethod
    def add_users_to_group(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, user_ids: list[user_domain.Id]
    ) -> None:
        pass

    @abstractmethod
    def delete_user_from_group(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, user_id: user_domain.Id
    ) -> None:
        pass

    @abstractmethod
    def delete_users_from_group(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, user_ids: list[user_domain.Id]
    ) -> None:
        pass

    @abstractmethod
    def update_group_role(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        user_id: user_domain.Id,
        role: group_domain.GroupRole,
    ) -> None:
        pass


class GroupUseCase(IGroupUseCase):
    @inject
    def __init__(
        self,
        group_repo: group_domain.IGroupRepository,
        user_repo: user_domain.IUserRepository,
        bot_repo: bot_domain.IBotRepository,
    ) -> None:
        self.group_repo = group_repo
        self.user_repo = user_repo
        self.bot_repo = bot_repo

    def get_groups_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[group_domain.Group]:
        return self.group_repo.get_groups_by_tenant_id(tenant_id)

    def get_group_by_id_and_tenant_id(
        self, group_id: group_domain.Id, tenant_id: tenant_domain.Id
    ) -> group_domain.Group:
        return self.group_repo.get_group_by_id_and_tenant_id(group_id, tenant_id)

    def create_group(
        self, tenant_id: tenant_domain.Id, name: group_domain.Name, group_admin_user_id: user_domain.Id
    ) -> None:
        try:
            existing_group = self.group_repo.find_by_tenant_id_and_name(tenant_id, name)
            if existing_group is not None:
                raise BadRequest("同じ名前のグループが既に存在します")
        except NotFound:
            pass

        # ユーザーがテナントに存在するか確認する
        try:
            self.user_repo.find_by_id_and_tenant_id(group_admin_user_id, tenant_id)
        except NotFound:
            raise BadRequest("ユーザーがテナントに存在しません")

        created_group = self.group_repo.create_group(tenant_id, name)
        self.group_repo.add_users_to_group(
            tenant_id, created_group.id, [group_admin_user_id], group_domain.GroupRole.GROUP_ADMIN
        )

    def update_group(self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, name: group_domain.Name) -> None:
        group = self.group_repo.get_group_by_id_and_tenant_id(group_id, tenant_id)
        if group.name == name:
            return self.group_repo.update_group(group_id, name)

        try:
            existing_group = self.group_repo.find_by_tenant_id_and_name(tenant_id, name)
            if existing_group is not None:
                raise BadRequest("同じ名前のグループが既に存在します")
        except NotFound:
            pass

        return self.group_repo.update_group(group_id, name)

    def delete_group(self, tenant_id: tenant_domain.Id, group_id: group_domain.Id) -> None:
        bots_in_group = self.bot_repo.find_by_group_id(
            tenant_id,
            group_id,
            statuses=[bot_domain.Status.ACTIVE, bot_domain.Status.ARCHIVED, bot_domain.Status.DELETING],
        )
        if len(bots_in_group) > 0:
            raise BadRequest("グループに所属するアシスタントが存在するため、グループを削除できません")

        group_to_delete = self.group_repo.get_group_by_id_and_tenant_id(group_id, tenant_id)
        if group_to_delete.is_general.root:
            raise BadRequest("Allグループは削除できません")

        self.group_repo.delete_group(tenant_id, group_id)

    def add_users_to_group(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, user_ids: list[user_domain.Id]
    ) -> None:
        existing_user_ids = self.user_repo.get_existing_user_ids(tenant_id, user_ids)
        self.group_repo.get_group_by_id_and_tenant_id(group_id, tenant_id)

        self.group_repo.add_users_to_group(
            tenant_id=tenant_id,
            group_id=group_id,
            user_ids=existing_user_ids,
        )

    def delete_user_from_group(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, user_id: user_domain.Id
    ) -> None:
        self.group_repo.get_group_by_id_and_tenant_id(group_id, tenant_id)
        self.group_repo.delete_user_from_group(group_id, user_id)

    def delete_users_from_group(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, user_ids: list[user_domain.Id]
    ) -> None:
        self.group_repo.get_group_by_id_and_tenant_id(group_id, tenant_id)
        self.group_repo.delete_users_from_group(group_id, user_ids)

    def update_group_role(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        user_id: user_domain.Id,
        role: group_domain.GroupRole,
    ) -> None:
        self.group_repo.get_group_by_id_and_tenant_id(group_id, tenant_id)
        self.user_repo.update_group_role(user_id, group_id, role)
