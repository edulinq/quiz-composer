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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        if (self.feedback is None):
            return self.text.to_pod()

        return {
            'text': self.text.to_pod(),
            'feedback': self.feedback.to_pod(),
        }

    @classmethod
    def from_pod(cls: typing.Type[TextOption],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> TextOption:
        if (serialization_options is None):
            serialization_options = {}

        label = serialization_options.get('label', '')
        base_dir = serialization_options.get('base_dir', None)

        if (isinstance(data, str)):
            parsed_text = quizcomp.parser.document.ParsedDocument.parse_text(data, base_dir = base_dir)
            return TextOption(parsed_text, None)

        if (not isinstance(data, dict)):
            raise quizcomp.errors.QuestionValidationError(
                f"{label} has text in an unknown format (not a string or dict): '{data}' (type: {type(data)}.",
                base_dir = base_dir)

        raw_text = data.get('text', None)
        if (raw_text is None):
            raise quizcomp.errors.QuestionValidationError(f"{label} has no 'text' field set.", base_dir = base_dir)

        parsed_text = quizcomp.parser.document.ParsedDocument.parse_text(raw_text, base_dir = base_dir)
        feedback = quizcomp.model.feedback.Feedback.from_raw_data(data.get('feedback', None), base_dir = base_dir)

        return TextOption(parsed_text, feedback)

    @classmethod
    def from_pod_with_error(cls: typing.Type[TextOption],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None],
            label: str,
            base_dir: typing.Union[str, None],
            ) -> TextOption:
        """ Wrap from_pod() with some error information. """

        if (serialization_options is None):
            serialization_options = {}
        else:
            serialization_options = serialization_options.copy()

        serialization_options['label'] = label
        serialization_options['base_dir'] = base_dir

        return cls.from_pod(data, serialization_options)

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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> NumericOption:
        if (serialization_options is None):
            serialization_options = {}

        label = serialization_options.get('label', '')
        base_dir = serialization_options.get('base_dir', None)

        quizcomp.errors.check_type(data, dict, label, base_dir = base_dir)

        answer_type = data.get('type', None)
        if (not edq.util.enum.has_value(NumericAnswerType, answer_type)):
            raise quizcomp.errors.QuestionValidationError(f"{label} has an unknown answer type: '{answer_type}'.", base_dir = base_dir)

        feedback = quizcomp.model.feedback.Feedback.from_raw_data(data.get('feedback', None), base_dir = base_dir)

        if (answer_type == NumericAnswerType.EXACT):
            value = data.get('value', None)
            if (value is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'value' key.", base_dir = base_dir)

            if (not isinstance(value, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'value' that is not an int or float, found '{type(value)}'.", base_dir = base_dir)

            margin = data.get('margin', 0.0)
            if (not isinstance(margin, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'margin' that is not an int or float, found '{type(margin)}'.", base_dir = base_dir)

            return NumericOptionExact(value, margin, feedback = feedback)
        elif (answer_type == NumericAnswerType.RANGE):
            min = data.get('min', None)
            if (min is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'min' key.", base_dir = base_dir)

            if (not isinstance(min, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'min' that is not an int or float, found '{type(min)}'.", base_dir = base_dir)

            max = data.get('max', None)
            if (max is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'max' key.", base_dir = base_dir)

            if (not isinstance(max, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'max' that is not an int or float, found '{type(max)}'.", base_dir = base_dir)

            return NumericOptionRange(min, max, feedback = feedback)
        elif (answer_type == NumericAnswerType.PRECISION):
            value = data.get('value', None)
            if (value is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'value' key.", base_dir = base_dir)

            if (not isinstance(value, (int, float))):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'value' that is not an int or float, found '{type(value)}'.", base_dir = base_dir)

            precision = data.get('precision', None)
            if (precision is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} does not have a required 'precision' key.", base_dir = base_dir)

            if (not isinstance(precision, int)):
                raise quizcomp.errors.QuestionValidationError(f"{label} has a 'precision' that is not an int, found '{type(precision)}'.", base_dir = base_dir)

            return NumericOptionPrecision(value, precision, feedback = feedback)
        else:
            raise quizcomp.errors.QuestionValidationError(f"{label} has an unknown answer type: '{answer_type}'.", base_dir = base_dir)

    @classmethod
    def from_pod_with_error(cls: typing.Type[NumericOption],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None],
            label: str,
            base_dir: typing.Union[str, None],
            ) -> NumericOption:
        """ Wrap from_pod() with some error information. """

        if (serialization_options is None):
            serialization_options = {}
        else:
            serialization_options = serialization_options.copy()

        serialization_options['label'] = label
        serialization_options['base_dir'] = base_dir

        return cls.from_pod(data, serialization_options)

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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        data = {
            'text': self.text.to_pod(),
            'correct': self.correct,
        }

        if (self.feedback is not None):
            data['feedback'] = self.feedback.to_pod()

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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> QuestionAnswers:
        """
        Create an answers object for a specific question type from some serialized data
        This data will normally come from a JSON file.
        Because of the differing nature of questions, several different forms of answers may need to be processed
        (even for the same question type).

        This function will not return a generic QuestionAnswers, but a subclass of QuestionAnswers.
        """

        if (serialization_options is None):
            serialization_options = {}

        raw_question_type = serialization_options.get('question_type', None)
        base_dir = serialization_options.get('base_dir', None)

        if (raw_question_type is None):
            raise quizcomp.errors.QuestionValidationError("Could not parse question answers because of lack of question type.", base_dir = base_dir)

        question_type = quizcomp.model.constants.QuestionType(raw_question_type)

        if (question_type == quizcomp.model.constants.QuestionType.ESSAY):
            return TextAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.FIMB):
            return MultiplePartTextAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.FITB):
            return TextAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.MA):
            serialization_options = serialization_options.copy()
            serialization_options['min_correct'] = 0
            return ChoiceAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.MATCHING):
            return MatchingAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.MCQ):
            serialization_options = serialization_options.copy()
            serialization_options['min_correct'] = 1
            serialization_options['max_correct'] = 1
            return ChoiceAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.MDD):
            serialization_options = serialization_options.copy()
            serialization_options['min_correct'] = 1
            serialization_options['max_correct'] = 1
            return MultiplePartChoiceAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.NUMERICAL):
            return NumericAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.SA):
            return TextAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.TEXT_ONLY):
            return TextAnswers.from_pod(data, serialization_options)
        elif (question_type == quizcomp.model.constants.QuestionType.TF):
            return TFAnswers.from_pod(data, serialization_options)
        else:
            raise quizcomp.errors.QuestionValidationError(f"Unknown question type: '{raw_question_type}'.", base_dir = base_dir)

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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return [option.to_pod() for option in self.options]

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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> TextAnswers:
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', None)

        if (data is None):
            return TextAnswers()

        if (isinstance(data, str)):
            parsed_text = quizcomp.parser.document.ParsedDocument.parse_text(data, base_dir = base_dir)
            return TextAnswers([TextOption(parsed_text, None)])

        if (isinstance(data, dict)):
            data = [data]

        quizcomp.errors.check_type(data, list, "'answers'", base_dir = base_dir)

        if (len(data) == 0):
            return TextAnswers()

        options = []
        for (i, raw_option) in enumerate(data):
            label = f"Choice at index {i}"

            option = TextOption.from_pod_with_error(raw_option, serialization_options, label, base_dir)
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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return {key: value.to_pod() for (key, value) in self.parts.items()}

    @classmethod
    def from_pod(cls: typing.Type[MultiplePartTextAnswers],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> MultiplePartTextAnswers:
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', None)

        quizcomp.errors.check_type(data, dict, "'answers'", base_dir = base_dir)

        parts = {}
        for (key, raw_options) in data.items():
            # Try to parse the key, even though we are not storing it right now.
            quizcomp.parser.document.ParsedDocument.parse_text(key, base_dir = base_dir)

            parts[key] = TextAnswers.from_pod(raw_options, serialization_options)

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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return [choice.to_pod() for choice in self.choices]

    def get_choices_with_markers(self) -> typing.List[typing.Tuple[quizcomp.parser.document.ParsedDocument, Choice]]:
        """ Get the choices for this answer along with markers for each (e.g., "A", "B", "C"). """

        return [(quizcomp.parser.document.ParsedDocument.parse_text(DEFAULT_CHOICES[i]), choice) for (i, choice) in enumerate(self.choices)]

    @classmethod
    def from_pod(cls: typing.Type[MultiplePartTextAnswers],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> MultiplePartTextAnswers:
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', None)
        min_correct = serialization_options.get('min_correct', 0)
        max_correct = serialization_options.get('max_correct', MAX_CHOICES)
        min_incorrect = serialization_options.get('min_incorrect', 0)
        max_incorrect = serialization_options.get('max_incorrect', MAX_CHOICES)

        quizcomp.errors.check_type(data, list, "'answers'", base_dir = base_dir)

        raw_choices: typing.List[typing.Any] = typing.cast(list, data)

        if (len(raw_choices) == 0):
            raise quizcomp.errors.QuestionValidationError("No answers provided, at least one answer required.", base_dir = base_dir)

        num_correct = 0
        num_incorrect = 0

        choices = []

        for (i, raw_choice) in enumerate(raw_choices):
            label = f"Choice at index {i}"

            quizcomp.errors.check_type(raw_choice, dict, label, base_dir = base_dir)

            raw_correct = raw_choice.get('correct', None)
            if (raw_correct is None):
                raise quizcomp.errors.QuestionValidationError(f"{label} has no 'correct' field set.", base_dir = base_dir)

            correct = edq.util.parse.soft_boolean(raw_correct)
            if (correct is None):
                raise quizcomp.errors.QuestionValidationError(f"{label}'s 'correct' field does not contain a boolean: '{raw_correct}'.")

            if (correct):
                num_correct += 1
            else:
                num_incorrect += 1

            option = TextOption.from_pod_with_error(raw_choice, serialization_options, label, base_dir)
            choices.append(Choice(option.text, correct, option.feedback))

        if (num_correct < min_correct):
            raise quizcomp.errors.QuestionValidationError(("Did not find enough correct choices."
                + f" Expected at least {min_correct}, found {num_correct}."),
                base_dir = base_dir)

        if (num_correct > max_correct):
            raise quizcomp.errors.QuestionValidationError(("Found too many correct choices."
                + f" Expected at most {max_correct}, found {num_correct}."),
                base_dir = base_dir)

        if (num_incorrect < min_incorrect):
            raise quizcomp.errors.QuestionValidationError(("Did not find enough incorrect choices."
                + f" Expected at least {min_incorrect}, found {num_incorrect}."),
                base_dir = base_dir)

        if (num_incorrect > max_incorrect):
            raise quizcomp.errors.QuestionValidationError(("Found too many incorrect choices."
                + f" Expected at most {max_incorrect}, found {num_incorrect}."),
                base_dir = base_dir)

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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) ->  TFAnswers:
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', None)

        if (isinstance(data, bool)):
            choices = [
                Choice(TextOption.from_pod_with_error("True", serialization_options, 'true', base_dir), data),
                Choice(TextOption.from_pod_with_error("False", serialization_options, 'false', base_dir), (not data)),
            ]
            return TFAnswers(choices)

        serialization_options['min_correct'] = 1
        serialization_options['max_correct'] = 1
        serialization_options['min_incorrect'] = 1
        serialization_options['max_incorrect'] = 1

        answers = ChoiceAnswers.from_pod(data, serialization_options)

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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return {key: value.to_pod() for (key, value) in self.parts.items()}

    @classmethod
    def from_pod(cls: typing.Type[MultiplePartTextAnswers],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> MultiplePartTextAnswers:
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', None)

        quizcomp.errors.check_type(data, dict, "'answers'", base_dir = base_dir)

        parts = {}
        for (key, raw_options) in data.items():
            # Try to parse the key, even though we are not storing it right now.
            quizcomp.parser.document.ParsedDocument.parse_text(key, base_dir = base_dir)

            parts[key] = ChoiceAnswers.from_pod(raw_options, serialization_options)

        return MultiplePartChoiceAnswers(parts)

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
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return {
            'matches': [[left.to_pod(), right.to_pod()] for (left, right) in self.pairs],
            'distractors': [value.to_pod() for value in self.distractors],
        }

    def get_tabular_options(self) -> typing.List[typing.Tuple[typing.Union[TextOption, None], TextOption, TextOption, quizcomp.parser.document.ParsedDocument]]:
        """
        Get all the options laid out in a table: (left, correct answer marker, correct answer, right, choice marker).
        The first marker maps the subquestion (left) to the correct answer.
        The second marker serves as a label for each possible choice (right).
        If there is no left option, it and its marker will be None.

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

            options.append((left, left_marker, correct_answer, right, right_marker))

        return options

    @classmethod
    def from_pod(cls: typing.Type[MatchingAnswers],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> MatchingAnswers:
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', None)

        quizcomp.errors.check_type(data, dict, "'answers'", base_dir = base_dir)

        raw_matches = data.get('matches', None)
        if (raw_matches is None):
            raise quizcomp.errors.QuestionValidationError("The 'matches' key was not provided for a matching-type question.", base_dir = base_dir)

        quizcomp.errors.check_type(raw_matches, list, "'matches'", base_dir = base_dir)

        if (len(raw_matches) == 0):
            raise quizcomp.errors.QuestionValidationError("At least one matching pair must be specified for matching questions.", base_dir = base_dir)

        pairs = []
        for (i, raw_match) in enumerate(raw_matches):
            label = f"Match pair at index {i}"

            if (isinstance(raw_match, list)):
                if (len(raw_match) != 2):
                    raise quizcomp.errors.QuestionValidationError(
                        f"{label} has an unexpected size. Expecting two items (left and right) found {len(raw_match)}.",
                        base_dir = base_dir)

                left_option = TextOption.from_pod_with_error(raw_match[0], serialization_options, label + ' (left)', base_dir)
                right_option = TextOption.from_pod_with_error(raw_match[1], serialization_options, label + ' (right)', base_dir)

                pairs.append((left_option, right_option))
            elif (isinstance(raw_match, dict)):
                if ('left' not in raw_match):
                    raise quizcomp.errors.QuestionValidationError(
                        f"{label} does not have a 'left' key.",
                        base_dir = base_dir)

                if ('right' not in raw_match):
                    raise quizcomp.errors.QuestionValidationError(
                        f"{label} does not have a 'right' key.",
                        base_dir = base_dir)

                left_option = TextOption.from_pod_with_error(raw_match['left'], serialization_options, label + ' (left)', base_dir)
                right_option = TextOption.from_pod_with_error(raw_match['right'], serialization_options, label + ' (right)', base_dir)

                pairs.append((left_option, right_option))
            else:
                raise quizcomp.errors.QuestionValidationError(
                    f"{label} has an unknown format (not a list or dict): '{raw_match}' (type: {type(raw_match)}.",
                    base_dir = base_dir)

        raw_distractors = data.get('distractors', None)
        if (raw_distractors is None):
            raw_distractors = []

        quizcomp.errors.check_type(raw_distractors, list, "'distractors'", base_dir = base_dir)

        distractors = []
        for (i, raw_distractor) in enumerate(raw_distractors):
            label = f"Match distractor at index {i}"

            option = TextOption.from_pod_with_error(raw_distractor, serialization_options, label, base_dir)
            distractors.append(option)

        if ((len(pairs) + len(distractors)) > MAX_CHOICES):
            raise quizcomp.errors.QuestionValidationError(
                f"Matching question has too many options. Found {(len(pairs) + len(distractors))}, while the max is {MAX_CHOICES}.",
                base_dir = base_dir)

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

    def to_pod(self,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return [option.to_pod() for option in self.options]

    @classmethod
    def from_pod(cls: typing.Type[MultiplePartTextAnswers],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> MultiplePartTextAnswers:
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', None)

        quizcomp.errors.check_type(data, list, "'answers'", base_dir = base_dir)

        raw_options: typing.List[typing.Any] = typing.cast(list, data)

        if (len(raw_options) == 0):
            raise quizcomp.errors.QuestionValidationError("No answers provided, at least one answer required.", base_dir = base_dir)

        options = []
        for (i, raw_option) in enumerate(raw_options):
            label = f"Option at index {i}"

            option = NumericOption.from_pod_with_error(raw_option, serialization_options, label, base_dir)
            options.append(option)

        return NumericAnswers(options)
