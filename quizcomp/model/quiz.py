import datetime
import logging
import os
import random
import string
import typing

import edq.util.dirent
import edq.util.git
import edq.util.time

import quizcomp.canvas
import quizcomp.common
import quizcomp.constants
import quizcomp.errors
import quizcomp.model.base
import quizcomp.model.group
import quizcomp.parser.document
import quizcomp.question.base
import quizcomp.util.serial

DUMMY_QUIZ_DATA: typing.Dict[str, typing.Any] = {
    'name': 'Dummy Title',
    'description': 'Dummy description.',
    'course_name': 'Dummy Course',
    'term_name': 'Dummy Term',
    'version': '0.0.0',
}

DUMMY_GROUP_DATA: typing.Dict[str, typing.Any] = {
    'name': 'Dummy Question',
    'hints': {},
    'hints_first': {},
    'hints_last': {},
}

DEFAULT_VARIANT_IDS: typing.List[str] = list(string.ascii_uppercase)
""" Default IDs for quiz variants. """

class Quiz(quizcomp.model.base.CoreType):
    """
    A quiz object represents multiple possible assessments (called "variants").
    """

    def __init__(self,
            children: typing.Union[typing.List[quizcomp.model.group.Group], None] = None,
            description: typing.Union[quizcomp.parser.document.ParsedDocument, None] = None,
            course_name: typing.Union[str, None] = None,
            term_name: typing.Union[str, None] = None,
            date: typing.Union[edq.util.time.Timestamp, None] = None,
            time_limit_mins: typing.Union[int, None] = None,
            version: typing.Union[str, None] = None,
            **kwargs: typing.Any) -> None:
        super().__init__(children = children, **kwargs)

        self.course_name: typing.Union[str, None] = course_name
        """ The optional name for the course associated with this quiz. """

        self.term_name: typing.Union[str, None] = term_name
        """ The optional name of the term this quiz takes place during (e.g., "Fall 20XX"). """

        self.date: typing.Union[edq.util.time.Timestamp, None] = date
        """ The optional date of this quiz. """

        if (description is None):
            description = quizcomp.parser.document.ParsedDocument()

        self.description: quizcomp.parser.document.ParsedDocument = description
        """ The description/prompt for this quiz. """

        self.time_limit_mins: typing.Union[int, None] = time_limit_mins
        """ The time limit (in minutes) for this quiz. """

        self.version: typing.Union[str, None] = version
        """ The version of this quiz. """

        ''' TEST
        if (seed is None):
            seed = random.randint(0, 2**64)

        # TEST - We probably shouldn't cary a seed. Leave it to the CLI.
        self.seed: int = seed
        """ The seed used for this quiz. """

        self._rng: random.Random = random.Random(self.seed)
        """ The RNG used for this quiz. """
        '''

    @classmethod
    def prep_init_data(cls,
            data: typing.Dict[str, typing.Any],
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> typing.Dict[str, typing.Any]:
        data = super().prep_init_data(data, serialization_options)

        data['description'] = cls._collect_description(data, serialization_options)

        return data

    @classmethod
    def _collect_description(cls,
            data: typing.Dict[str, typing.Any],
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> quizcomp.parser.document.ParsedDocument:
        """
        Collect the description from one of several possible locations.

        The description is allowed to appear (in order of priority):
        1) in the `description` field.
        2) pointed to by the `description_path` field.
        3) or be in the same path as the quiz JSON, but with an `.md` extension
           (e.g., `a/b/my_quiz.json` and `a/b/my_quiz.md`).

        None values will be ignored (but empty values are valid).
        Will return an empty description if none of these are present.
        """

        if (serialization_options is None):
            serialization_options = {}

        quiz_path = serialization_options.get('path', None)
        base_dir = serialization_options.get('base_dir', '.')
        default_description_path = None

        # If we have a quiz path, use that to resolve paths.
        if (quiz_path is not None):
            quiz_path = os.path.abspath(quiz_path)
            base_dir = os.path.dirname(quiz_path)
            default_description_path = os.path.splitext(quiz_path)[0] + '.md'

        # Check the `description` field.
        text = data.get('description', None)
        if (text is not None):
            return quizcomp.parser.document.ParsedDocument.parse_text(text, base_dir = base_dir)

        # Check for an explicitly provided path.
        description_path = data.get('description_path', None)
        if (description_path is not None):
            if (not os.path.isabs(description_path)):
                description_path = os.path.join(base_dir, description_path)

            description_path = os.path.abspath(description_path)

            if (not os.path.isfile(description_path)):
                raise quizcomp.errors.QuestionValidationError(f"Could not find a description at the provided path: '{data['description_path']}' (Absolute Path: '{description_path}').", base_dir = base_dir)

            return quizcomp.parser.document.ParsedDocument.parse_file(description_path)

        # Check for an implicit path.
        if ((default_description_path is not None) and os.path.isfile(default_description_path)):
            return quizcomp.parser.document.ParsedDocument.parse_file(default_description_path)

        return quizcomp.parser.document.ParsedDocument()

    def shuffle(self, rng: random.Random) -> None:
        """
        Shuffle the answers for this question.
        This method will do nothing if question shuffling is not allowed by the config settings.
        """

        if (self.get_config(quizcomp.model.config.OPTION_SHUFFLE_ANSWERS) is not True):
            return

        self.answers.shuffle(rng)

    def to_pod(self,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        data = super().to_pod(serialization_options)
        data['groups'] = data.pop('children', data.get('groups', None))
        return data

    @classmethod
    def from_pod(cls,
            data: edq.util.serial.PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> 'Quiz':
        data['children'] = data.pop('groups', data.get('children', None))
        return super().from_pod(data, serialization_options)

    # TEST
    ''' TEST
    def _validate(self, **kwargs: typing.Any) -> None:
        """ Check if this quiz is valid, will raise if the group is not valid. """

        if ((self.name is None) or (self.name == "")):
            raise quizcomp.common.QuizValidationError("Title cannot be empty.")

        if ((self._raw_description is None) or (self._raw_description == "")):
            raise quizcomp.common.QuizValidationError("Description cannot be empty.")

        self.description = quizcomp.parser.document.ParsedDocument.parse_text(self._raw_description, base_dir = self.base_dir)

        if (self.version is None):
            self.version = edq.util.git.get_version(self.base_dir, throw = False)
            if (self.version == edq.util.git.UNKNOWN_VERSION):
                logging.warning("Could not get a version for the quiz (is it in a git repo?).")

        self.canvas = quizcomp.canvas.validate_options(self.canvas)

        self._validate_time_limit()

        if (self.date == ''):
            self.date = datetime.date.today()
        elif (isinstance(self.date, str)):
            self.date = datetime.date.fromisoformat(self.date)
        else:
            raise quizcomp.common.QuizValidationError(f"Date should be a string or datetime.date, found '{str(type(self.date))}'.")

        for key in kwargs:
            logging.warning("Unknown quiz option: '%s'.", key)

    def _validate_time_limit(self) -> None:
        """ Validate the time limit component of this quiz. """

        if (self.time_limit_mins is None):
            return

        if (not isinstance(self.time_limit_mins, (str, int))):
            raise quizcomp.common.QuizValidationError(f"Time limit must be a positive int, found '{str(self.time_limit_mins)}'.")

        try:
            self.time_limit_mins = int(self.time_limit_mins)
        except:
            raise quizcomp.common.QuizValidationError(f"Time limit must be a positive int, found '{str(self.time_limit_mins)}'.")  # pylint: disable=raise-missing-from

        if (self.time_limit_mins < 0):
            raise quizcomp.common.QuizValidationError(f"Time limit must be a positive int, found '{str(self.time_limit_mins)}'.")

        if (self.time_limit_mins == 0):
            self.time_limit_mins = None
    '''

    def create_variants(self,
            count: int = 1,
            seed: typing.Union[int, None] = None,
            identifiers: typing.Union[typing.List[str], None] = None,
            all_questions: bool = False,
            ) -> typing.List['Variant']:
        """
        Create a collection of variants based on this quiz.
        These variants will share the same question pool,
        which is influenced by the `pick_with_replacement` config option.
        """

        if (seed is None):
            seed = self._rng.randint(0, 2**64)

        rng = random.Random(seed)

        if (identifiers is None):
            identifiers = DEFAULT_VARIANT_IDS

        if (count < 0):
            raise quizcomp.common.QuizValidationError(f"Variant count must be non-negative, found: {count}.", base_dir = self.base_dir)

        if (count > len(identifiers)):
            raise quizcomp.common.QuizValidationError(f"Not enough variant identifiers supplied. Got {len(identifiers)} identifiers and {count} requested variants. Given identifiers: {identifiers}.", base_dir = base_dir)

        logging.debug("Creating %d variants with seed %d.", count, seed)

        used_question_indexes = [set() for _ in self.children]
        variants = [self._create_variant(identifiers[i], rng, used_question_indexes, all_questions) for i in range(count)]

        return variants

    def _create_variant(self,
            identifier: str,
            rng: random.Random,
            used_question_indexes: typing.List[typing.Set[int]],
            all_questions: bool,
            ) -> 'Variant':
        """ Create a single variant based on this quiz. """

        new_groups = []
        for group in self.children:
            questions = group.choose_variant_questions(all_questions, used_question_indexes, rng)

            group_data = vars(group).copy()
            group_data['children'] = questions

            new_groups.append(quizcomp.model.group.Group(**group_data))

        data = vars(self).copy()

        data['variant_id'] = identifier
        data['quiz_name'] = self.name
        data['name'] = f"{self.name} - {identifier}"
        data['groups'] = new_groups

        if (self.version is not None):
            data['version'] = f"{self.version}, Variant: {identifier}"

        return Variant(**data)

class Variant(Quiz):
    """
    A quiz variant is an instantiation of a quiz with specific set of questions chosen for each group.
    Variants still have question groups, but each group must only have the exact number of questions required for each group
    (or it is a validation error).

    Variants created directly from quizzes (as opposed to from a JSON file)
    will already have all the correct components, and will therefore only be lightly validated.
    Quizzes created from files will undergo full validation.
    """

    def __init__(self,
            quiz_name: str,
            variant_id: str,
            **kwargs: typing.Any,
            ) -> None:
        super().__init__(**kwargs)

        self.quiz_name: str = quiz_name
        """ The name of the quiz this variant was generated from. """

        self.variant_id: str = variant_id
        """ An identifier to differentiate this variant from its siblings. """

    ''' TEST
    def _validate(self, **kwargs: typing.Any) -> None:
        """ Check if this variant is valid, will raise if the group is not valid. """

        # Ensure that each group has the correct number of questions.
        for (i, group) in enumerate(self.groups):
            if (len(group.questions) != group.pick_count):
                raise quizcomp.common.QuizValidationError(
                        f"Group at index {i} ('{group.name}') has {len(group.questions)} questions, expecting exactly {group.pick_count}.")
    '''

    @staticmethod
    def get_dummy(question: quizcomp.question.base.Question) -> 'Variant':
        """
        Get a "dummy" variant that has no real information.
        """

        quiz_data = DUMMY_QUIZ_DATA.copy()
        group_data = DUMMY_GROUP_DATA.copy()

        group_data['questions'] = [question]
        group_data['_skip_class_validations'] = [quizcomp.model.group.Group]
        quiz_data['groups'] = [quizcomp.model.group.Group(**group_data)]

        return Variant(**quiz_data)
