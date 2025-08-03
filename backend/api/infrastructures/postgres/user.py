from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, joinedload

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    policy as policy_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.libs.exceptions import Conflict, NotFound

from .models.administrator import Administrator
from .models.bot import Bot
from .models.group import Group
from .models.user import User
from .models.user_group import UserGroup
from .models.user_policy import UserPolicy


class UserRepository(user_domain.IUserRepository):
    def __init__(self, session: Session):
        self.session = session

    def _select_user_by_external_id(self, external_user_id: user_domain.ExternalUserId):
        return (
            select(User)
            .where(User.auth0_id == external_user_id.root)
            .where(User.tenant_id.isnot(None))
            .options(joinedload(User.tenant))
            .options(joinedload(User.administrator))
            .options(joinedload(User.liked_bots))
        )

    def _select_user_by_email(self, email: user_domain.Email):
        return (
            select(User)
            .where(User.email == email.value)
            .where(User.tenant_id.isnot(None))
            .options(joinedload(User.tenant))
            .options(joinedload(User.administrator))
            .options(joinedload(User.liked_bots))
        )

    def get_user_info_by_external_id(self, external_user_id: user_domain.ExternalUserId) -> user_domain.UserInfo:
        stmt = self._select_user_by_external_id(external_user_id)
        user = self.session.execute(stmt).scalars().first()

        if not user:
            raise NotFound("ユーザーが見つかりませんでした。")
        if not user.tenant:
            raise NotFound("ユーザーがテナントに紐づいていません。")

        return user.to_userinfo()

    def get_user_info_by_email(self, email: user_domain.Email) -> user_domain.UserInfo:
        stmt = self._select_user_by_email(email)
        user = self.session.execute(stmt).scalars().first()

        if not user:
            raise NotFound("ユーザーが見つかりませんでした。")
        if not user.tenant:
            raise NotFound("ユーザーがテナントに紐づいていません。")

        return user.to_userinfo()

    def get_user_info_with_groups_and_policies_by_external_id(
        self, external_user_id: user_domain.ExternalUserId
    ) -> user_domain.UserInfoWithGroupsAndPolicies:
        stmt = (
            self._select_user_by_external_id(external_user_id)
            .options(joinedload(User.policies))
            .options(joinedload(User.user_groups).joinedload(UserGroup.group).joinedload(Group.bots))
        )
        user = self.session.execute(stmt).scalars().first()

        if not user:
            raise NotFound("ユーザーが見つかりませんでした。")
        if not user.tenant:
            raise NotFound("ユーザーがテナントに紐づいていません。")

        return user.to_userinfo_with_groups_and_policies()

    def get_user_info_with_groups_and_policies_by_email(
        self, email: user_domain.Email
    ) -> user_domain.UserInfoWithGroupsAndPolicies:
        stmt = (
            self._select_user_by_email(email)
            .options(joinedload(User.policies))
            .options(joinedload(User.user_groups).joinedload(UserGroup.group).joinedload(Group.bots))
        )
        user = self.session.execute(stmt).scalars().first()

        if not user:
            raise NotFound("ユーザーが見つかりませんでした。")
        if not user.tenant:
            raise NotFound("ユーザーがテナントに紐づいていません。")

        return user.to_userinfo_with_groups_and_policies()

    def find_by_tenant_id(self, tenant_id: tenant_domain.Id, include_deleted: bool = False) -> list[user_domain.User]:
        users = (
            self.session.execute(
                select(User)
                .where(User.tenant_id == tenant_id.value)
                .options(joinedload(User.policies))
                .execution_options(include_deleted=include_deleted)
            )
            .unique()
            .scalars()
            .all()
        )
        return [user.to_domain() for user in users]

    def find_by_tenant_id_and_email(self, tenant_id: tenant_domain.Id, email: user_domain.Email) -> user_domain.User:
        user = (
            self.session.execute(
                select(User)
                .where(User.tenant_id == tenant_id.value)
                .where(User.email == email.value)
                .options(joinedload(User.policies))
            )
            .scalars()
            .first()
        )

        if not user:
            raise NotFound("ユーザーが見つかりませんでした。")

        return user.to_domain()

    def find_by_email(self, email: user_domain.Email) -> user_domain.User:
        user = (
            self.session.execute(select(User).where(User.email == email.value).options(joinedload(User.policies)))
            .scalars()
            .first()
        )

        if not user:
            raise NotFound("ユーザーが見つかりませんでした。")

        return user.to_domain()

    def find_by_emails(self, emails: list[user_domain.Email]) -> list[user_domain.Id]:
        users = (
            self.session.execute(select(User).where(User.email.in_([email.value for email in emails]))).scalars().all()
        )

        if not len(users) > 0:
            raise NotFound("ユーザーが見つかりませんでした。")

        return [user_domain.Id(value=user.id) for user in users]

    def find_by_id_and_tenant_id(
        self,
        user_id: user_domain.Id,
        tenant_id: tenant_domain.Id,
        include_deleted: bool = False,
    ) -> user_domain.User:
        user = (
            self.session.execute(
                select(User)
                .where(User.tenant_id == tenant_id.value)
                .where(User.id == user_id.value)
                .options(joinedload(User.policies))
                .execution_options(include_deleted=include_deleted)
            )
            .scalars()
            .first()
        )

        if not user:
            raise NotFound("ユーザーが見つかりませんでした。")

        return user.to_domain()

    def find_by_tenant_id_and_group_id(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id
    ) -> list[user_domain.UserWithGroupRole]:
        stmt = (
            select(User)
            .where(User.tenant_id == tenant_id.value)
            .join(UserGroup, User.id == UserGroup.user_id)
            .where(UserGroup.group_id == group_id.value)
            .options(joinedload(User.user_groups))
        )
        users = self.session.execute(stmt).unique().scalars().all()

        return [user.to_user_with_group_role(group_id) for user in users]

    def find_by_tenant_id_and_emails(
        self, tenant_id: tenant_domain.Id, emails: list[user_domain.Email]
    ) -> list[user_domain.UserWithGroupIds]:
        users = (
            self.session.execute(
                select(User)
                .where(User.tenant_id == tenant_id.value)
                .where(User.email.in_([email.value for email in emails]))
                .outerjoin(UserGroup, User.id == UserGroup.user_id)
                .options(joinedload(User.user_groups))
            )
            .unique()
            .scalars()
            .all()
        )
        return [user.to_user_with_group_ids() for user in users]

    def get_existing_user_ids(
        self,
        tenant_id: tenant_domain.Id,
        user_ids: list[user_domain.Id],
    ) -> list[user_domain.Id]:
        users = (
            self.session.execute(
                select(User)
                .where(User.tenant_id == tenant_id.value)
                .where(User.id.in_([user_id.value for user_id in user_ids]))
            )
            .scalars()
            .all()
        )
        existing_user_ids = list({user.id for user in users})
        return [user_domain.Id(value=user_id) for user_id in existing_user_ids]

    def get_users_with_group_ids(self, tenant_id: tenant_domain.Id) -> list[user_domain.UserWithGroupIds]:
        users = (
            self.session.execute(
                select(User)
                .where(User.tenant_id == tenant_id.value)
                .outerjoin(UserGroup, User.id == UserGroup.user_id)
                .options(joinedload(User.user_groups))
            )
            .unique()
            .scalars()
            .all()
        )

        return [user.to_user_with_group_ids() for user in users]

    def update_group_role(
        self, user_id: user_domain.Id, group_id: group_domain.Id, role: group_domain.GroupRole
    ) -> None:
        user_group = (
            self.session.execute(
                select(UserGroup).where(UserGroup.user_id == user_id.value, UserGroup.group_id == group_id.value)
            )
            .scalars()
            .first()
        )

        if not user_group:
            raise NotFound("グループ内にユーザーが見つかりませんでした。")

        user_group.role = role.value

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def create(
        self,
        tenant_id: tenant_domain.Id,
        user: user_domain.UserForCreate,
        auth0_id: str,
    ) -> user_domain.Id:
        existing_user = self.session.execute(select(User).filter_by(auth0_id=auth0_id)).scalars().first()

        if existing_user is not None:
            raise Conflict("ユーザーはすでに存在します")

        try:
            new_user = User.from_domain(domain_model=user, auth0_id=auth0_id, tenant_id=tenant_id)
            self.session.add(new_user)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        user_id = new_user.id

        return user_domain.Id(value=user_id)

    def update(self, user_id: user_domain.Id, name: user_domain.Name) -> None:
        user = self.session.execute(select(User).filter_by(id=user_id.value)).scalars().first()

        if not user:
            raise NotFound("ユーザーが見つかりませんでした。")

        try:
            user.name = name.value
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def bulk_update(self, tenant_id: tenant_domain.Id, users: list[user_domain.UserForBulkUpdate]) -> None:
        existing_users = (
            self.session.execute(
                select(User)
                .where(User.tenant_id == tenant_id.value)
                .where(User.id.in_([user.id.value for user in users]))
            )
            .scalars()
            .all()
        )
        for existing_user in existing_users:
            user = next((user for user in users if user.id.value == existing_user.id), None)
            if not user:
                continue
            existing_user.name = user.name.value
            existing_user.roles = [role.value for role in user.roles]

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_id_and_tenant_id(self, user_id: user_domain.Id, tenant_id: tenant_domain.Id) -> None:
        """userとuser_policyを削除する"""
        now = datetime.utcnow()

        user = (
            self.session.execute(select(User).filter_by(id=user_id.value, tenant_id=tenant_id.value)).scalars().first()
        )
        if user is None:
            raise NotFound("ユーザが見つかりませんでした。")

        user.deleted_at = now

        user_policies = (
            self.session.execute(select(UserPolicy).where(UserPolicy.user_id == user_id.value)).scalars().all()
        )
        for user_policy in user_policies:
            user_policy.deleted_at = now

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_tenant_id(self, tenant_id: tenant_domain.Id) -> None:
        try:
            self.session.execute(
                update(User).where(User.tenant_id == tenant_id.value).values(deleted_at=datetime.now(timezone.utc))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_tenant_id(self, tenant_id: tenant_domain.Id) -> None:
        try:
            self.session.execute(
                delete(User).where(User.tenant_id == tenant_id.value).where(User.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def add_roles(self, user_id: user_domain.Id, tenant_id: tenant_domain.Id, roles: list[user_domain.Role]) -> None:
        user = (
            self.session.execute(select(User).filter_by(id=user_id.value, tenant_id=tenant_id.value)).scalars().first()
        )

        if not user:
            raise NotFound("ユーザが見つかりませんでした。")

        user_roles = user.roles

        for role in roles:
            if role.value not in user_roles:
                user_roles.append(role.value)

        try:
            # ARRAY型のカラムを更新するために、self.session.executeを使用する
            self.session.execute(
                update(User)
                .where(User.id == user_id.value)
                .where(User.tenant_id == tenant_id.value)
                .values(roles=user_roles)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_role(self, user_id: user_domain.Id, tenant_id: tenant_domain.Id, role: user_domain.Role) -> None:
        user = (
            self.session.execute(select(User).filter_by(id=user_id.value, tenant_id=tenant_id.value)).scalars().first()
        )

        if not user:
            raise NotFound("ユーザーが見つかりませんでした")

        user_roles = user.roles

        if role.value in user_roles:
            user_roles.remove(role.value)

        try:
            # ARRAY型のカラムを更新するために、self.session.executeを使用する
            self.session.execute(
                update(User)
                .where(User.id == user_id.value)
                .where(User.tenant_id == tenant_id.value)
                .values(roles=user_roles)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_policy(
        self, user_id: user_domain.Id, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id
    ) -> policy_domain.Policy:
        user_policy = (
            self.session.execute(
                select(UserPolicy)
                .where(UserPolicy.user_id == user_id.value, UserPolicy.bot_id == bot_id.value)
                .join(Bot, Bot.id == UserPolicy.bot_id)
                .join(Group, Group.id == Bot.group_id)
                .where(Group.tenant_id == tenant_id.value)
            )
            .scalars()
            .first()
        )
        user_group = (
            self.session.execute(
                select(UserGroup)
                .where(UserGroup.user_id == user_id.value)
                .join(Group, Group.id == UserGroup.group_id)
                .join(Bot, Bot.group_id == Group.id)
                .where(Bot.id == bot_id.value)
                .where(Group.tenant_id == tenant_id.value)
            )
            .scalars()
            .first()
        )

        action_from_user_policy = policy_domain.Action.from_str(user_policy.action) if user_policy else None
        action_from_group_role = group_domain.GroupRole(user_group.role).to_policy_action() if user_group else None

        if action_from_user_policy is None and action_from_group_role is not None:
            return policy_domain.Policy(
                bot_id=bot_id,
                action=action_from_group_role,
            )
        if action_from_group_role is None and action_from_user_policy is not None:
            return policy_domain.Policy(
                bot_id=bot_id,
                action=action_from_user_policy,
            )
        if action_from_user_policy is not None and action_from_group_role is not None:
            return policy_domain.Policy(
                bot_id=bot_id,
                action=action_from_user_policy
                if action_from_user_policy.priority > action_from_group_role.priority
                else action_from_group_role,
            )
        raise NotFound("ポリシーが見つかりませんでした。")

    def find_policies(self, user_id: user_domain.Id, tenant_id: tenant_domain.Id) -> list[policy_domain.Policy]:
        stmt = (
            select(User)
            .where(User.id == user_id.value)
            .where(User.tenant_id == tenant_id.value)
            .options(joinedload(User.policies))
            .options(joinedload(User.user_groups).joinedload(UserGroup.group).joinedload(Group.bots))
        )
        user = self.session.execute(stmt).scalars().first()

        if not user:
            raise NotFound("ユーザーが見つかりませんでした。")

        return user.get_policies()

    def update_user_policy(
        self, user_id: user_domain.Id, tenant_id: tenant_domain.Id, policy: policy_domain.Policy
    ) -> None:
        user_policy = (
            self.session.execute(
                select(UserPolicy)
                .where(UserPolicy.user_id == user_id.value, UserPolicy.bot_id == policy.bot_id.value)
                # 指定されたテナントに属するボットのポリシーのみを取得する
                .join(Bot, Bot.id == UserPolicy.bot_id)
                .join(Group, Group.id == Bot.group_id)
                .where(Group.tenant_id == tenant_id.value)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .first()
        )

        if user_policy:
            user_policy.action = policy.action.to_str()
            user_policy.deleted_at = None
        else:
            try:
                user_policy = UserPolicy.from_domain(domain_model=policy, user_id=user_id)
                self.session.add(user_policy)
            except Exception as e:
                self.session.rollback()
                raise e

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_user_policy(self, user_id: user_domain.Id, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> None:
        user_policy = (
            self.session.execute(
                select(UserPolicy)
                .where(UserPolicy.user_id == user_id.value, UserPolicy.bot_id == bot_id.value)
                # 指定されたテナントに属するボットのポリシーのみを取得する
                .join(Bot, Bot.id == UserPolicy.bot_id)
                .join(Group, Group.id == Bot.group_id)
                .where(Group.tenant_id == tenant_id.value)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .first()
        )

        if user_policy:
            user_policy.deleted_at = datetime.utcnow()
        else:
            return

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_user_policy_by_bot_id(self, bot_id: bot_domain.Id) -> None:
        # 物理削除
        try:
            self.session.execute(delete(UserPolicy).where(UserPolicy.bot_id == bot_id.value))
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_admins_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[user_domain.User]:
        users = (
            self.session.execute(
                select(User).where(User.tenant_id == tenant_id.value).where(User.roles.contains({"admin"}))
            )
            .scalars()
            .all()
        )

        return [user.to_domain() for user in users]

    def find_administrators(self) -> list[user_domain.Administrator]:
        administrators = (
            self.session.execute(select(User).join(Administrator, User.id == Administrator.user_id)).scalars().all()
        )

        return [administrator.to_administrator() for administrator in administrators]

    def bulk_create_users(self, tenant_id: tenant_domain.Id, users: list[user_domain.UserForBulkCreate]) -> None:
        new_users = [
            User.from_domain(
                domain_model=user.to_user_for_create(),
                auth0_id=user.auth0_id,
                tenant_id=tenant_id,
            )
            for user in users
        ]

        try:
            self.session.add_all(new_users)
            self.session.flush()

            new_user_groups: list[UserGroup] = []
            for new_user in new_users:
                groups: list[group_domain.GroupWithRole] = next(
                    (user.groups for user in users if user.email.value == new_user.email), []
                )
                for group in groups:
                    new_user_groups.append(
                        UserGroup.from_domain(
                            user_id=user_domain.Id(value=new_user.id),
                            group_id=group.id,
                            group_role=group.role,
                        )
                    )

            self.session.add_all(new_user_groups)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
