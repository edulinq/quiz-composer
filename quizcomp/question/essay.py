import typing

import quizcomp.constants
import quizcomp.model.constants
import quizcomp.question.base

class Essay(quizcomp.question.base.Question, question_type = quizcomp.model.constants.QuestionType.ESSAY):
    """ A question answered with an essay (long text entry). """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def _validate_answers(self) -> None:
        self._validate_text_answers()
