import abc
import enum
import math
import random
import string
import typing

import edq.util.enum
import edq.util.serial

import quizcomp.errors
import quizcomp.model.feedback

DEFAULT_CHOICES: typing.List[str] = string.ascii_uppercase
MAX_CHOICES: int = len(DEFAULT_CHOICES)

class NumericAnswerType(enum.StrEnum):
    """ The types of numeric answers supported by the Quiz Composer. """

    EXACT = 'exact'
    RANGE = 'range'
    PRECISION = 'precision'

class TextOption(edq.util.serial.PODConverter):
    """
    One possible text answer to a question.
    """

    serialization_omit_none = True,
    serialization_omit_empty = True,

    def __init__(self,
            text: quizcomp.parser.document.ParsedDocument,
            feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = None,
            **kwargs: typing.Any) -> None:
        self.text: quizcomp.parser.document.ParsedDocument = text
        """ The text/label for this choice. """

        if ((feedback is not None) and feedback.is_empty()):
            feedback = None

        self.feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = feedback
        """ Feedback specific to this choice. """

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        if (self.feedback is None):
            return self.text.to_pod(context)

        return {
            'text': self.text.to_pod(context),
            'feedback': self.feedback.to_pod(context),
        }

    @classmethod
    def from_pod(cls: typing.Type[TextOption],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) -> TextOption:
        label = context.extra.get('label', '')

        if (isinstance(data, str)):
            parsed_text = quizcomp.parser.document.ParsedDocument.parse_text(data, context)
            return TextOption(parsed_text, None)

        if (not isinstance(data, dict)):
            raise quizcomp.errors.QuestionValidationError(
                f"{label} has text in an unknown format (not a string or dict): '{data}' (type: {type(data)}.",
                context = context)

        raw_text = data.get('text', None)
        if (raw_text is None):
            raise quizcomp.errors.QuestionValidationError(f"{label} has no 'text' field set.", context = context)

        parsed_text = quizcomp.parser.document.ParsedDocument.parse_text(raw_text, context)
        feedback = quizcomp.model.feedback.Feedback.from_raw_data(data.get('feedback', None), context)

        return TextOption(parsed_text, feedback)

    @classmethod
    def from_pod_with_error(cls: typing.Type[TextOption],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            label: str,
            ) -> TextOption:
        """ Wrap from_pod() with some error information. """

        context = context.copy()
        context.extra['label'] = label

        return cls.from_pod(data, context)

