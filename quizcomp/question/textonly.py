import quizcomp.common
import quizcomp.constants
import quizcomp.question.base

class TextOnly(quizcomp.question.base.Question, question_type = quizcomp.constants.QUESTION_TYPE_TEXT_ONLY):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        if (self.answers is not None):
            raise quizcomp.common.QuestionValidationError(self, "'answers' key must be missing or None/null, found: '%s'." % (
                    str(self.answers)))
