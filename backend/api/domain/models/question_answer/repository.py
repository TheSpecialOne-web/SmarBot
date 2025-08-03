from abc import ABC, abstractmethod

from ..bot import Id as BotId
from .question_answer import (
    Id,
    Question,
    QuestionAnswer,
    QuestionAnswerForCreate,
    Status,
)


class IQuestionAnswerRepository(ABC):
    @abstractmethod
    def find_by_bot_id(self, bot_id: BotId) -> list[QuestionAnswer]:
        pass

    @abstractmethod
    def find_by_id(self, id: Id, bot_id: BotId) -> QuestionAnswer:
        pass

    @abstractmethod
    def find_by_ids_and_statuses(self, ids: list[Id], bot_id: BotId, statuses: list[Status]) -> list[QuestionAnswer]:
        pass

    @abstractmethod
    def find_by_bot_id_and_question(self, bot_id: BotId, question: Question) -> QuestionAnswer:
        pass

    @abstractmethod
    def create(self, bot_id: BotId, question_answer: QuestionAnswerForCreate) -> QuestionAnswer:
        pass

    @abstractmethod
    def bulk_create(self, bot_id: BotId, question_answers: list[QuestionAnswerForCreate]) -> list[QuestionAnswer]:
        pass

    @abstractmethod
    def update(self, bot_id: BotId, question_answer: QuestionAnswer) -> None:
        pass

    @abstractmethod
    def bulk_update_status(self, ids: list[Id], bot_id: BotId, status: Status) -> None:
        pass

    @abstractmethod
    def bulk_update(self, bot_id: BotId, question_answers: list[QuestionAnswer]) -> None:
        pass

    @abstractmethod
    def delete(self, id: Id, bot_id: BotId) -> None:
        pass

    @abstractmethod
    def delete_by_bot_id(self, bot_id: BotId) -> None:
        pass

    @abstractmethod
    def hard_delete_by_bot_ids(self, bot_ids: list[BotId]) -> None:
        pass
