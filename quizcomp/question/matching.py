import random
import typing

import quizcomp.common
import quizcomp.constants
import quizcomp.model.question
import quizcomp.question.base

class Matching(quizcomp.question.base.Question, question_type = quizcomp.model.question.QuestionType.MATCHING):
    """ A question answered by matching components from a left-hand list to component on a right-hand list. """

    def __init__(self, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

    def _validate_answers(self) -> None:
        self._check_type(self.answers, dict, "'answers' key")

        self._validate_matches()
        self._validate_distractors()

    def _validate_matches(self) -> None:
        if ('matches' not in self.answers):
            raise quizcomp.common.QuestionValidationError(
                    "Matching 'answers' value is missing the 'matches' field.",
                    ids = self.ids)

        matches = self.answers['matches']
        new_matches = []

        for (i, match) in enumerate(matches):
            if (isinstance(match, list)):
                if (len(match) != 2):
                    raise quizcomp.common.QuestionValidationError(
                            f"Expected exactly two items for a match list, found {len(match)} items at element {i}.",
                            ids = self.ids)

                match = {
                    'left': match[0],
                    'right': match[1],
                }

            keys = ['left', 'right']
            for key in keys:
                if (key not in match):
                    raise quizcomp.common.QuestionValidationError(
                            f"Missing key '{key}' for for match item {i}.",
                            ids = self.ids)

            new_matches.append({
                'left': self._validate_text_item(match['left'], f"Left value for match item {i}"),
                'right': self._validate_text_item(match['right'], f"Right value for match item {i}"),
            })

        self.answers['matches'] = new_matches

    def _validate_distractors(self) -> None:
        if ('distractors' not in self.answers):
            self.answers['distractors'] = []

        distractors = self.answers['distractors']
        new_distractors = []

        for (i, distractor) in enumerate(distractors):
            new_distractors.append(self._validate_text_item(distractor, f"distractor at index {i}",
                    clean_whitespace = True))

        self.answers['distractors'] = new_distractors

    def _shuffle(self, rng: random.Random) -> None:
        # Shuffling matching is special because it requires additional shuffling support at the converter level.
        self.answers['shuffle'] = True
        self.answers['shuffle_seed'] = rng.randint(0, 2 ** 64)
