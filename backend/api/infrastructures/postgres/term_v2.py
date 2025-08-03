from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from api.domain.models import (
    bot as bot_domain,
    term as term_domain,
)
from api.libs.exceptions import NotFound

from .models.term_v2 import TermV2


class TermV2Repository(term_domain.ITermV2Repository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, bot_id: bot_domain.Id, term: term_domain.TermForCreateV2) -> term_domain.TermV2:
        try:
            new_term = TermV2.from_domain(
                domain_model=term,
                bot_id=bot_id,
            )
            self.session.add(new_term)
            self.session.commit()
            return new_term.to_domain()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_by_bot_id(self, bot_id: bot_domain.Id) -> list[term_domain.TermV2]:
        terms = self.session.execute(select(TermV2).where(TermV2.bot_id == bot_id.value)).scalars().all()
        return [term.to_domain() for term in terms]

    def find_by_bot_id_and_description(
        self, bot_id: bot_domain.Id, term_description: term_domain.DescriptionV2
    ) -> term_domain.TermV2:
        term = self.session.execute(
            select(TermV2).where(TermV2.bot_id == bot_id.value).where(TermV2.description == term_description.root)
        ).scalar()
        if not term:
            raise NotFound("同一の説明を持つ用語が見つかりませんでした")
        return term.to_domain()

    def find_by_bot_id_and_name(
        self,
        bot_id: bot_domain.Id,
        term_name: list[term_domain.NameV2],
    ) -> list[term_domain.TermV2]:
        term_names = [name.root for name in term_name]
        terms = (
            self.session.execute(
                select(TermV2).where(TermV2.bot_id == bot_id.value).where(TermV2.names.op("&&")(term_names))
            )
            .scalars()
            .all()
        )
        return [term.to_domain() for term in terms]

    def find_by_bot_id_and_term_id(self, bot_id: bot_domain.Id, term_id: term_domain.IdV2) -> term_domain.TermV2:
        term = self.session.execute(
            select(TermV2).where(TermV2.bot_id == bot_id.value).where(TermV2.id == term_id.root)
        ).scalar()
        if not term:
            raise NotFound("指定された用語が見つかりませんでした")
        return term.to_domain()

    def update(self, term: term_domain.TermV2) -> None:
        try:
            self.session.execute(
                update(TermV2)
                .where(TermV2.id == term.id.root)
                .values(
                    names=[name.root for name in term.names],
                    description=term.description.root,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_term_ids_and_bot_id(self, bot_id: bot_domain.Id, term_ids: list[term_domain.IdV2]) -> None:
        now = datetime.utcnow()
        terms = (
            self.session.execute(
                select(TermV2)
                .where(TermV2.bot_id == bot_id.value)
                .where(TermV2.id.in_([term_id.root for term_id in term_ids]))
            )
            .scalars()
            .all()
        )

        if len(terms) == 0:
            raise NotFound("指定された用語が見つかりませんでした")
        for term in terms:
            term.deleted_at = now
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_bot_id(self, bot_id: bot_domain.Id) -> None:
        terms = self.session.execute(select(TermV2).where(TermV2.bot_id == bot_id.value)).scalars().all()

        now = datetime.now(timezone.utc)
        for term in terms:
            term.deleted_at = now

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_bot_ids(self, bot_ids: list[bot_domain.Id]) -> None:
        bot_id_values = [bot_id.value for bot_id in bot_ids]
        try:
            self.session.execute(
                delete(TermV2).where(TermV2.bot_id.in_(bot_id_values)).where(TermV2.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
