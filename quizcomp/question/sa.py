import typing

import quizcomp.constants
import quizcomp.model.question
import quizcomp.question.base

class SA(quizcomp.question.base.Question, question_type = quizcomp.model.question.QuestionType.SA):
    """ A question answered with a short piece of text (e.g. sentence or paragraph). """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def _validate_answers(self) -> None:
        self._validate_text_answers()
