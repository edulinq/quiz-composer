import quizcomp.constants
import quizcomp.question.base

class MA(quizcomp.question.base.Question, question_type = quizcomp.constants.QUESTION_TYPE_MA):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        self._validate_self_answer_list()

    def _shuffle(self, rng):
        self._shuffle_answers_list(rng)
