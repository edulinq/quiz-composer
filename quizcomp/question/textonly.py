import typing

import quizcomp.common
import quizcomp.constants
import quizcomp.model.constants
import quizcomp.question.base

class TextOnly(quizcomp.question.base.Question, question_type = quizcomp.model.constants.QuestionType.TEXT_ONLY):
    """ A question that accepts no answer. """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def _validate_answers(self) -> None:
        if (self.answers is None):
            return

        if (isinstance(self.answers, (tuple, list, dict)) and (len(self.answers) == 0)):
            self.answers = None
            return

        raise quizcomp.common.QuestionValidationError(
                f"'answers' key must be missing, None/null, or empty, found: '{self.answers}''.",
                ids = self.ids)
