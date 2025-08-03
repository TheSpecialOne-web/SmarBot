from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.group import GroupRole
from api.domain.models.policy import Action, Policy
from api.domain.models.user import administrator as administrator_domain

from .administrator import Administrator
from .attachment import Attachment
from .base import BaseModel
from .conversation_export import ConversationExport
from .tenant import Tenant

if TYPE_CHECKING:
    from .chat_completion_export import ChatCompletionExport
    from .user_document import UserDocument
    from .user_group import UserGroup
    from .user_liked_bots import UserLikedBot
    from .user_policy import UserPolicy


class User(BaseModel):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    auth0_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=True)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String(255)), nullable=True)

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="users")

    attachments: Mapped[list[Attachment]] = relationship(
        "Attachment",
        back_populates="user",
    )
    documents: Mapped[list["UserDocument"]] = relationship(
        "UserDocument",
        back_populates="user",
    )

    user_groups: Mapped[list["UserGroup"]] = relationship("UserGroup", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    policies: Mapped[list["UserPolicy"]] = relationship("UserPolicy", back_populates="user")
    liked_bots: Mapped[list["UserLikedBot"]] = relationship("UserLikedBot", back_populates="user")

    administrator: Mapped[Administrator] = relationship("Administrator", back_populates="user")
    chat_completion_exports: Mapped[list["ChatCompletionExport"]] = relationship(
        "ChatCompletionExport", back_populates="creator"
    )

    conversation_exports: Mapped[list[ConversationExport]] = relationship(
        "ConversationExport", foreign_keys="ConversationExport.user_id", back_populates="user"
    )

    @classmethod
    def from_domain(
        cls,
        domain_model: user_domain.UserForCreate,
        auth0_id: str,
        tenant_id: tenant_domain.Id,
    ) -> "User":
        return cls(
            name=domain_model.name.value,
            email=domain_model.email.value,
            auth0_id=auth0_id,
            tenant_id=tenant_id.value,
            roles=[role.value for role in domain_model.roles],
        )

    def to_domain(self) -> user_domain.User:
        id = user_domain.Id(value=self.id)
        name = user_domain.Name(value=self.name)
        email = user_domain.Email(value=self.email)
        roles = self.get_roles()
        policies = [policy.to_domain() for policy in self.policies]
        return user_domain.User(
            id=id,
            name=name,
            email=email,
            roles=roles,
            policies=policies,
        )

    def to_userinfo(self) -> user_domain.UserInfo:
        id = user_domain.Id(value=self.id)
        name = user_domain.Name(value=self.name)
        email = user_domain.Email(value=self.email)
        tenant = self.tenant.to_domain()
        roles = self.get_roles()
        is_administrator = user_domain.IsAdministrator(value=self.administrator is not None)
        liked_bot_ids = [bot_domain.Id(value=liked_bot.bot_id) for liked_bot in self.liked_bots]

        return user_domain.UserInfo(
            id=id,
            name=name,
            email=email,
            tenant=tenant,
            roles=roles,
            is_administrator=is_administrator,
            liked_bot_ids=liked_bot_ids,
        )

    def to_userinfo_with_groups_and_policies(self) -> user_domain.UserInfoWithGroupsAndPolicies:
        id = user_domain.Id(value=self.id)
        name = user_domain.Name(value=self.name)
        email = user_domain.Email(value=self.email)
        tenant = self.tenant.to_domain()
        roles = self.get_roles()
        is_administrator = user_domain.IsAdministrator(value=self.administrator is not None)

        groups_for_userinfo: list[group_domain.GroupWithRole] = []

        for user_group in self.user_groups:
            groups_for_userinfo.append(
                group_domain.GroupWithRole(
                    id=group_domain.Id(value=user_group.group_id),
                    name=group_domain.Name(value=user_group.group.name),
                    created_at=group_domain.CreatedAt(value=user_group.group.created_at),
                    role=group_domain.GroupRole(user_group.role),
                    is_general=group_domain.IsGeneral(root=user_group.group.is_general),
                )
            )

        policies = self.get_policies()

        liked_bot_ids = [bot_domain.Id(value=liked_bot.bot_id) for liked_bot in self.liked_bots]

        return user_domain.UserInfoWithGroupsAndPolicies(
            id=id,
            name=name,
            email=email,
            tenant=tenant,
            roles=roles,
            policies=policies,
            is_administrator=is_administrator,
            groups=groups_for_userinfo,
            liked_bot_ids=liked_bot_ids,
        )

    def get_policies(self) -> list[Policy]:
        policy_dict: dict[int, Action] = {}

        # user_policiesから個人対ボットのポリシーを取得
        for user_policy in self.policies:
            policy_dict[user_policy.bot_id] = Action.from_str(user_policy.action)

        for user_group in self.user_groups:
            # 個人ポリシーとグループの権限によるボットに対するポリシーで強い方を採択
            action_from_group_role = GroupRole(user_group.role).to_policy_action()
            for bot in user_group.group.bots:
                current_action = policy_dict.get(bot.id)
                if current_action is None or current_action.priority < action_from_group_role.priority:
                    policy_dict[bot.id] = action_from_group_role
        return [
            Policy(
                bot_id=bot_domain.Id(value=bot_id),
                action=action,
            )
            for bot_id, action in policy_dict.items()
        ]

    def to_user_with_group_role(self, group_id: group_domain.Id) -> user_domain.UserWithGroupRole:
        id = user_domain.Id(value=self.id)
        name = user_domain.Name(value=self.name)
        email = user_domain.Email(value=self.email)
        roles = self.get_roles()
        group_role = next((ug.role for ug in self.user_groups if ug.group_id == group_id.value), None)
        if group_role is None:
            raise ValueError("Group role not found", group_id.value, self.user_groups)
        return user_domain.UserWithGroupRole(
            id=id, name=name, email=email, roles=roles, group_role=group_domain.GroupRole(group_role)
        )

    def to_user_with_group_ids(
        self,
    ) -> user_domain.UserWithGroupIds:
        id = user_domain.Id(value=self.id)
        name = user_domain.Name(value=self.name)
        email = user_domain.Email(value=self.email)
        roles = self.get_roles()
        group_ids = [
            group_domain.Id(value=user_group.group_id)
            for user_group in self.user_groups
            if user_group.user_id == self.id
        ]
        return user_domain.UserWithGroupIds(
            id=id,
            name=name,
            email=email,
            roles=roles,
            group_ids=group_ids,
        )

    def get_roles(self) -> list[user_domain.Role]:
        roles: list[user_domain.Role] = []
        if self.roles is None or len(self.roles) == 0:
            return [user_domain.Role.USER]
        for role in self.roles:
            roles.append(user_domain.Role(role))
        return roles

    def to_administrator(
        self,
    ) -> user_domain.Administrator:
        id = user_domain.Id(value=self.id)
        name = user_domain.Name(value=self.name)
        email = user_domain.Email(value=self.email)
        created_at = administrator_domain.CreatedAt(value=self.administrator.created_at)
        return user_domain.Administrator(
            id=id,
            name=name,
            email=email,
            created_at=created_at,
        )
