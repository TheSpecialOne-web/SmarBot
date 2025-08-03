from sqlalchemy import not_, or_, select
from sqlalchemy.orm import Session

from .models.user import User


def find_admin_users(session: Session, tenant_id: int, include_deleted: bool = False) -> list[User]:
    stmt = (
        select(User)
        .where(User.tenant_id == tenant_id)
        .where(User.roles.contains(["admin"]))
        .execution_options(include_deleted=include_deleted)
    )
    users = session.execute(stmt).scalars().all()
    return list(users)


def find_users_without_admin_by_tenant_id(
    session: Session, tenant_id: int, include_deleted: bool = False
) -> list[User]:
    stmt = (
        select(User)
        .where(User.tenant_id == tenant_id)
        .where(or_(User.roles.is_(None), not_(User.roles.contains(["admin"]))))
        .execution_options(include_deleted=include_deleted)
    )
    users = session.execute(stmt).scalars().all()
    return list(users)
