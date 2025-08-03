from sqlalchemy import select
from sqlalchemy.orm import Session

from .models.bot import Bot

BASIC_AI_APPROACHES = ["chat_gpt_default", "text_2_image"]


def get_bots() -> list[Bot]:
    with Session() as session:
        bots = session.execute(select(Bot).execution_options(include_deleted=True)).scalars().all()
        return list(bots)


def find_bots_without_basic_ai(
    session: Session,
    tenant_id: int,
    include_deleted: bool = False,
) -> list[Bot]:
    bots = (
        session.execute(
            select(Bot)
            .where(Bot.tenant_id == tenant_id)
            .where(Bot.approach.notin_(BASIC_AI_APPROACHES))
            .execution_options(include_deleted=include_deleted)
        )
        .scalars()
        .all()
    )
    return list(bots)


def find_basic_ais(
    session: Session,
    tenant_id: int,
    include_deleted: bool = False,
) -> list[Bot]:
    bots = (
        session.execute(
            select(Bot)
            .where(Bot.tenant_id == tenant_id)
            .where(Bot.approach.in_(BASIC_AI_APPROACHES))
            .execution_options(include_deleted=include_deleted)
        )
        .scalars()
        .all()
    )
    return list(bots)


def add_bots_to_group(session: Session, group_id: int, bots: list[Bot]):
    bots_to_add: list[Bot] = []
    for bot in bots:
        bot.group_id = group_id
        bots_to_add.append(bot)
    session.add_all(bots_to_add)
