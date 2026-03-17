import random
import typing

import quizcomp.constants
import quizcomp.question.base

class MA(quizcomp.question.base.Question, question_type = quizcomp.constants.QUESTION_TYPE_MA):
    """ A question answered by selecting zero or more provided choices. """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def _validate_answers(self) -> None:
        self._validate_self_answer_list()

    def _shuffle(self, rng: random.Random) -> None:
        self._shuffle_answers_list(rng)
