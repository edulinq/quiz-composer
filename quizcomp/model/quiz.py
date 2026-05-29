import logging
import os
import random
import string
import typing

import edq.util.dirent
import edq.util.git
import edq.util.time

import quizcomp.constants
import quizcomp.model.base
import quizcomp.model.errors
import quizcomp.model.group
import quizcomp.model.question
import quizcomp.parser.document

_logger = logging.getLogger(__name__)

DUMMY_QUIZ_DATA: typing.Dict[str, typing.Any] = {
    'name': 'Dummy Name',
    'description': quizcomp.parser.document.ParsedDocument.parse_text('Dummy description.'),
    'course_name': 'Dummy Course',
    'term_name': 'Dummy Term',
    'version': '0.0.0',
}

DUMMY_GROUP_DATA: typing.Dict[str, typing.Any] = {
    'name': 'Dummy Question',
}

DEFAULT_VARIANT_IDS: typing.List[str] = list(string.ascii_uppercase)
""" Default IDs for quiz variants. """

DEFAULT_MAX_VARIANTS: int = len(DEFAULT_VARIANT_IDS)

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
        # Remove aliases before super construction.
        kwargs.pop('groups', None)

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

        if ((time_limit_mins is not None) and (time_limit_mins < 0)):
            time_limit_mins = None

        self.time_limit_mins: typing.Union[int, None] = time_limit_mins
        """ The time limit (in minutes) for this quiz. """

        self.version: typing.Union[str, None] = version
        """ The version of this quiz. """

        self._validate()

    def _validate(self) -> None:
        """ Check if this quiz is valid. """

        if (self.name is None):
            raise quizcomp.model.errors.QuizValidationError("Quiz name cannot be empty.", context = self)

    def collect_documents(self) -> typing.List[quizcomp.parser.document.ParsedDocument]:
        return [self.description]

    @classmethod
    def prep_init_data(cls,
            data: typing.Dict[str, typing.Any],
            context: edq.util.serial.SerializationContext,
            ) -> typing.Dict[str, typing.Any]:
        data = super().prep_init_data(data, context)

        data['description'] = cls._collect_description(data, context)

        return data

    @classmethod
    def _collect_description(cls,
            data: typing.Dict[str, typing.Any],
            context: edq.util.serial.SerializationContext,
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

        # If we have a quiz path, use that to resolve paths.
        default_description_path = None
        if (context.source_path is not None):
            context.source_path = os.path.abspath(context.source_path)
            context.base_dir = os.path.dirname(context.source_path)
            default_description_path = os.path.splitext(context.source_path)[0] + '.md'

        # Check the `description` field.
        text = data.get('description', None)
        if (text is not None):
            return quizcomp.parser.document.ParsedDocument.parse_text(text, context)

        # Check for an explicitly provided path.
        description_path = data.get('description_path', None)
        if (description_path is not None):
            if (not os.path.isabs(description_path)):
                description_path = os.path.join(context.base_dir, description_path)

            description_path = os.path.abspath(description_path)

            if (not os.path.isfile(description_path)):
                raise quizcomp.model.errors.QuestionValidationError(
                        f"Could not find a description at the provided path: '{data['description_path']}' (Absolute Path: '{description_path}').",
                        context = context)

            return quizcomp.parser.document.ParsedDocument.parse_file(description_path)

        # Check for an implicit path.
        if ((default_description_path is not None) and os.path.isfile(default_description_path)):
            return quizcomp.parser.document.ParsedDocument.parse_file(default_description_path)

        return quizcomp.parser.document.ParsedDocument()

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        data = super().to_pod(context)
        data['groups'] = data.pop('children', data.get('groups', None))
        return data

    @classmethod
    def from_pod(cls,
            data: edq.util.serial.PODType,
            context: edq.util.serial.SerializationContext,
            ) -> 'Quiz':
        data['children'] = data.pop('groups', data.get('children', None))
        return super().from_pod(data, context)

    def create_variant(self,
            seed: typing.Union[int, None] = None,
            identifiers: typing.Union[typing.List[str], None] = None,
            all_questions: bool = False,
            include_solo_identifier: bool = False,
            ) -> 'Variant':
        """ A convenience call to create_variants(). """

        return self.create_variants(
            count = 1,
            seed = seed,
            identifiers = identifiers,
            all_questions = all_questions, include_solo_identifier = include_solo_identifier,
        )[0]

    def create_variants(self,
            count: int = 1,
            seed: typing.Union[int, None] = None,
            identifiers: typing.Union[typing.List[str], None] = None,
            all_questions: bool = False,
            include_solo_identifier: bool = False,
            ) -> typing.List['Variant']:
        """
        Create a collection of variants based on this quiz.
        These variants will share the same question pool,
        which is influenced by the `pick_with_replacement` config option.

        Setting `include_solo_identifier` to true will include an identifier (e.g., " - A")
        in the name of variants when only one variant is created.
        """

        if (seed is None):
            seed = random.randint(0, 2**64)

        rng = random.Random(seed)

        if (identifiers is None):
            identifiers = DEFAULT_VARIANT_IDS

        if (count < 0):
            raise quizcomp.model.errors.QuizValidationError(
                    f"Variant count must be non-negative, found: {count}.",
                    context = self)

        if (count > len(identifiers)):
            raise quizcomp.model.errors.QuizValidationError(
                ('"Not enough variant identifiers supplied.'
                    + f" Got {len(identifiers)} identifiers and {count} requested variants."
                    + f" Given identifiers: {identifiers}."),
                context = self)

        _logger.debug("Creating %d variants with seed %d.", count, seed)

        used_question_indexes: typing.List[typing.Set[int]] = [set() for _ in self.children]
        variants = []

        for i in range(count):
            variant_id: typing.Union[str, None] = None
            if ((count > 1) or (include_solo_identifier)):
                variant_id = identifiers[i]

            variants.append(self._create_variant(variant_id, rng, used_question_indexes, all_questions))

        return variants

    def _create_variant(self,
            variant_id: typing.Union[str, None],
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

        data['name'] = self.name
        if (variant_id is not None):
            data['name'] += f" - {variant_id}"

        data['variant_id'] = variant_id
        data['quiz_name'] = self.name
        data['groups'] = new_groups

        data['version'] = self.version
        if ((self.version is not None) and (variant_id is not None)):
            data['version'] = f"{self.version}, Variant: {variant_id}"

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

    @staticmethod
    def get_dummy(
            question: quizcomp.model.question.Question,
            seed: typing.Union[int, None] = None,
            ) -> 'Variant':
        """
        Get a "dummy" variant that has no real information.
        """

        question = question.copy()
        group = quizcomp.model.group.Group(children = [question], **DUMMY_GROUP_DATA.copy())
        quiz = Quiz(children = [group], **DUMMY_QUIZ_DATA.copy())

        return quiz.create_variant(seed = seed)
