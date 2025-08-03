from datetime import datetime, timezone
from typing import List

from sqlalchemy import delete, select, update
from sqlalchemy.orm.session import Session

from api.domain.models import (
    group as group_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.group import GroupRole
from api.libs.exceptions import NotFound

from .models.group import Group
from .models.user import User
from .models.user_group import UserGroup


class GroupRepository(group_domain.IGroupRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_groups_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[group_domain.Group]:
        # Groupと関連するGroupPolicy、UserGroupを事前にロード
        groups = self.session.execute(select(Group).where(Group.tenant_id == tenant_id.value)).unique().scalars().all()
        return [group.to_domain() for group in groups]

    def get_group_by_id_and_tenant_id(
        self, group_id: group_domain.Id, tenant_id: tenant_domain.Id
    ) -> group_domain.Group:
        # Groupと関連するGroupPolicy、UserGroupを事前にロード
        group = (
            self.session.execute(select(Group).where(Group.id == group_id.value, Group.tenant_id == tenant_id.value))
            .unique()
            .scalars()
            .first()
        )
        if not group:
            raise NotFound("グループが見つかりませんでした。")
        return group.to_domain()

    def create_group(
        self,
        tenant_id: tenant_domain.Id,
        name: group_domain.Name,
        is_general: group_domain.IsGeneral | None = None,
    ) -> group_domain.Group:
        try:
            group = Group.from_domain(
                name=name,
                tenant_id=tenant_id,
                is_general=is_general if is_general is not None else group_domain.IsGeneral(root=False),
            )
            self.session.add(group)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return group.to_domain()

    def update_group(self, group_id: group_domain.Id, name: group_domain.Name):
        group = self.session.execute(select(Group).where(Group.id == group_id.value)).scalars().first()
        if not group:
            raise NotFound("グループが見つかりませんでした。")
        try:
            group.name = name.value
            self.session.add(group)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return group

    def delete_group(self, tenant_id: tenant_domain.Id, group_id: group_domain.Id):
        try:
            # Groupを取得
            group = (
                self.session.execute(
                    select(Group).where(Group.id == group_id.value, Group.tenant_id == tenant_id.value)
                )
                .scalars()
                .first()
            )
            if not group:
                raise NotFound("グループが見つかりませんでした。")

            # Groupを論理削除
            group.deleted_at = datetime.utcnow()

            self._delete_group_users_by_group_id(
                self.session,
                group_id,
            )

            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_tenant_id(self, tenant_id: tenant_domain.Id):
        try:
            self.session.execute(
                update(Group).where(Group.tenant_id == tenant_id.value).values(deleted_at=datetime.now(timezone.utc))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_tenant_id(self, tenant_id: tenant_domain.Id):
        try:
            self.session.execute(
                delete(Group).where(Group.tenant_id == tenant_id.value).where(Group.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def add_users_to_group(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        user_ids: list[user_domain.Id],
        group_role: GroupRole = GroupRole.GROUP_VIEWER,
    ):
        try:
            existing_group_users = (
                self.session.execute(
                    select(UserGroup)
                    .where(
                        UserGroup.group_id == group_id.value,
                        UserGroup.user_id.in_([user_id.value for user_id in user_ids]),
                    )
                    .join(Group, Group.id == UserGroup.group_id)
                    .where(Group.tenant_id == tenant_id.value)
                )
                .scalars()
                .all()
            )

            existing_user_ids = [group_user.user_id for group_user in existing_group_users]

            user_groups_to_add: list[UserGroup] = []

            for user_id in user_ids:
                if user_id.value in existing_user_ids:
                    continue
                user_groups_to_add.append(
                    UserGroup.from_domain(user_id=user_id, group_id=group_id, group_role=group_role)
                )

            self.session.add_all(user_groups_to_add)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_user_from_group(self, group_id: group_domain.Id, user_id: user_domain.Id):
        try:
            user_to_delete = (
                self.session.execute(
                    select(UserGroup).where(UserGroup.group_id == group_id.value, UserGroup.user_id == user_id.value)
                )
                .scalars()
                .first()
            )

            if not user_to_delete:
                raise NotFound("ユーザーが見つかりませんでした。")

            self.session.delete(user_to_delete)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_users_from_group(self, group_id: group_domain.Id, user_ids: List[user_domain.Id]):
        try:
            users_to_delete = (
                self.session.execute(
                    select(UserGroup).where(
                        UserGroup.group_id == group_id.value,
                        UserGroup.user_id.in_([user_id.value for user_id in user_ids]),
                    )
                )
                .scalars()
                .all()
            )

            for user in users_to_delete:
                self.session.delete(user)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def _delete_group_users_by_group_id(self, session: Session, group_id: group_domain.Id):
        user_groups = session.execute(select(UserGroup).where(UserGroup.group_id == group_id.value)).scalars().all()

        if not user_groups:
            return

        for user_group in user_groups:
            session.delete(user_group)

    def find_by_tenant_id_and_name(self, tenant_id: tenant_domain.Id, name: group_domain.Name) -> group_domain.Group:
        group = (
            self.session.execute(select(Group).where(Group.tenant_id == tenant_id.value, Group.name == name.value))
            .unique()
            .scalars()
            .first()
        )
        if not group:
            raise NotFound("グループが見つかりませんでした。")
        return group.to_domain()

    def get_group_role_by_user_id_and_group_id_and_tenant_id(
        self, user_id: user_domain.Id, group_id: group_domain.Id, tenant_id: tenant_domain.Id
    ) -> GroupRole:
        user_group = self.session.execute(
            select(UserGroup)
            .join(Group, Group.id == UserGroup.group_id)
            .join(User, User.id == UserGroup.user_id)
            .where(
                UserGroup.user_id == user_id.value,
                UserGroup.group_id == group_id.value,
                Group.tenant_id == tenant_id.value,
                User.tenant_id == tenant_id.value,
            )
        ).scalar()

        if not user_group:
            raise NotFound("グループが見つかりませんでした。")

        return GroupRole.from_str(user_group.role)

    def find_general_group_by_tenant_id(self, tenant_id: tenant_domain.Id):
        group = (
            self.session.execute(select(Group).where(Group.tenant_id == tenant_id.value, Group.is_general.is_(True)))
            .scalars()
            .first()
        )
        if not group:
            raise NotFound("グループが見つかりませんでした。")
        return group.to_domain()

    def get_has_any_group_admin_by_user_id_and_tenant_id(
        self, user_id: user_domain.Id, tenant_id: tenant_domain.Id
    ) -> bool:
        user_groups = (
            self.session.execute(
                select(UserGroup)
                .join(Group, Group.id == UserGroup.group_id)
                .join(User, User.id == UserGroup.user_id)
                .where(
                    UserGroup.user_id == user_id.value,
                    Group.tenant_id == tenant_id.value,
                    User.tenant_id == tenant_id.value,
                    UserGroup.role == GroupRole.GROUP_ADMIN.value,
                )
            )
            .scalars()
            .all()
        )

        return len(list(user_groups)) > 0

    def find_by_tenant_id_and_user_id(
        self, tenant_id: tenant_domain.Id, user_id: user_domain.Id
    ) -> list[group_domain.Group]:
        groups = (
            self.session.execute(
                select(Group)
                .join(UserGroup, UserGroup.group_id == Group.id)
                .join(User, User.id == UserGroup.user_id)
                .where(Group.tenant_id == tenant_id.value, User.id == user_id.value)
            )
            .scalars()
            .all()
        )
        return [group.to_domain() for group in groups]
