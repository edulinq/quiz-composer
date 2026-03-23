import abc
import copy
import importlib
import logging
import os
import pkgutil
import random
import re
import typing

import edq.util.dirent

import quizcomp.common
import quizcomp.constants
import quizcomp.model.question
import quizcomp.model.text
import quizcomp.parser.document
import quizcomp.parser.public
import quizcomp.util.serial

BASE_MODULE_NAME: str = 'quizcomp.question'
THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

MAX_CHOICES: int = 2**64

class Question(quizcomp.util.serial.JSONSerializer):
    """ The base question class. """

    # {question_type: class, ...}
    _types: typing.Dict[str, typing.Type] = {}
    """ The known/seen question types. """

    _imported_this_package: bool = False
    """ Thether this module has already been imported. """

    def __init_subclass__(cls, question_type: typing.Union[str, None] = None, **kwargs: typing.Any) -> None:
        """
        Register question subclasses (types).
        """

        super().__init_subclass__(**kwargs)

        if (question_type is None):
            raise quizcomp.common.QuizValidationError("No question type provided for question subclass.")

        cls._types[question_type] = cls

    def __init__(self,
            question_type: quizcomp.model.question.QuestionType,
            prompt: typing.Union[str, None] = None,
            prompt_path: typing.Union[str, None] = None,
            answers: typing.Any = None,
            base_dir: str = '.',
            points: float = 0,
            name: str = '',
            shuffle_answers: bool = True,
            custom_header: typing.Union[str, None] = None,
            skip_numbering: typing.Union[bool, None] = None,
            hints: typing.Union[typing.Dict[str, typing.Any], None] = None,
            feedback: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ids: typing.Union[typing.Dict[str, typing.Any], None] = None,
            **kwargs: typing.Any) -> None:
        super().__init__(type = quizcomp.constants.TYPE_QUESTION, **kwargs)

        self.question_type: quizcomp.model.question.QuestionType = question_type
        """ The type of this question. """

        self._raw_prompt: typing.Union[str, None] = prompt
        """ The raw (unparsed) prompt. """

        self.prompt: quizcomp.model.text.ParsedTextWithFeedback = quizcomp.model.text.ParsedTextWithFeedback()
        """ The parsed prompt. """

        self._prompt_path: typing.Union[str, None] = prompt_path
        """ The path to the prompt file file. """

        self.answers: typing.Any = answers
        """ The answers for this question. """

        self.base_dir: str = base_dir
        """ The base directory (typically where question.json lives). """

        self.points: float = points
        """ The number of points possible. """

        self.name: str = name
        """ The name. """

        self.shuffle_answers: bool = shuffle_answers
        """ Whether the answers should be shuffled. """

        self.custom_header: typing.Union[str, None] = custom_header
        """ A custom header, instead of something generic like "Question 4". """

        self.skip_numbering: typing.Union[bool, None] = skip_numbering
        """ Whether to skip numbering. """

        if (hints is None):
            hints = {}

        self.hints: typing.Dict[str, typing.Any] = hints
        """ Rendering hints. """

        if (feedback is None):
            feedback = {}

        self.feedback: typing.Dict[str, typing.Any] = feedback
        """ Question-level feedback. """

        if (ids is None):
            ids = {}

        self.ids: typing.Dict[str, typing.Any] = ids.copy()
        """ Identifiers for this question. """

        self.ids['base_dir'] = base_dir

        try:
            self.validate()
        except Exception as ex:
            ids = self.ids.copy()
            ids['name'] = self.name
            ids['question_type'] = self.question_type

            raise quizcomp.common.QuizValidationError('Error while validating question.', ids = ids) from ex

    def _validate(self, **kwargs: typing.Any) -> None:
        """ Check that this question is valid. """

        self._validate_prompt()
        self._validate_question_feedback()
        self._validate_answers()

        if (self.hints is None):
            self.hints = {}
        else:
            self._check_type(self.hints, dict, "'hints'")

    @abc.abstractmethod
    def _validate_answers(self) -> None:
        """ Validate the answers for this question. """

    def _validate_prompt(self) -> None:
        """
        The prompt is allowed to appear (in order of priority):
        in the prompt field, be pointed to by the _prompt_path member, or be in ./quizcomp.constants.PROMPT_FILENAME.
        Both None and empty/white strings are ignored.

        Will raise an exception on an empty prompt.
        If this method does not raise an exception, the result will be placed in self.prompt.
        If the prompt is loaded from a file, self._prompt_path will be set with the absolute path.
        """

        text = self._get_prompt_text()

        self.prompt = self._validate_text_item(text, 'question prompt', check_feedback = False, allow_empty = False)

    def _get_prompt_text(self) -> str:
        """ Collect the prompt text from this question. """

        # First check self._raw_prompt.
        text = self._raw_prompt
        if (text is None):
            text = ''

        text = text.strip()

        if (text != ''):
            return text

        # Next, check for prompt files.

        check_paths = [self._prompt_path, quizcomp.constants.PROMPT_FILENAME]
        for path in check_paths:
            if ((path is None) or (path.strip() == '')):
                continue

            if (not os.path.isabs(path)):
                path = os.path.join(self.base_dir, path)

            path = os.path.abspath(path)
            if (not os.path.exists(path)):
                continue

            logging.debug("Loading question prompt from '%s'.", path)
            self._prompt_path = path
            return edq.util.dirent.read_file(path)

        raise quizcomp.common.QuestionValidationError("Could not find any non-empty prompt.", ids = self.ids)

    def inherit_from_group(self, group_info: typing.Dict[str, typing.Any]) -> None:
        """
        Inherit attributes from a group's info (`group.to_dict()`).
        """

        self.points = group_info['points']
        self.name = group_info['name']

        if (group_info['custom_header'] is not None):
            self.custom_header = group_info['custom_header']

        if (group_info['skip_numbering'] is not None):
            self.skip_numbering = group_info['skip_numbering']

        self.shuffle_answers = (self.shuffle_answers and group_info['shuffle_answers'])

        self.add_hints(group_info['hints'])

    def add_hints(self, new_hints: typing.Union[typing.Dict[str, typing.Any], None], override: bool = False) -> None:
        """ Add hints to this question. """

        if (new_hints is None):
            return

        for (key, value) in new_hints.items():
            if (override or (key not in self.hints)):
                self.hints[key] = value

    def collect_file_paths(self) -> typing.List[str]:
        """ Collect the file paths represented in this question. """

        paths: typing.List[str] = []

        for document in self._collect_documents([self.prompt, self.answers]):
            paths += document.collect_file_paths(self.base_dir)

        return paths

    def _collect_documents(self, target: typing.Any) -> typing.List[quizcomp.parser.document.ParsedDocument]:
        """ Collect the documents in this object. """

        if (isinstance(target, dict)):
            return self._collect_documents(list(target.values()))
        elif (isinstance(target, list)):
            documents = []
            for value in target:
                documents += self._collect_documents(value)
            return documents
        elif (isinstance(target, quizcomp.model.text.ParsedText)):
            return [target.document]
        else:
            return []

    def should_skip_numbering(self) -> bool:
        """ Check if this question should skip numbering. """

        return ((self.skip_numbering is not None) and (self.skip_numbering))

    def copy(self) -> 'Question':
        """ Make a deep copy of this question. """

        return copy.deepcopy(self)

    def shuffle(self, rng: typing.Union[random.Random, None] = None) -> None:
        """ Shuffle answers. """

        if (not self.shuffle_answers):
            return

        if (rng is None):
            rng = random.Random()

        self._shuffle(rng)

    def _shuffle(self, rng: random.Random) -> None:
        """
        Shuffle the answers for this question.
        By default (this method), no shuffling is performed.
        Children can override this method to support shuffling.
        """

    def _shuffle_answers_list(self, rng: random.Random) -> None:
        """
        A shuffle method for question types that are a simple list.
        """

        rng.shuffle(self.answers)

    # Override the class method JSONSerializer.from_dict() with a static method
    # so that we can select the correct child class.
    @staticmethod
    def from_dict(  # type: ignore[override] # pylint: disable=arguments-renamed
            data: typing.Dict[str, typing.Any],
            base_dir: typing.Union[str, None] = None,
            ids: typing.Union[typing.Dict[str, typing.Any], None] = None,
            **kwargs: typing.Any) -> 'Question':
        if (ids is None):
            ids = {}

        if (base_dir is not None):
            data['base_dir'] = base_dir
        elif ('base_dir' not in data):
            data['base_dir'] = '.'

        question_type = data.get('question_type', None)
        if (question_type is None):
            raise quizcomp.common.QuizValidationError("Question does not contain a 'question_type' field.", ids = ids)

        question_class = Question._fetch_question_class(question_type, ids = ids, **kwargs)
        question: 'Question' = quizcomp.util.serial._from_dict(question_class, data, ids = ids, **kwargs)
        return question

    @staticmethod
    def _fetch_question_class(
            question_type: str,
            ids: typing.Union[typing.Dict[str, typing.Any], None] = None,
            **kwargs: typing.Any) -> typing.Type:
        """ Get the class for the specified question type. """

        if (ids is None):
            ids = {}

        if (not Question._imported_this_package):
            for _, name, is_package in pkgutil.iter_modules([THIS_DIR]):
                if (is_package):
                    continue

                module_name = BASE_MODULE_NAME + '.' + name
                importlib.import_module(module_name)

            _imported_this_package = True

        if (question_type not in Question._types):
            ids = ids.copy()
            ids['question_type'] = question_type

            raise quizcomp.common.QuizValidationError("Unknown question type.", ids = ids)

        return Question._types[question_type]

    def _validate_question_feedback(self) -> None:
        """ Check that the feedback on this question is valid. """

        if (self.feedback is None):
            self.feedback = {}
            return

        if (isinstance(self.feedback, str)):
            self.feedback = {'general': self.feedback}

        self._check_type(self.feedback, dict, "'feedback'")

        allowed_keys = ['general', 'correct', 'incorrect']
        actual_keys = list(self.feedback.keys())

        bad_keys = list(sorted(set(actual_keys) - set(allowed_keys)))
        if (len(bad_keys) > 0):
            raise quizcomp.common.QuestionValidationError(
                    f"Unknown keys in feedback ({bad_keys}). Allowed keys: {allowed_keys}.", ids = self.ids)

        new_feedback = {}
        for (key, value) in self.feedback.items():
            item = self._validate_feedback_item(value, f"'{key}' feedback value")
            if (item is not None):
                new_feedback[key] = item

        self.feedback = new_feedback

    def _validate_feedback_item(self,
            item: typing.Union[str, quizcomp.model.text.ParsedText, None],
            label: str,
            ) -> typing.Union[quizcomp.model.text.ParsedText, None]:
        """ Parse and return the given feedback text. """

        if ((item is None) or isinstance(item, quizcomp.model.text.ParsedText)):
            # Nothing to do.
            return item

        self._check_type(item, str, label)

        item = item.strip()
        if (len(item) == 0):
            return None

        return quizcomp.parser.public.parse_text(item, base_dir = self.base_dir)

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

        If no exception is raised, a quizcomp.model.text.ParsedTextWithFeedback (child of quizcomp.model.text.ParsedText)
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
