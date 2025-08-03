from sqlalchemy import select
from sqlalchemy.orm import Session

from libs.logging import get_logger
from libs.session import session_scope

from .models.group import Group
from .models.user_group import UserGroup

logger = get_logger(__name__)
logger.setLevel("INFO")


def create_tenant_admin_group(session: Session, tenant_id: int) -> int:
    new_group = Group(name="組織管理者グループ", tenant_id=tenant_id, is_general=False)
    session.add(new_group)
    session.flush()
    group_id = new_group.id
    session.refresh(new_group)
    logger.info(f"new_group: {group_id}")
    return group_id


def add_users_to_group(session: Session, group_id: int, user_ids: list[int], group_role: str = "group_viewer"):
    new_users_groups = [UserGroup(group_id=group_id, user_id=user_id, role=group_role) for user_id in user_ids]
    for new_user_group in new_users_groups:
        session.add(new_user_group)


def create_general_group(session: Session, tenant_id: int, tenant_name: str) -> int:
    new_group = Group(name=f"{tenant_name} All", tenant_id=tenant_id, is_general=True)
    session.add(new_group)
    session.flush()
    group_id = new_group.id
    session.refresh(new_group)
    logger.info(f"new_group: {group_id}")
    return group_id


def find_general_group_by_tenant_id(tenant_id: int) -> Group | None:
    with session_scope() as session:
        stmt = session.execute(select(Group).where(Group.tenant_id == tenant_id).where(Group.is_general.is_(True)))
        group = stmt.scalars().one_or_none()
    return group
