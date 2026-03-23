import random
import typing

import quizcomp.common
import quizcomp.constants
import quizcomp.model.question
import quizcomp.question.base

class TF(quizcomp.question.base.Question, question_type = quizcomp.model.question.QuestionType.TF):
    """ A question answered by choosing true or false. """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def _validate_answers(self) -> None:
        if (isinstance(self.answers, bool)):
            # Change answers to look like multiple choice.
            self.answers = [
                {"correct": self.answers, "text": 'True'},
                {"correct": (not self.answers), "text": 'False'},
            ]
        elif (isinstance(self.answers, list)):
            pass
        else:
            raise quizcomp.common.QuestionValidationError(
                    f"'answers' value must be a boolean, found '{self.answers}' ({type(self.answers)}).",
                    ids = self.ids)

        self._validate_self_answer_list()

        if (len(self.answers) != 2):
            raise quizcomp.common.QuestionValidationError(
                    f"Expecting exactly two answers, found {len(self.answers)}.",
                    ids = self.ids)

        labels = list(sorted([answer.text for answer in self.answers]))

        expected = ['False', 'True']
        if (labels != expected):
            raise quizcomp.common.QuestionValidationError(
                    f"T/F labels (text) not as expected. Expected: '{expected}', Actual: '{labels}'.",
                    ids = self.ids)

    def _shuffle(self, rng: random.Random) -> None:
        self._shuffle_answers_list(rng)
