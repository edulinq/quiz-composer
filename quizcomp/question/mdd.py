import random
import typing

import quizcomp.common
import quizcomp.constants
import quizcomp.model.question
import quizcomp.parser.public
import quizcomp.question.base

class MDD(quizcomp.question.base.Question, question_type = quizcomp.model.question.QuestionType.MDD):
    """ A question answered by selecting exactly one of the provided choices for multiple instances. """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def _validate_answers(self) -> None:
        self._check_type(self.answers, dict, "'answers' key")

        if (len(self.answers) == 0):
            raise quizcomp.common.QuestionValidationError("No answers provided, at least one answer required.", ids = self.ids)

        for (key, answers) in list(self.answers.items()):
            # If this was already in the full MDD format, then we need to pull out the values.
            if ((isinstance(answers, dict)) and ('values' in answers)):
                answers = answers['values']

            values = self._validate_answer_list(answers, self.base_dir, min_correct = 1, max_correct = 1)

            self.answers[key] = {
                'key': quizcomp.parser.public.parse_text(key, base_dir = self.base_dir),
                'values': values,
            }

        self._check_placeholders(self.answers.keys())

    def _shuffle(self, rng: random.Random) -> None:
        for key in self.answers:
            rng.shuffle(self.answers[key]['values'])
