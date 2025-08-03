from datetime import datetime

from sqlalchemy import DateTime, event, func, orm
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    ORMExecuteState,
    Session,
    mapped_column,
)


class BaseModelWithoutDeletedAt(DeclarativeBase):
    __abstract__ = True  # SQLAlchemyにこれが抽象クラスであることを伝えます
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )


class BaseModel(BaseModelWithoutDeletedAt):
    __abstract__ = True  # SQLAlchemyにこれが抽象クラスであることを伝えます
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


@event.listens_for(Session, "do_orm_execute")
def _add_filtering_deleted_at(execute_state: ORMExecuteState):
    """
    論理削除用のwhereを自動的に適用する
    以下のようにすると、論理削除済のデータも含めて取得可能
    query(...).where(...).execution_options(include_deleted=True)
    """
    if (
        execute_state.is_select
        and not execute_state.is_column_load
        and not execute_state.is_relationship_load
        and not execute_state.execution_options.get("include_deleted", False)
    ):
        execute_state.statement = execute_state.statement.options(
            orm.with_loader_criteria(
                BaseModel,
                lambda cls: cls.deleted_at.is_(None),  # type: ignore[misc,arg-type]
                include_aliases=True,
            )
        )
