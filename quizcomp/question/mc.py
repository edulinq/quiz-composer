import quizcomp.constants
import quizcomp.question.base

class MC(quizcomp.question.base.Question, question_type = quizcomp.constants.QUESTION_TYPE_MCQ):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        self._validate_self_answer_list(min_correct = 1, max_correct = 1)

    def _shuffle(self, rng):
        self._shuffle_answers_list(rng)
