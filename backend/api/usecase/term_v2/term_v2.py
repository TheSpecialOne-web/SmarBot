from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    term as term_domain,
)
from api.libs.exceptions import BadRequest, Conflict, NotFound


class ITermUseCase(ABC):
    @abstractmethod
    def create_term(self, bot_id: bot_domain.Id, term: term_domain.TermForCreateV2) -> term_domain.TermV2:
        pass

    @abstractmethod
    def find_terms_by_bot_id(self, bot_id: bot_domain.Id) -> list[term_domain.TermV2]:
        pass

    @abstractmethod
    def find_term_by_bot_id_and_term_id(self, bot_id: bot_domain.Id, term_id: term_domain.IdV2) -> term_domain.TermV2:
        pass

    @abstractmethod
    def update_term(self, bot_id: bot_domain.Id, term_id: term_domain.IdV2, term: term_domain.TermForUpdateV2) -> None:
        pass

    @abstractmethod
    def delete_terms_by_term_ids_and_bot_id(self, bot_id: bot_domain.Id, term_ids: list[term_domain.IdV2]) -> None:
        pass


class TermUseCase(ITermUseCase):
    @inject
    def __init__(self, bot_repo: bot_domain.IBotRepository, term_repo: term_domain.ITermV2Repository) -> None:
        self.bot_repo = bot_repo
        self.term_repo = term_repo

    def create_term(self, bot_id: bot_domain.Id, term: term_domain.TermForCreateV2) -> term_domain.TermV2:
        bot = self.bot_repo.find_by_id(bot_id)

        if bot.approach == bot_domain.Approach.CHAT_GPT_DEFAULT:
            raise BadRequest("基盤モデルは用語をサポートしていません。")

        try:
            same_description_term = self.term_repo.find_by_bot_id_and_description(
                bot_id=bot_id, term_description=term.description
            )
            if same_description_term:
                raise Conflict("同一の説明を持つ用語が既に存在します")
        except NotFound:
            pass

        same_name_terms = self.term_repo.find_by_bot_id_and_name(bot_id=bot_id, term_name=term.names)
        if len(same_name_terms) > 0:
            raise Conflict("同一の用語が既に存在します")

        return self.term_repo.create(bot_id=bot_id, term=term)

    def find_terms_by_bot_id(self, bot_id: bot_domain.Id) -> list[term_domain.TermV2]:
        bot = self.bot_repo.find_by_id(bot_id)

        if bot.approach == bot_domain.Approach.CHAT_GPT_DEFAULT:
            return []

        return self.term_repo.find_by_bot_id(bot_id=bot_id)

    def find_term_by_bot_id_and_term_id(self, bot_id: bot_domain.Id, term_id: term_domain.IdV2) -> term_domain.TermV2:
        bot = self.bot_repo.find_by_id(bot_id)

        if bot.approach == bot_domain.Approach.CHAT_GPT_DEFAULT:
            raise NotFound("用語が見つかりません")

        term = self.term_repo.find_by_bot_id_and_term_id(bot_id=bot_id, term_id=term_id)
        if not term:
            raise NotFound("用語が見つかりません")

        return term

    def update_term(self, bot_id: bot_domain.Id, term_id: term_domain.IdV2, term: term_domain.TermForUpdateV2) -> None:
        try:
            same_description_term = self.term_repo.find_by_bot_id_and_description(
                bot_id=bot_id, term_description=term.description
            )
            if same_description_term and same_description_term.id != term_id:
                raise Conflict("同一の説明を持つ用語が既に存在します")
        except NotFound:
            pass

        same_name_terms = self.term_repo.find_by_bot_id_and_name(bot_id=bot_id, term_name=term.names)
        same_name_term_ids_without_target = [
            same_name_term.id for same_name_term in same_name_terms if same_name_term.id != term_id
        ]

        if len(same_name_term_ids_without_target) > 0:
            raise Conflict("同一の用語が既に存在します")

        term_to_update = self.term_repo.find_by_bot_id_and_term_id(term_id=term_id, bot_id=bot_id)
        term_to_update.update(term_for_update=term)
        self.term_repo.update(term=term_to_update)

    def delete_terms_by_term_ids_and_bot_id(self, bot_id: bot_domain.Id, term_ids: list[term_domain.IdV2]) -> None:
        bot = self.bot_repo.find_by_id(bot_id)

        if bot.approach == bot_domain.Approach.CHAT_GPT_DEFAULT:
            raise BadRequest("基盤モデルは用語をサポートしていません。")

        self.term_repo.delete_by_term_ids_and_bot_id(bot_id=bot_id, term_ids=term_ids)
