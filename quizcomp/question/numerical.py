import quizcomp.common
import quizcomp.constants
import quizcomp.question.base
import quizcomp.question.common

class Numerical(quizcomp.question.base.Question, question_type = quizcomp.constants.QUESTION_TYPE_NUMERICAL):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _validate_answers(self):
        self._check_type(self.answers, list, "'answers' key")

        for i in range(len(self.answers)):
            answer = self.answers[i]
            label = "'answers' value index %d" % (i)

            self._check_type(answer, dict, label)

            if ('type' not in answer):
                raise quizcomp.common.QuestionValidationError(self, f"Missing key ('type') for {label}.")

            if (answer['type'] == quizcomp.constants.NUMERICAL_ANSWER_TYPE_EXACT):
                required_keys = ['value']

                if ('margin' not in answer):
                    answer['margin'] = 0
            elif (answer['type'] == quizcomp.constants.NUMERICAL_ANSWER_TYPE_RANGE):
                required_keys = ['min', 'max']
            elif (answer['type'] == quizcomp.constants.NUMERICAL_ANSWER_TYPE_PRECISION):
                required_keys = ['value', 'precision']
            else:
                raise quizcomp.common.QuestionValidationError(self, f"Unknown numerical answer type: '{answer['type']}'.")

            for key in required_keys:
                if (key not in answer):
                    raise quizcomp.common.QuestionValidationError(self, f"Missing required key '{key}' for numerical answer type '{answer['type']}'.")

            feedback = self._validate_feedback_item(answer.get('feedback', None), label)
            if (feedback is not None):
                answer['feedback'] = feedback
            else:
                answer.pop('feedback', None)

            self.answers[i] = quizcomp.question.common.NumericChoice(**answer)
