import quizcomp.constants
import quizcomp.question.base

class SA(quizcomp.question.base.Question, question_type = quizcomp.constants.QUESTION_TYPE_SA):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        self._validate_text_answers()
