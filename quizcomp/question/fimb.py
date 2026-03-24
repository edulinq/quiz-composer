import typing

import quizcomp.constants
import quizcomp.model.constants
import quizcomp.question.base

class FIMB(quizcomp.question.base.Question, question_type = quizcomp.model.constants.QuestionType.FIMB):
    """ A question answered by filling in multiple blanks with text. """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def _validate_answers(self) -> None:
        self._validate_fimb_answers()
