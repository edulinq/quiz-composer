import random
import typing

import quizcomp.constants
import quizcomp.model.question
import quizcomp.question.base

class MC(quizcomp.question.base.Question, question_type = quizcomp.model.question.QuestionType.MCQ):
    """ A question answered by selecting exactly one of the provided choices. """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def _validate_answers(self) -> None:
        self._validate_self_answer_list(min_correct = 1, max_correct = 1)

    def _shuffle(self, rng: random.Random) -> None:
        self._shuffle_answers_list(rng)
