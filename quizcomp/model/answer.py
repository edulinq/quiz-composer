import string
import typing

import edq.util.serial

import quizcomp.errors
import quizcomp.model.feedback

MAX_CHOICES: int = len(string.ascii_uppercase)

class TextOption(edq.util.serial.PODConverter):
    """
    One possible answer to a question.
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

    def to_pod(self,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return [option.to_pod() for option in self.options]

    def _serialization_is_empty(self) -> bool:
        """ A special method for the serialization library to check. """

        return (len(self.options) == 0)

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

        quizcomp.errors.check_type(data, list, "'answers'")

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

        quizcomp.errors.check_type(data, dict, "'answers'")

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

    def to_pod(self,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return [choice.to_pod() for choice in self.choices]

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

        quizcomp.errors.check_type(data, list, "'answers'")

        raw_choices: typing.List[typing.Any] = typing.cast(list, data)

        if (len(raw_choices) == 0):
            raise quizcomp.errors.QuestionValidationError("No answers provided, at least one answer required.", base_dir = base_dir)

        num_correct = 0
        num_incorrect = 0

        choices = []

        for (i, raw_choice) in enumerate(raw_choices):
            label = f"Choice at index {i}"

            quizcomp.errors.check_type(raw_choice, dict, label)

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

        quizcomp.errors.check_type(data, dict, "'answers'")

        parts = {}
        for (key, raw_options) in data.items():
            # Try to parse the key, even though we are not storing it right now.
            quizcomp.parser.document.ParsedDocument.parse_text(key, base_dir = base_dir)

            parts[key] = ChoiceAnswers.from_pod(raw_options, serialization_options)

        return MultiplePartChoiceAnswers(parts)

class MatchingAnswers(QuestionAnswers):
    """ Answers for matching-type questions. """

    serialization_omit_empty = True

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

    def to_pod(self,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> edq.util.serial.PODType:
        return {
            'pairs': [[left.to_pod(), right.to_pod()] for (left, right) in self.pairs],
            'distractors': [value.to_pod() for value in self.distractors],
        }

    @classmethod
    def from_pod(cls: typing.Type[MatchingAnswers],
            data: PODType,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> MatchingAnswers:
        if (serialization_options is None):
            serialization_options = {}

        base_dir = serialization_options.get('base_dir', None)

        quizcomp.errors.check_type(data, dict, "'answers'")

        raw_matches = data.get('matches', None)
        if (raw_matches is None):
            raise quizcomp.errors.QuestionValidationError("The 'matches' key was not provided for a matching-type question.", base_dir = base_dir)

        quizcomp.errors.check_type(raw_matches, list, "'matches'")

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

        quizcomp.errors.check_type(raw_distractors, list, "'distractors'")

        distractors = []
        for (i, raw_distractor) in enumerate(raw_distractors):
            label = f"Match distractor at index {i}"

            option = TextOption.from_pod_with_error(raw_distractor, serialization_options, label, base_dir)
            distractors.append(option)

        return MatchingAnswers(pairs, distractors)

# TEST
''' TEST
    def _validate_self_answer_list(self, min_correct: int = 0, max_correct: int = MAX_CHOICES) -> None:
        """ Check that the answers are a list with the specified range of correct choices. """

        self.answers = self._validate_answer_list(self.answers, self.base_dir,
                min_correct = min_correct, max_correct = max_correct)

    def _validate_answer_list(self,
            answers: typing.List[typing.Dict[str, typing.Any]],
            base_dir: str,
            min_correct: int = 0,
            max_correct: int = MAX_CHOICES,
            ) -> typing.List[quizcomp.model.text.ParsedTextChoice]:
        """ Check that the given answers are a list with the specified range of correct choices. """

        self._check_type(answers, list, "'answers'")

        if (len(answers) == 0):
            raise quizcomp.common.QuestionValidationError("No answers provided, at least one answer required.", ids = self.ids)

        num_correct = 0
        for answer in answers:
            if ('correct' not in answer):
                raise quizcomp.common.QuestionValidationError("Answer has no 'correct' field.", ids = self.ids)

            if ('text' not in answer):
                raise quizcomp.common.QuestionValidationError("Answer has no 'text' field.", ids = self.ids)

            if (answer['correct']):
                num_correct += 1

        if (num_correct < min_correct):
            raise quizcomp.common.QuestionValidationError(("Did not find enough correct answers."
                + f" Expected at least {min_correct}, found {num_correct}."),
                ids = self.ids)

        if (num_correct > max_correct):
            raise quizcomp.common.QuestionValidationError(("Found too many correct answers."
                + f" Expected at most {max_correct}, found {num_correct}."),
                ids = self.ids)

        new_answers = []
        for (i, answer) in enumerate(answers):
            parsed_text = self._validate_text_item(answer, f"'answers' values (element {i})")
            new_answer = quizcomp.model.text.ParsedTextChoice(parsed_text, answer['correct'])
            new_answers.append(new_answer)

        return new_answers

    def _validate_text_answers(self) -> None:
        """ Check that the answers are valid text answer. """

        possible_answers = 'null/None, string, empty list, list of strings, or list of objects'

        if (self.answers is None):
            self.answers = ['']
        elif (isinstance(self.answers, str)):
            self.answers = [self.answers]

        if (not isinstance(self.answers, list)):
            raise quizcomp.common.QuestionValidationError(
                    f"'answers' value must be {possible_answers}, found: {self.answers}.", ids = self.ids)

        if (len(self.answers) == 0):
            self.answers = ['']

        new_answers = []
        for (i, answer) in enumerate(self.answers):
            new_answers.append(self._validate_text_item(answer, f"'answers' values (element {i})"))

        self.answers = new_answers

    def _validate_text_item(self,
            item: typing.Union[str, typing.Dict[str, typing.Any], quizcomp.model.text.ParsedTextWithFeedback],
            label: str,
            check_feedback: bool = True,
            allow_empty: bool = True,
            strip: bool = True,
            clean_whitespace: bool = False,
            ) -> quizcomp.model.text.ParsedTextWithFeedback:
        """
        Validate a portion of an answer/choice/field that is a parsed string.

        Allowed values are:
         - None (will be converted to an empty string).
         - Empty String (if allow_empty is True).
         - String
         - quizcomp.model.text.ParsedTextWithFeedback (will be passed back without any checks).
         - Dict with required key 'text' and optional key 'feedback'.

        If no exception is raised, a quizcomp.model.text.ParsedTextWithFeedback (child of quizcomp.parser.document.ParsedDocument)
        will be returned, even if there is no feedback.
        """

        if (isinstance(item, quizcomp.model.text.ParsedTextWithFeedback)):
            # Nothing to do if the item is already parsed.
            return item

        if (item is None):
            item = ''

        if (isinstance(item, str)):
            item = {'text': item}

        self._check_type(item, dict, label)

        if ('text' not in item):
            raise quizcomp.common.QuestionValidationError(f"{label} is missing a 'text' key.", ids = self.ids)

        text = item['text']
        self._check_type(item['text'], str, f"{label} 'text' key")

        if (clean_whitespace):
            text = re.sub(r'\s+', ' ', text)

        if (strip):
            text = text.strip()

        if ((not allow_empty) and (text == '')):
            raise quizcomp.common.QuestionValidationError(f"{label} text is empty.", ids = self.ids)

        feedback = None
        if (check_feedback):
            feedback = self._validate_feedback_item(item.get('feedback', None), label)

        return quizcomp.model.text.ParsedTextWithFeedback(quizcomp.parser.public.parse_text(text,
                base_dir = self.base_dir), feedback = feedback)

    def _validate_fimb_answers(self) -> None:
        """ Check that the answers are valid fill in multiple blanks answers. """

        self._check_type(self.answers, dict, "'answers' key")

        if (len(self.answers) == 0):
            raise quizcomp.common.QuestionValidationError("Expected 'answers' dict to be non-empty.", ids = self.ids)

        for (key, values) in self.answers.items():
            # If this was already in the full FIMB format, then we need to pull out the values.
            if ((isinstance(values, dict)) and ('values' in values)):
                self.answers[key] = values['values']
            elif (not isinstance(values, list)):
                self.answers[key] = [values]

        new_answers = {}

        for (key, values) in self.answers.items():
            self._check_type(key, str, "key in 'answers' dict")

            if (len(values) == 0):
                raise quizcomp.common.QuestionValidationError("Expected possible values to be non-empty.", ids = self.ids)

            new_values = []
            for (i, value) in enumerate(values):
                label = f"answers key '{key}' index {i}"
                new_values.append(self._validate_text_item(value, label))

            new_answers[key] = {
                'key': quizcomp.parser.public.parse_text(key, base_dir = self.base_dir),
                'values': new_values,
            }

        self.answers = new_answers

        self._check_placeholders(self.answers.keys())

    def _check_type(self, value: typing.Any, expected_type: typing.Type, label: str) -> None:
        """ Check that the given value has the expected type. """

        if (not isinstance(value, expected_type)):
            raise quizcomp.common.QuestionValidationError(f"{label} must be a {expected_type}, found '{value}' ({type(value)}).",
                    ids = self.ids)

    def _check_placeholders(self, answer_placeholders: typing.Set[str]) -> None:
        """
        Check placeholders from the answers against placeholders in the prompt.
        """

        document_placeholders = self.prompt.document.collect_placeholders()

        # Special case for FITB documents.
        if ((len(answer_placeholders) == 1) and (list(answer_placeholders)[0] == '')):
            if (len(document_placeholders) != 0):
                output_answer_placeholders = list(sorted(answer_placeholders))
                raise quizcomp.common.QuestionValidationError(
                        f"Found placeholders ({output_answer_placeholders}) in the question prompt when none were expected.",
                        ids = self.ids)

            return

        if (answer_placeholders != document_placeholders):
            output_answer_placeholders = list(sorted(answer_placeholders))
            output_document_placeholders = list(sorted(document_placeholders))

            raise quizcomp.common.QuestionValidationError(
                    (f"Mismatch between the placeholders found in the question prompt ({output_document_placeholders})"
                        + f" and answers config ({output_answer_placeholders})."),
                    ids = self.ids)
'''

# TEST
''' TEST
class NumericChoice(edq.util.serial.DictConverter):
    """
    Numeric choices have no parsed text (aside from optional feedback).
    """

    def __init__(self,
            type: str,
            margin: typing.Union[float, None] = None,
            min: typing.Union[float, None] = None,
            max: typing.Union[float, None] = None,
            value: typing.Union[float, None] = None,
            precision: typing.Union[int, None] = None,
            feedback: typing.Union[ParsedText, None] = None,
            ) -> None:
        self.type: str = type
        """ The type of numeric answer for this choice. """

        self.margin: typing.Union[float, None] = margin
        """ The allowed/error margin. """

        self.min: typing.Union[float, None] = min
        """ The min value. """

        self.max: typing.Union[float, None] = max
        """ The max value. """

        self.value: typing.Union[float, None] = value
        """ The expected/correct value. """

        self.precision: typing.Union[int, None] = precision
        """ The number of expected significant places. """

        self.feedback: typing.Union[ParsedText, None] = feedback
        """ Feedback associated with this text. """
'''