class NumericOption(edq.util.serial.PODConverter, abc.ABC):
    """
    One possible numeric answer to a question.
    """

    serialization_omit_none = True,
    serialization_omit_empty = True,

    def __init__(self,
            type: NumericAnswerType,
            feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = None,
            **kwargs: typing.Any) -> None:
        self.type: NumericAnswerType = type
        """ The type of numeric answer. """

        if ((feedback is not None) and feedback.is_empty()):
            feedback = None

        self.feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = feedback
        """ Feedback specific to this choice. """

    @abc.abstractmethod
    def to_text(self) -> TextOption:
        """ Get a textual representation of this option. """

    @classmethod
    def from_pod(cls: typing.Type[NumericOption],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) -> NumericOption:
        label = context.extra.get('label', '')

        quizcomp.errors.check_type(data, dict, label, context = context)

        answer_type = data.get('type', None)
        if (not edq.util.enum.has_value(NumericAnswerType, answer_type)):
            raise quizcomp.errors.QuestionValidationError(f"{label} has an unknown answer type: '{answer_type}'.", context = context)

        feedback = quizcomp.model.feedback.Feedback.from_raw_data(data.get('feedback', None), context = context)

        if (answer_type == NumericAnswerType.EXACT):
            value = data.get('value', None)
            if (value is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'value' key.", context = context)

            if (not isinstance(value, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'value' that is not an int or float, found '{type(value)}'.", context = context)

            margin = data.get('margin', 0.0)
            if (not isinstance(margin, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'margin' that is not an int or float, found '{type(margin)}'.", context = context)

            return NumericOptionExact(value, margin, feedback = feedback)
        elif (answer_type == NumericAnswerType.RANGE):
            min = data.get('min', None)
            if (min is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'min' key.", context = context)

            if (not isinstance(min, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'min' that is not an int or float, found '{type(min)}'.", context = context)

            max = data.get('max', None)
            if (max is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'max' key.", context = context)

            if (not isinstance(max, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'max' that is not an int or float, found '{type(max)}'.", context = context)

            return NumericOptionRange(min, max, feedback = feedback)
        elif (answer_type == NumericAnswerType.PRECISION):
            value = data.get('value', None)
            if (value is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'value' key.", context = context)

            if (not isinstance(value, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'value' that is not an int or float, found '{type(value)}'.", context = context)

            precision = data.get('precision', None)
            if (precision is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'precision' key.", context = context)

            if (not isinstance(precision, int)):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'precision' that is not an int, found '{type(precision)}'.", context = context)

            return NumericOptionPrecision(value, precision, feedback = feedback)
        else:
            raise quizcomp.errors.QuestionValidationError(f"{label} has an unknown answer type: '{answer_type}'.", context = context)

    @classmethod
    def from_pod_with_error(cls: typing.Type[NumericOption],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            label: str,
            ) -> NumericOption:
        """ Wrap from_pod() with some error information. """

        context = context.copy()
        context.extra['label'] = label

        return cls.from_pod(data, context)

class NumericOptionExact(NumericOption):
    """ A numeric option to represent an exact value (within a margin). """

    def __init__(self,
            value: typing.Union[float, int],
            margin: typing.Union[float, int] = 0.0,
            **kwargs) -> None:
        super().__init__(type = NumericAnswerType.EXACT, **kwargs)

        self.value: typing.Union[float, int] = value
        """ The value for this answer. """

        self.margin: typing.Union[float, int] = margin
        """ The allowed margin or error for this answer. """

    def to_text(self) -> TextOption:
        text = str(self.value)
        if (not math.isclose(self.margin, 0.0)):
            text += f" ± {self.margin}"

        return TextOption(quizcomp.parser.document.ParsedDocument.parse_text(text), feedback = self.feedback)

class NumericOptionRange(NumericOption):
    """ A numeric option to represent a value within a range. """

    def __init__(self,
            min: typing.Union[float, int],
            max: typing.Union[float, int],
            **kwargs) -> None:
        super().__init__(type = NumericAnswerType.RANGE, **kwargs)

        self.min: typing.Union[float, int] = min
        """ The minimum allowed value. """

        self.max: typing.Union[float, int] = max
        """ The maximum allowed value. """

    def to_text(self) -> TextOption:
        text = f"[{self.min}, {self.max}]"
        return TextOption(quizcomp.parser.document.ParsedDocument.parse_text(text), feedback = self.feedback)

class NumericOptionPrecision(NumericOption):
    """ A numeric option to represent a value within a specified order of magnitudes. """

    def __init__(self,
            value: typing.Union[float, int],
            precision: int,
            **kwargs) -> None:
        super().__init__(type = NumericAnswerType.PRECISION, **kwargs)

        self.value: typing.Union[float, int] = value
        """ The value for this answer. """

        self.precision: int = precision
        """ The number of order of magnitudes allowed. """

    def to_text(self) -> TextOption:
        text = str(self.value)
        if (self.precision != 1):
            text += f" ({self.precision} decimal places)"

        return TextOption(quizcomp.parser.document.ParsedDocument.parse_text(text), feedback = self.feedback)

class Choice(TextOption):
    """
    One possible choice for an answer.
    This is for questions with a finite number of choices (e.g., MCQ, MA, TF).
    """

    serialization_omit_none = True,

    def __init__(self,
            text: quizcomp.parser.document.ParsedDocument,
            correct: bool,
            feedback: typing.Union[quizcomp.model.feedback.Feedback, None] = None,
            **kwargs: typing.Any) -> None:
        super().__init__(text, feedback)

        self.correct: bool = correct
        """ Whether this choice is a correct answer. """

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        data = {
            'text': self.text.to_pod(context),
            'correct': self.correct,
        }

        if (self.feedback is not None):
            data['feedback'] = self.feedback.to_pod(context)

        return data

class QuestionAnswers(edq.util.serial.PODConverter):
    """
    The base type that represents all the listed answers/choices for a question.
    The exact contents of answers vary depending on the question's type.
    """

    def shuffle(self, rng: random.Random) -> None:
        """ Shuffle the choices/options (if applicable). """

    @classmethod
    def from_pod(cls: typing.Type[QuestionAnswers],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) -> QuestionAnswers:
        """
        Create an answers object for a specific question type from some serialized data
        This data will normally come from a JSON file.
        Because of the differing nature of questions, several different forms of answers may need to be processed
        (even for the same question type).

        This function will not return a generic QuestionAnswers, but a subclass of QuestionAnswers.
        """

        raw_question_type = context.extra.get('question_type', None)

        if (raw_question_type is None):
            raise quizcomp.errors.QuestionValidationError("Could not parse question answers because of lack of question type.", context = context)

        question_type = quizcomp.model.constants.QuestionType(raw_question_type)

        if (question_type == quizcomp.model.constants.QuestionType.ESSAY):
            return TextAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.FIMB):
            return MultiplePartTextAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.FITB):
            return TextAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.MA):
            context = context.copy()
            context.extra['min_correct'] = 0
            return ChoiceAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.MATCHING):
            return MatchingAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.MCQ):
            context = context.copy()
            context.extra['min_correct'] = 1
            context.extra['max_correct'] = 1
            return ChoiceAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.MDD):
            context = context.copy()
            context.extra['min_correct'] = 1
            context.extra['max_correct'] = 1
            return MultiplePartChoiceAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.NUMERICAL):
            return NumericAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.SA):
            return TextAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.TEXT_ONLY):
            return TextAnswers.from_pod(data, context)
        elif (question_type == quizcomp.model.constants.QuestionType.TF):
            return TFAnswers.from_pod(data, context)
        else:
            raise quizcomp.errors.QuestionValidationError(f"Unknown question type: '{raw_question_type}'.", context = context)

class TextAnswers(QuestionAnswers):
    """
    Answers that include a list of possible text options.
    Note that the text options are not choices (i.e., they are not presented in a multiple choice fashion),
    instead they are possible answers.
    Question types with this type of answers are often graded via text equality or manually
    (where these answers would serve as a guide/rubric).
    """

    def __init__(self,
            options: typing.Union[typing.List[TextOption], None] = None,
            *args: typing.Any,
            **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

        if (options is None):
            options = []

        self.options: typing.List[TextOption] = options
        """ The possible text options. """

    def shuffle(self, rng: random.Random) -> None:
        rng.shuffle(self.options)

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        return [option.to_pod(context) for option in self.options]

    def _serialization_is_empty(self) -> bool:
        """ A special method for the serialization library to check. """

        return (len(self.options) == 0)

    def get_first_option_text(self) -> quizcomp.parser.document.ParsedDocument:
        """
        Get the text document for the first option.
        If there is no option, return an empty document.
        """

        if (len(self.options) == 0):
            return quizcomp.parser.document.ParsedDocument()

        return self.options[0].text

    @classmethod
    def from_pod(cls: typing.Type[TextAnswers],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) -> TextAnswers:
        if (data is None):
            return TextAnswers()

        if (isinstance(data, str)):
            parsed_text = quizcomp.parser.document.ParsedDocument.parse_text(data, context)
            return TextAnswers([TextOption(parsed_text, None)])

        if (isinstance(data, dict)):
            data = [data]

        quizcomp.errors.check_type(data, list, "'answers'", context = context)

        if (len(data) == 0):
            return TextAnswers()

        options = []
        for (i, raw_option) in enumerate(data):
            label = f"Choice at index {i}"

            option = TextOption.from_pod_with_error(raw_option, context, label)
            options.append(option)

        return TextAnswers(options)

class MultiplePartTextAnswers(QuestionAnswers):
    """
    Answers that have multiple parts, each having their own text-based answers.
    """

    def __init__(self,
            parts: typing.Dict[str, TextAnswers],
            *args: typing.Any,
            **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

        self.parts: typing.Dict[str, TextAnswers] = parts
        """ The different parts of this question. """

    def shuffle(self, rng: random.Random) -> None:
        for part in self.parts.values():
            part.shuffle(rng)

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        return {key: value.to_pod(context) for (key, value) in self.parts.items()}

    @classmethod
    def from_pod(cls: typing.Type[MultiplePartTextAnswers],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) -> MultiplePartTextAnswers:
        quizcomp.errors.check_type(data, dict, "'answers'", context = context)

        parts = {}
        for (key, raw_options) in data.items():
            # Try to parse the key, even though we are not storing it right now.
            quizcomp.parser.document.ParsedDocument.parse_text(key, context)

            parts[key] = TextAnswers.from_pod(raw_options, context)

        return MultiplePartTextAnswers(parts)

class ChoiceAnswers(QuestionAnswers):
    """ Answers that include a finite set of choices. """

    def __init__(self,
            choices: typing.List[Choice],
            *args: typing.Any,
            **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

        self.choices: typing.List[Choice] = choices
        """ The possible choices. """

    def shuffle(self, rng: random.Random) -> None:
        rng.shuffle(self.choices)

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        return [choice.to_pod(context) for choice in self.choices]

    def get_choices_with_markers(self) -> typing.List[typing.Tuple[quizcomp.parser.document.ParsedDocument, Choice]]:
        """ Get the choices for this answer along with markers for each (e.g., "A", "B", "C"). """

        return [(quizcomp.parser.document.ParsedDocument.parse_text(DEFAULT_CHOICES[i]), choice) for (i, choice) in enumerate(self.choices)]

    @classmethod
    def from_pod(cls: typing.Type[ChoiceAnswers],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) -> ChoiceAnswers:
        min_correct = context.extra.get('min_correct', 0)
        max_correct = context.extra.get('max_correct', MAX_CHOICES)
        min_incorrect = context.extra.get('min_incorrect', 0)
        max_incorrect = context.extra.get('max_incorrect', MAX_CHOICES)

        quizcomp.errors.check_type(data, list, "'answers'", context = context)

        raw_choices: typing.List[typing.Any] = typing.cast(list, data)

        if (len(raw_choices) == 0):
            raise quizcomp.errors.QuestionValidationError("No answers provided, at least one answer required.", context = context)

        num_correct = 0
        num_incorrect = 0

        choices = []

        for (i, raw_choice) in enumerate(raw_choices):
            label = f"Choice at index {i}"

            quizcomp.errors.check_type(raw_choice, dict, label, context = context)

            raw_correct = raw_choice.get('correct', None)
            if (raw_correct is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} has no 'correct' field set.", context = context)

            correct = edq.util.parse.soft_boolean(raw_correct)
            if (correct is None):
                raise quizcomp.errors.QuestionValidationError(f"{label}'s 'correct' field does not contain a boolean: '{raw_correct}'.")

            if (correct):
                num_correct += 1
            else:
                num_incorrect += 1

            option = TextOption.from_pod_with_error(raw_choice, context, label)
            choices.append(Choice(option.text, correct, option.feedback))

        if (num_correct < min_correct):
            raise quizcomp.errors.QuestionValidationError(("Did not find enough correct choices."
                + f" Expected at least {min_correct}, found {num_correct}."),
                context = context)

        if (num_correct > max_correct):
            raise quizcomp.errors.QuestionValidationError(("Found too many correct choices."
                + f" Expected at most {max_correct}, found {num_correct}."),
                context = context)

        if (num_incorrect < min_incorrect):
            raise quizcomp.errors.QuestionValidationError(("Did not find enough incorrect choices."
                + f" Expected at least {min_incorrect}, found {num_incorrect}."),
                context = context)

        if (num_incorrect > max_incorrect):
            raise quizcomp.errors.QuestionValidationError(("Found too many incorrect choices."
                + f" Expected at most {max_incorrect}, found {num_incorrect}."),
                context = context)

        return ChoiceAnswers(choices)

class TFAnswers(ChoiceAnswers):
    """ Answers that must be true or false. """

    def __init__(self,
            *args: typing.Any,
            **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

    @classmethod
    def from_pod(cls: typing.Type[TFAnswers],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) ->  TFAnswers:
        if (isinstance(data, bool)):
            choices = [
                Choice(quizcomp.parser.document.ParsedDocument.parse_text("True", context), data),
                Choice(quizcomp.parser.document.ParsedDocument.parse_text("False", context), (not data)),
            ]
            return TFAnswers(choices)

        context.extra['min_correct'] = 1
        context.extra['max_correct'] = 1
        context.extra['min_incorrect'] = 1
        context.extra['max_incorrect'] = 1

        answers = ChoiceAnswers.from_pod(data, context)

        return TFAnswers(answers.choices)

class MultiplePartChoiceAnswers(QuestionAnswers):
    """
    Answers that have multiple parts, each having their own choice-based answers.
    """

    def __init__(self,
            parts: typing.Dict[str, ChoiceAnswers],
            *args: typing.Any,
            **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

        self.parts: typing.Dict[str, ChoiceAnswers] = parts
        """ The different parts of this question. """

    def shuffle(self, rng: random.Random) -> None:
        for part in self.parts.values():
            part.shuffle(rng)

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        return {key: value.to_pod(context) for (key, value) in self.parts.items()}

    @classmethod
    def from_pod(cls: typing.Type[MultiplePartTextAnswers],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) -> MultiplePartTextAnswers:
        quizcomp.errors.check_type(data, dict, "'answers'", context = context)

        parts = {}
        for (key, raw_options) in data.items():
            # Try to parse the key, even though we are not storing it right now.
            quizcomp.parser.document.ParsedDocument.parse_text(key, context)

            parts[key] = ChoiceAnswers.from_pod(raw_options, context)

        return MultiplePartChoiceAnswers(parts)

class MatchingAnswerRow:
    """
    A single "row" when writing out a matching problem as a table.
    """

    def __init__(self,
            left: typing.Union[TextOption, None],
            right: TextOption,
            right_marker: quizcomp.parser.document.ParsedDocument,
            correct_marker: typing.Union[quizcomp.parser.document.ParsedDocument, None],
            correct_option: typing.Union[TextOption, None],
            ) -> None:
        self.left: typing.Union[TextOption, None] = left
        """
        The query part of the match that needs to find its partner.
        This may be None if there are distractors.
        """

        self.right: TextOption = right
        """
        The target part of the match.
        Note that this may NOT be the correct partner to `self.left`,
        it is just the target that should appear on the same row.
        """

        self.right_marker: quizcomp.parser.document.ParsedDocument = right_marker
        """
        The marker that accompanies this target.
        """

        self.correct_marker: typing.Union[quizcomp.parser.document.ParsedDocument, None] = correct_marker
        """
        The marker for the correct partner to `self.left`.
        Will be None if `self.left` is None.
        """

        self.correct_option: typing.Union[TextOption, None] = correct_option
        """
        The text for the correct partner to `self.left`.
        Will be None if `self.left` is None.
        """

class MatchingAnswers(QuestionAnswers):
    """ Answers for matching-type questions. """

    serialization_omit_empty = True
    serialization_skip_fields = {
        '_shuffle_seed',
    }

    def __init__(self,
            pairs: typing.List[typing.Tuple[TextOption, TextOption]],
            distractors: typing.Union[typing.List[TextOption], None] = None,
            *args: typing.Any,
            **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

        self.pairs: typing.List[typing.Tuple[TextOption, TextOption]] = pairs
        """ The matching pairs of items. """

        if (distractors is None):
            distractors = []

        self.distractors: typing.List[TextOption] = distractors
        """ Extra options to serve as a distraction. """

        self._shuffle_seed: typing.Union[int, None] = None
        """
        A seed to use when shuffling the left and right sides.

        This will be set in shuffle().
        A None value indicates that no shuffling will occur.
        """

    def shuffle(self, rng: random.Random) -> None:
        rng.shuffle(self.pairs)
        rng.shuffle(self.distractors)
        self._shuffle_seed = rng.randint(0, 2**64)

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        return {
            'matches': [[left.to_pod(context), right.to_pod(context)] for (left, right) in self.pairs],
            'distractors': [value.to_pod(context) for value in self.distractors],
        }

    def get_tabular_options(self) -> typing.List[MatchingAnswerRow]:
        """
        Get all the matching options laid out in a table.

        If shuffle() was called on this object, then the left and right options will he shuffled before being put into the table.
        """

        lefts = []
        rights = []

        for (left, right) in self.pairs:
            lefts.append(left)
            rights.append(right)

        for distractor in self.distractors:
            rights.append(distractor)

        # The ordered indexes to use in the options table.
        # This may be shuffled.
        left_indexes = list(range(len(lefts)))
        right_indexes = list(range(len(rights)))

        if (self._shuffle_seed is not None):
            rng = random.Random(self._shuffle_seed)
            rng.shuffle(left_indexes)
            rng.shuffle(right_indexes)

        options = []
        for (i, right_index) in enumerate(right_indexes):
            right = rights[right_index]
            right_marker = quizcomp.parser.document.ParsedDocument.parse_text(DEFAULT_CHOICES[i])

            left = None
            left_marker = None
            correct_answer = None
            if (i < len(left_indexes)):
                left_index = left_indexes[i]

                # Find the correct marker index for this left by looking up the matching index in the right indexes.
                matching_right_marker_index = right_indexes.index(left_index)

                left = lefts[left_index]
                left_marker = quizcomp.parser.document.ParsedDocument.parse_text(DEFAULT_CHOICES[matching_right_marker_index])
                correct_answer = rights[left_index]

            options.append(MatchingAnswerRow(left, right, right_marker, left_marker, correct_answer))

        return options

    @classmethod
    def from_pod(cls: typing.Type[MatchingAnswers],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) -> MatchingAnswers:
        quizcomp.errors.check_type(data, dict, "'answers'", context = context)

        raw_matches = data.get('matches', None)
        if (raw_matches is None):
            raise quizcomp.errors.QuestionValidationError("The 'matches' key was not provided for a matching-type question.", context = context)

        quizcomp.errors.check_type(raw_matches, list, "'matches'", context = context)

        if (len(raw_matches) == 0):
            raise quizcomp.errors.QuestionValidationError("At least one matching pair must be specified for matching questions.", context = context)

        pairs = []
        for (i, raw_match) in enumerate(raw_matches):
            label = f"Match pair at index {i}"

            if (isinstance(raw_match, list)):
                if (len(raw_match) != 2):
                    raise quizcomp.errors.QuestionValidationError(
                        f"{label} has an unexpected size. Expecting two items (left and right) found {len(raw_match)}.",
                        context = context)

                left_option = TextOption.from_pod_with_error(raw_match[0], context, label + ' (left)')
                right_option = TextOption.from_pod_with_error(raw_match[1], context, label + ' (right)')

                pairs.append((left_option, right_option))
            elif (isinstance(raw_match, dict)):
                if ('left' not in raw_match):
                    raise quizcomp.errors.QuestionValidationError(
                        f"{label} does not have a 'left' key.",
                        context = context)

                if ('right' not in raw_match):
                    raise quizcomp.errors.QuestionValidationError(
                        f"{label} does not have a 'right' key.",
                        context = context)

                left_option = TextOption.from_pod_with_error(raw_match['left'], context, label + ' (left)')
                right_option = TextOption.from_pod_with_error(raw_match['right'], context, label + ' (right)')

                pairs.append((left_option, right_option))
            else:
                raise quizcomp.errors.QuestionValidationError(
                    f"{label} has an unknown format (not a list or dict): '{raw_match}' (type: {type(raw_match)}.",
                    context = context)

        raw_distractors = data.get('distractors', None)
        if (raw_distractors is None):
            raw_distractors = []

        quizcomp.errors.check_type(raw_distractors, list, "'distractors'", context = context)

        distractors = []
        for (i, raw_distractor) in enumerate(raw_distractors):
            label = f"Match distractor at index {i}"

            option = TextOption.from_pod_with_error(raw_distractor, context, label)
            distractors.append(option)

        if ((len(pairs) + len(distractors)) > MAX_CHOICES):
            raise quizcomp.errors.QuestionValidationError(
                f"Matching question has too many options. Found {(len(pairs) + len(distractors))}, while the max is {MAX_CHOICES}.",
                context = context)

        return MatchingAnswers(pairs, distractors)

class NumericAnswers(QuestionAnswers):
    """ Answers that include a finite set of numeric options. """

    def __init__(self,
            options: typing.List[NumericOption],
            *args: typing.Any,
            **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)

        self.options: typing.List[NumericOption] = options
        """ The possible options. """

    def shuffle(self, rng: random.Random) -> None:
        rng.shuffle(self.options)

    def get_first_option_text(self) -> quizcomp.parser.document.ParsedDocument:
        """
        Get the text document for the first option.
        If there is no option, return an empty document.
        """

        if (len(self.options) == 0):
            return quizcomp.parser.document.ParsedDocument()

        return self.options[0].to_text().text

    def to_pod(self,
            context: typing.Union[edq.util.serial.SerializationContext, None] = None,
            ) -> edq.util.serial.PODType:
        return [option.to_pod(context) for option in self.options]

    @classmethod
    def from_pod(cls: typing.Type[MultiplePartTextAnswers],
            data: PODType,
            context: edq.util.serial.SerializationContext,
            ) -> MultiplePartTextAnswers:
        quizcomp.errors.check_type(data, list, "'answers'", context = context)

        raw_options: typing.List[typing.Any] = typing.cast(list, data)

        if (len(raw_options) == 0):
            raise quizcomp.errors.QuestionValidationError("No answers provided, at least one answer required.", context = context)

        options = []
        for (i, raw_option) in enumerate(raw_options):
            label = f"Option at index {i}"

            option = NumericOption.from_pod_with_error(raw_option, context, label)
            options.append(option)

        return NumericAnswers(options)
