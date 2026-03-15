import glob
import logging
import os
import random
import typing

import quizcomp.common
import quizcomp.constants
import quizcomp.question.base
import quizcomp.util.serial
import quizcomp.variant

class Group(quizcomp.util.serial.JSONSerializer):
    def __init__(self,
            name: str = '',
            pick_count: int = 1,
            points: float = 10,
            shuffle_answers: bool = True,
            pick_with_replacement: bool = True,
            custom_header: typing.Union[str, None] = None,
            skip_numbering: typing.Union[bool, None] = None,
            hints: typing.Union[typing.Dict[str, typing.Any], None] = None,
            hints_first: typing.Union[typing.Dict[str, typing.Any], None] = None,
            hints_last: typing.Union[typing.Dict[str, typing.Any], None] = None,
            questions: typing.Union[typing.List[quizcomp.question.base.Question], None] = None,
            ids: typing.Union[typing.Dict[str, typing.Any], None] = None,
            **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

        self.name: str = name
        """ The name of this question group. """

        self.pick_count: int = pick_count
        """ The number of questions to choose from this group. """

        self.points: float = points
        """ The number of points for each question in this group. """

        self.shuffle_answers: bool = shuffle_answers
        """ Whether the answers for this group's questions should be shuffled. """

        self.pick_with_replacement: bool = pick_with_replacement
        """
        Whether or not questions are chosen with replacement between variants.
        Choosing with replacement means that the same question may appear in multiple variants.
        """

        self._used_question_indexes: typing.Set[int] = set()
        """ The questions that have already been used in different variants. """

        self.custom_header: typing.Union[str, None] = custom_header
        """ A custom header for the question, instead of something generic like "Question 4". """

        self.skip_numbering: typing.Union[bool, None] = skip_numbering
        """ Whether to skip numbering for this group. """

        self.hints: typing.Union[typing.Dict[str, typing.Any], None] = hints
        """ Hints applied to this entire group. """

        self.hints_first: typing.Union[typing.Dict[str, typing.Any], None] = hints_first
        """ Hints applied to the first question of this group. """

        self.hints_last: typing.Union[typing.Dict[str, typing.Any], None] = hints_last
        """ Hints applied to the last question of this group. """

        if (questions is None):
            questions = []

        self.questions = questions
        """ The questions for this group. """

        if (ids is None):
            ids = {}

        try:
            self.validate()
        except Exception as ex:
            ids = ids.copy()
            ids[name] = self.name

            raise quizcomp.common.QuizValidationError('Error while validating group.', ids = ids) from ex

    def _validate(self, **kwargs: typing.Any) -> None:
        """ Check if this group is valid, will raise if the group is not valid. """

        if ((self.name is None) or (self.name == "")):
            raise quizcomp.common.QuizValidationError("Name cannot be empty.")

        if (self.pick_count < 0):
            raise quizcomp.common.QuizValidationError("Pick count cannot be negative.")

        if (self.hints is None):
            self.hints = {}

        if (self.hints_first is None):
            self.hints_first = {}

        if (self.hints_last is None):
            self.hints_last = {}

        if (not isinstance(self.questions, list)):
            raise quizcomp.common.QuizValidationError("Questions must be a non-empty list, found: '%s'." % (str(self.questions)))

        if (len(self.questions) == 0):
            raise quizcomp.common.QuizValidationError("Questions must be non-empty.")

        for question in self.questions:
            question.inherit_from_group(self)

        if (self.pick_count > len(self.questions)):
            logging.warning("Group '%s' was asked to pick more questions than available (pick_count: %d, group size: %d)." % (
                    self.name, self.pick_count, len(self.questions)))
            self.pick_count = len(self.questions)

    def collect_file_paths(self) -> typing.List[str]:
        """ Collect the file paths represented in this group. """

        paths = []

        for question in self.questions:
            paths += question.collect_file_paths()

        return paths

    @staticmethod
    def from_dict(group_info: typing.Dict[str, typing.Any], base_dir: str, **kwargs: typing.Any) -> 'Group':  # type: ignore[override]
        """ Construct a group from a dict. """

        group_info = group_info.copy()

        paths = []
        for path in group_info.get('questions', []):
            if (not os.path.isabs(path)):
                path = os.path.join(base_dir, path)
            paths.append(os.path.abspath(path))

        paths = list(sorted(set(paths)))

        questions = []
        for path in paths:
            questions += _parse_questions(path)

        group_info['questions'] = questions

        return Group(**group_info)

    def choose_questions(self,
            all_questions: bool = False,
            rng: typing.Union[random.Random, None] = None,
            with_replacement: bool = True,
            ) -> typing.List[quizcomp.question.base.Question]:
        """ Choose a list of questions to use for an instantiated variant of this group. """

        if ((self.pick_count == 0) or (len(self.questions) == 0)):
            logging.warning("Group '%s' will select no questions (pick_count: %d, group size: %d)." % (
                    self.name, self.pick_count, len(self.questions)))
            return []

        with_replacement = (self.pick_with_replacement and with_replacement)

        if (rng is None):
            seed = random.randint(0, 2**64)
            rng = random.Random(seed)

        count = self.pick_count
        if (all_questions):
            count = len(self.questions)

        questions = self._choose_questions(count, rng, with_replacement)

        # Rename questions if there are more than one.
        if (len(questions) > 1):
            for i in range(len(questions)):
                questions[i].name = "%s - %d" % (self.name, i + 1)

        # Inherit position-specific hints.
        questions[0].add_hints(self.hints_first)
        questions[-1].add_hints(self.hints_last)

        return questions

    def _choose_questions(self,
            count: int,
            rng: random.Random,
            with_replacement: bool
            ) -> typing.List[quizcomp.question.base.Question]:
        """ Internally, choose a list of questions to use for an instantiated variant of this group. """

        indexes = list(range(len(self.questions)))

        if (not with_replacement):
            indexes = list(set(indexes) - self._used_question_indexes)

            if (count > len(indexes)):
                logging.warning("Group '%s' does not have enough questions to pick without replacement." % (self.name))
                # Reset the selection pool.
                indexes = list(range(len(self.questions)))
                self._used_question_indexes = set()

        rng.shuffle(indexes)
        indexes = indexes[:count]

        if (not with_replacement):
            self._used_question_indexes |= set(indexes)

        return [self.questions[index].copy() for index in indexes]

def _parse_questions(path: str) -> typing.List[quizcomp.question.base.Question]:
    """ Recursively parse questions from a path. """

    if (not os.path.exists(path)):
        raise quizcomp.common.QuizValidationError(f"Question path does not exist: '{path}'.")

    if (os.path.isfile(path)):
        return [quizcomp.question.base.Question.from_path(path)]

    questions = []
    for subpath in sorted(glob.glob(os.path.join(path, '**', quizcomp.constants.QUESTION_FILENAME), recursive = True)):
        questions.append(quizcomp.question.base.Question.from_path(subpath))

    return questions
