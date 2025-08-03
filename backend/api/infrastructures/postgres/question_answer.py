from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, class_mapper

from api.domain.models.bot import Id as BotId
from api.domain.models.question_answer import (
    Id,
    Question,
    QuestionAnswer,
    QuestionAnswerForCreate,
    Status,
)
from api.domain.models.question_answer.repository import IQuestionAnswerRepository
from api.libs.exceptions import NotFound

from .models.question_answer import QuestionAnswer as QuestionAnswerModel


class QuestionAnswerRepository(IQuestionAnswerRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_by_bot_id(self, bot_id: BotId) -> list[QuestionAnswer]:
        try:
            question_answers = (
                self.session.execute(select(QuestionAnswerModel).where(QuestionAnswerModel.bot_id == bot_id.value))
                .scalars()
                .all()
            )
        except Exception as e:
            self.session.rollback()
            raise e
        return [question_answer.to_domain() for question_answer in question_answers]

    def find_by_id(self, id: Id, bot_id: BotId) -> QuestionAnswer:
        question_answer = (
            self.session.execute(
                select(QuestionAnswerModel).where(
                    QuestionAnswerModel.id == id.root, QuestionAnswerModel.bot_id == bot_id.value
                )
            )
            .scalars()
            .first()
        )
        if question_answer is None:
            raise NotFound("指定されたFAQが見つかりませんでした。")
        return question_answer.to_domain()

    def find_by_ids_and_statuses(self, ids: list[Id], bot_id: BotId, statuses: list[Status]) -> list[QuestionAnswer]:
        try:
            question_answers = (
                self.session.execute(
                    select(QuestionAnswerModel).where(
                        QuestionAnswerModel.id.in_([id.root for id in ids]),
                        QuestionAnswerModel.bot_id == bot_id.value,
                        QuestionAnswerModel.status.in_([status.value for status in statuses]),
                    )
                )
                .scalars()
                .all()
            )
        except Exception as e:
            self.session.rollback()
            raise e
        return [question_answer.to_domain() for question_answer in question_answers]

    def find_by_bot_id_and_question(self, bot_id: BotId, question: Question) -> QuestionAnswer:
        try:
            question_answer = (
                self.session.execute(
                    select(QuestionAnswerModel).where(
                        QuestionAnswerModel.bot_id == bot_id.value, QuestionAnswerModel.question == question.root
                    )
                )
                .scalars()
                .first()
            )
            if question_answer is None:
                raise NotFound("指定されたFAQが見つかりませんでした。")
        except Exception as e:
            self.session.rollback()
            raise e
        return question_answer.to_domain()

    def create(self, bot_id: BotId, question_answer: QuestionAnswerForCreate) -> QuestionAnswer:
        try:
            question_answer_model = QuestionAnswerModel.from_domain(domain_model=question_answer, bot_id=bot_id)
            self.session.add(question_answer_model)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return question_answer_model.to_domain()

    def bulk_create(self, bot_id: BotId, question_answers: list[QuestionAnswerForCreate]) -> list[QuestionAnswer]:
        try:
            question_answer_models = [
                QuestionAnswerModel(
                    id=question_answer.id.root,
                    bot_id=bot_id.value,
                    question=question_answer.question.root,
                    answer=question_answer.answer.root,
                    status=question_answer.status,
                )
                for question_answer in question_answers
            ]
            self.session.add_all(question_answer_models)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
        return [question_answer_model.to_domain() for question_answer_model in question_answer_models]

    def update(self, bot_id: BotId, question_answer: QuestionAnswer) -> None:
        try:
            self.session.execute(
                update(QuestionAnswerModel)
                .where(QuestionAnswerModel.bot_id == bot_id.value, QuestionAnswerModel.id == question_answer.id.root)
                .values(
                    question=question_answer.question.root,
                    answer=question_answer.answer.root,
                    status=question_answer.status,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def bulk_update_status(self, ids: list[Id], bot_id: BotId, status: Status) -> None:
        try:
            self.session.execute(
                update(QuestionAnswerModel)
                .where(QuestionAnswerModel.bot_id == bot_id.value, QuestionAnswerModel.id.in_([id.root for id in ids]))
                .values(status=status)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def bulk_update(self, bot_id: BotId, question_answers: list[QuestionAnswer]) -> None:
        try:
            mappings = [
                {"id": qa.id.root, "question": qa.question.root, "answer": qa.answer.root, "status": qa.status}
                for qa in question_answers
            ]

            self.session.bulk_update_mappings(class_mapper(QuestionAnswerModel), mappings)
            self.session.commit()

        except Exception as e:
            self.session.rollback()
            raise e

    def delete(self, id: Id, bot_id: BotId) -> None:
        try:
            question_answer = (
                self.session.execute(
                    select(QuestionAnswerModel).where(
                        QuestionAnswerModel.id == id.root, QuestionAnswerModel.bot_id == bot_id.value
                    )
                )
                .scalars()
                .first()
            )
            if question_answer is None:
                raise NotFound("Q&Aが見つかりませんでした。")
            question_answer.deleted_at = datetime.utcnow()
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_bot_id(self, bot_id: BotId) -> None:
        question_answers = (
            self.session.execute(select(QuestionAnswerModel).where(QuestionAnswerModel.bot_id == bot_id.value))
            .scalars()
            .all()
        )

        now = datetime.now(timezone.utc)
        for question_answer in question_answers:
            question_answer.deleted_at = now

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_bot_ids(self, bot_ids: list[BotId]) -> None:
        bot_id_values = [bot_id.value for bot_id in bot_ids]
        try:
            self.session.execute(
                delete(QuestionAnswerModel)
                .where(QuestionAnswerModel.bot_id.in_(bot_id_values))
                .where(QuestionAnswerModel.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
