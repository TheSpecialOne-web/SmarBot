from typing import Tuple

import pytest
from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import (
    bot as bot_domain,
    question_answer as question_answer_domain,
)
from api.domain.models.question_answer.question_answer import QuestionAnswerForCreate
from api.infrastructures.postgres.models.question_answer import QuestionAnswer
from api.infrastructures.postgres.question_answer import QuestionAnswerRepository
from tests.conftest import BotsSeed

QuestionAnswerSeed = Tuple[bot_domain.Id, list[question_answer_domain.QuestionAnswer]]


class TestQuestionAnswer:
    def setup_method(self):
        self.session = SessionFactory()
        self.question_answer_repo = QuestionAnswerRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_find_by_bot_id(
        self, question_answer_seed: Tuple[bot_domain.Id, list[question_answer_domain.QuestionAnswer]]
    ):
        bot_id, question_answers = question_answer_seed
        got = self.question_answer_repo.find_by_bot_id(
            bot_id=bot_id,
        )
        assert got == question_answers

    def test_find_by_id(self, question_answer_seed: Tuple[bot_domain.Id, list[question_answer_domain.QuestionAnswer]]):
        bot_id, question_answers = question_answer_seed
        want = question_answers[0]
        got = self.question_answer_repo.find_by_id(
            id=want.id,
            bot_id=bot_id,
        )
        assert got == want

    def test_find_by_ids_and_statuses(
        self, question_answer_seed: Tuple[bot_domain.Id, list[question_answer_domain.QuestionAnswer]]
    ):
        bot_id, question_answers = question_answer_seed
        got = self.question_answer_repo.find_by_ids_and_statuses(
            ids=[qa.id for qa in question_answers],
            bot_id=bot_id,
            statuses=[question_answer_domain.Status.INDEXED, question_answer_domain.Status.PENDING],
        )
        assert got == question_answers

    def test_find_by_bot_id_and_question(
        self, question_answer_seed: Tuple[bot_domain.Id, list[question_answer_domain.QuestionAnswer]]
    ):
        bot_id, question_answers = question_answer_seed
        question = question_answers[0].question
        got = self.question_answer_repo.find_by_bot_id_and_question(
            bot_id=bot_id,
            question=question,
        )
        assert got == question_answers[0]

    def test_create(
        self,
        bots_seed: BotsSeed,
    ):
        bots, _, _, _ = bots_seed
        bot_id = bots[0].id
        question_answer_for_create = QuestionAnswerForCreate(
            question=question_answer_domain.Question(root="question"),
            answer=question_answer_domain.Answer(root="answer"),
            status=question_answer_domain.Status.INDEXED,
        )

        self.question_answer_repo.create(
            bot_id=bot_id,
            question_answer=question_answer_for_create,
        )

        created_question_answer = (
            self.session.execute(
                select(QuestionAnswer)
                .where(QuestionAnswer.bot_id == bot_id.value)
                .where(QuestionAnswer.id == question_answer_for_create.id.root)
            )
            .scalars()
            .first()
        )
        assert created_question_answer is not None
        assert created_question_answer.id == question_answer_for_create.id.root
        assert created_question_answer.bot_id == bot_id.value
        assert created_question_answer.question == question_answer_for_create.question.root
        assert created_question_answer.answer == question_answer_for_create.answer.root

    def test_bulk_create(
        self,
        bots_seed: BotsSeed,
    ):
        bots, _, _, _ = bots_seed
        bot_id = bots[0].id
        question_answers_for_create = [
            QuestionAnswerForCreate(
                question=question_answer_domain.Question(root=f"question_{i}"),
                answer=question_answer_domain.Answer(root=f"answer_{i}"),
            )
            for i in range(3)
        ]

        self.question_answer_repo.bulk_create(
            bot_id=bot_id,
            question_answers=question_answers_for_create,
        )

        created_question_answers = (
            self.session.execute(
                select(QuestionAnswer)
                .where(QuestionAnswer.bot_id == bot_id.value)
                .where(QuestionAnswer.id.in_([qa.id.root for qa in question_answers_for_create]))
            )
            .scalars()
            .all()
        )
        assert len(created_question_answers) == 3

        for i, created_question_answer in enumerate(created_question_answers):
            assert created_question_answer.id == question_answers_for_create[i].id.root
            assert created_question_answer.bot_id == bot_id.value
            assert created_question_answer.question == question_answers_for_create[i].question.root
            assert created_question_answer.answer == question_answers_for_create[i].answer.root
            assert created_question_answer.status == question_answer_domain.Status.PENDING

    def test_update(self, question_answer_seed: Tuple[bot_domain.Id, list[question_answer_domain.QuestionAnswer]]):
        bot_id, question_answers = question_answer_seed
        question_answer = question_answers[0]
        question_answer.update(
            question_answer_domain.QuestionAnswerForUpdate(
                id=question_answer.id,
                question=question_answer_domain.Question(root="question1_updated"),
                answer=question_answer_domain.Answer(root="answer1_updated"),
            )
        )
        self.question_answer_repo.update(
            bot_id=bot_id,
            question_answer=question_answer,
        )
        updated_question_answer = (
            self.session.execute(
                select(QuestionAnswer)
                .where(QuestionAnswer.bot_id == bot_id.value)
                .where(QuestionAnswer.id == question_answer.id.root)
            )
            .scalars()
            .first()
        )
        assert updated_question_answer is not None
        assert updated_question_answer.id == question_answer.id.root
        assert updated_question_answer.bot_id == bot_id.value
        assert updated_question_answer.question == "question1_updated"
        assert updated_question_answer.answer == "answer1_updated"

    def test_bulk_update_status(
        self, question_answer_seed: Tuple[bot_domain.Id, list[question_answer_domain.QuestionAnswer]]
    ):
        bot_id, question_answers = question_answer_seed
        ids = [qa.id for qa in question_answers]
        self.question_answer_repo.bulk_update_status(
            ids=ids,
            bot_id=bot_id,
            status=question_answer_domain.Status.INDEXED,
        )
        updated_question_answers = (
            self.session.execute(
                select(QuestionAnswer)
                .where(QuestionAnswer.bot_id == bot_id.value)
                .where(QuestionAnswer.id.in_([id.root for id in ids]))
            )
            .scalars()
            .all()
        )
        assert len(updated_question_answers) == len(question_answers)

        for updated_question_answer in updated_question_answers:
            assert updated_question_answer.status == question_answer_domain.Status.INDEXED

    def test_bulk_update(
        self, question_answer_seed: Tuple[bot_domain.Id, list[question_answer_domain.QuestionAnswer]]
    ):
        bot_id, question_answers = question_answer_seed
        for question_answer in question_answers:
            question_answer.update(
                question_answer_domain.QuestionAnswerForUpdate(
                    id=question_answer.id,
                    question=question_answer_domain.Question(root=f"{question_answer.question.root}_updated"),
                    answer=question_answer_domain.Answer(root=f"{question_answer.answer.root}_updated"),
                )
            )

        self.question_answer_repo.bulk_update(
            bot_id=bot_id,
            question_answers=question_answers,
        )
        updated_question_answers = (
            self.session.execute(
                select(QuestionAnswer)
                .where(QuestionAnswer.bot_id == bot_id.value)
                .where(QuestionAnswer.id.in_([qa.id.root for qa in question_answers]))
            )
            .scalars()
            .all()
        )
        assert len(updated_question_answers) == len(question_answers)

        for i, updated_question_answer in enumerate(updated_question_answers):
            assert updated_question_answer.id == question_answers[i].id.root
            assert updated_question_answer.bot_id == bot_id.value
            assert updated_question_answer.question == f"question{i+1}_updated"
            assert updated_question_answer.answer == f"answer{i+1}_updated"

    @pytest.mark.parametrize("question_answer_seed", [{"cleanup_resources": False}], indirect=True)
    def test_delete_by_bot_id(self, question_answer_seed: QuestionAnswerSeed):
        bot_id, _ = question_answer_seed

        self.question_answer_repo.delete_by_bot_id(bot_id)

        question_answers = self.question_answer_repo.find_by_bot_id(bot_id)
        assert len(question_answers) == 0

    @pytest.mark.parametrize("question_answer_seed", [{"cleanup_resources": False}], indirect=True)
    def test_hard_delete_by_bot_ids(self, question_answer_seed: QuestionAnswerSeed):
        bot_id, _ = question_answer_seed

        self.question_answer_repo.delete_by_bot_id(bot_id)
        self.question_answer_repo.hard_delete_by_bot_ids([bot_id])

        question_answers = (
            self.session.execute(
                select(QuestionAnswer)
                .where(QuestionAnswer.bot_id == bot_id.value)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )
        assert len(question_answers) == 0
