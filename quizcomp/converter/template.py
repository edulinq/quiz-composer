"""
The most common way to render Quiz Composer quizzes is via templates.
We use the [Jinja](https://jinja.palletsprojects.com) template system.

# TEST
The standard rendering context sent to most templates will always include:
 - `this: typing.Any` -- The context object being rendered (e.g., a quiz, group, or question).
 - `quiz: quizcomp.model.quiz.Quiz` -- The current quiz (often a variant) being rendered.
 - `answer_key: bool` -- Whether this conversion if for an answer key.

Core types (quiz, group, question) will additionally include:
 - `id: str` -- An identifier specific to this.
 - `number: int` -- The number that should be displayed for this object (if any), e.g., a question's number.
 - `children_content: str` -- The rendered content from this' children (if any).

# TEST
 - `meta: typing.Dict[str, typing.Any]` -- A dictionary of metadata relevant to the context (e.g. for a question this would contain the question number).
"""

import math
import os
import random
import re
import string
import typing

import edq.net.request
import edq.util.dirent
import jinja2

import quizcomp.constants
import quizcomp.converter.converter
import quizcomp.model.base
import quizcomp.model.config
import quizcomp.model.constants
import quizcomp.parser.document
import quizcomp.model.group
import quizcomp.model.question
import quizcomp.model.quiz

TEMPLATE_FILENAME_QUIZ: str = 'quiz.template'
TEMPLATE_FILENAME_QUESTION_SEPARATOR: str = 'question-separator.template'
TEMPLATE_FILENAME_GROUP: str = 'group.template'
TEMPLATE_FILENAME_GROUP_SEPARATOR: str = 'group-separator.template'

RIGHT_IDS: typing.List[str] = list(string.ascii_uppercase)
LEFT_IDS: typing.List[str] = [str(i + 1) for i in range(len(RIGHT_IDS))]

DEFAULT_JINJA_OPTIONS: typing.Dict[str, typing.Any] = {
    'trim_blocks': True,
    'lstrip_blocks': True,
    'autoescape': jinja2.select_autoescape(),
}

DEFAULT_ID_DELIM: str = '.'

class TemplateConverter(quizcomp.converter.converter.Converter):
    """
    The base class for a converter that uses templates.
    """

    # TEST - Check args.
    def __init__(self,
            format: str,
            template_dir: str,
            jinja_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            jinja_filters: typing.Union[typing.Dict[str, typing.Any], None] = None,
            jinja_globals: typing.Union[typing.Dict[str, typing.Any], None] = None,
            parser_format_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            image_base_dir: typing.Union[str, None] = None,
            image_relative_root: typing.Union[str, None] = None,
            cleanup_images: bool = True,
            id_delim: str = DEFAULT_ID_DELIM,
            **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

        if (not os.path.isdir(template_dir)):
            raise ValueError(f"Provided template dir ('{template_dir}') does not exist or is not a dir.")

        self.format: str = format
        """ The format being converted to. """

        self.template_dir: str = template_dir
        """ The directory containing the templates to use. """

        if (parser_format_options is None):
            parser_format_options = {}

        self.parser_format_options: typing.Dict[str, typing.Any] = parser_format_options
        """ Formatting options. """

        self.id_delim: str = id_delim
        """ The delimiter when creating internal identifiers for groups, questions, answers, etc. """

        self.image_base_dir: typing.Union[str, None] = image_base_dir
        """
        The location images are to be stored.
        Some converters will need to store image paths.
        Using the _store_images() callback will put the images here.
        """

        self.image_paths: typing.Dict[str, str] = {}
        """ This will hold: {<abs_path or link>: <new path (based on image_base_dir)>, ...} """

        self.image_relative_root: typing.Union[str, None] = image_relative_root
        """ If not None, override the default image output path with os.join(image_relative_root, filename). """

        self.cleanup_images: bool = cleanup_images
        """ Remove any temp image directories. """

        if (jinja_options is None):
            jinja_options = {}

        self.jinja_options: typing.Dict[str, typing.Any] = DEFAULT_JINJA_OPTIONS.copy()
        """ Top-level options to pass Jinja. """

        self.jinja_options.update(jinja_options)

        self.env: jinja2.Environment = jinja2.Environment(
            loader = jinja2.FileSystemLoader(self.template_dir, followlinks = True),
            **self.jinja_options,
        )
        """ The Jinja environment for this converter. """

        if (jinja_globals is None):
            jinja_globals = {}

        self.env.globals.update(jinja_globals)

        if (jinja_filters is None):
            jinja_filters = {}

        for (name, function) in jinja_filters.items():
            self.env.filters[name] = function

        self.answer_functions: typing.Dict[quizcomp.model.constants.QuestionType, str] = {
            quizcomp.model.constants.QuestionType.ESSAY: 'create_answers_essay',
            quizcomp.model.constants.QuestionType.FIMB: 'create_answers_fimb',
            quizcomp.model.constants.QuestionType.FITB: 'create_answers_fitb',
            quizcomp.model.constants.QuestionType.MA: 'create_answers_ma',
            quizcomp.model.constants.QuestionType.MATCHING: 'create_answers_matching',
            quizcomp.model.constants.QuestionType.MCQ: 'create_answers_mcq',
            quizcomp.model.constants.QuestionType.MDD: 'create_answers_mdd',
            quizcomp.model.constants.QuestionType.NUMERICAL: 'create_answers_numerical',
            quizcomp.model.constants.QuestionType.SA: 'create_answers_sa',
            quizcomp.model.constants.QuestionType.TEXT_ONLY: 'create_answers_text_only',
            quizcomp.model.constants.QuestionType.TF: 'create_answers_tf',
        }
        """
        Methods to generate answers.
        Signature: func(self, question_id, question_number, question, variant)
        """

    def convert_quiz(self, quiz: quizcomp.model.quiz.Quiz, **kwargs: typing.Any) -> str:
        """ Convert an entire quiz (including variants). """

        return self._convert_quiz(quiz)

    def convert_variant(self, variant: quizcomp.model.quiz.Variant, **kwargs: typing.Any) -> str:
        """ Convert a a standard quiz variant. """

        return self._convert_quiz(variant)

    def _convert_quiz(self, quiz: quizcomp.model.quiz.Quiz) -> str:
        """ Convert a quiz (or variant). """

        quiz_id = '0'
        quiz_number = 1

        children_content = self._convert_children(quiz, quiz, quiz_id, self._convert_group, self._convert_group_separator)

        context = {
            'this': quiz,
            'quiz': quiz,
            'answer_key': self.answer_key,
            'id': quiz_id,
            'number': quiz_number,
            'children_content': children_content,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_QUIZ)
        return template.render(**context)

    def _convert_children(self,
            quiz: quizcomp.model.quiz.Quiz,
            parent: quizcomp.model.base.CoreType,
            parent_id: str,
            convert_child_func: typing.Callable,
            convert_child_separator_func: typing.Callable,
            ) -> str:
        """ Convert a list of children. """

        last_child = None
        last_child_id = None
        lasr_child_number = None

        next_child_number = 1

        children_content = []
        for (i, child) in enumerate(parent.children):
            child_id = f"{parent_id}.{i}"

            child_number = None
            if (child.get_config(quizcomp.model.config.OPTION_SKIP_NUMBERING_KEY) is not True):
                child_number = next_child_number
                next_child_number += 1

            # Add in a separator if we are between two children.
            if (last_child is not None):
                children_content.append(convert_child_separator_func(quiz, parent, last_child, last_child_id, last_child_number, child, child_id, child_number))

            child_content = convert_child_func(quiz, child, child_id, child_number)
            children_content.append(child_content)

            last_child = child
            last_child_id = child_id
            last_child_number = child_number

            # TEST
            if (i >= 1):
                break

        return "\n".join(children_content)

    def _convert_group(self,
            quiz: quizcomp.model.quiz.Quiz,
            group: quizcomp.model.group.Group, group_id: str, group_number: typing.Union[int, None],
            ) -> str:
        """ Convert a group. """

        children_content = self._convert_children(quiz, group, group_id, self._convert_question, self._convert_question_separator)

        context = {
            'this': group,
            'quiz': quiz,
            'answer_key': self.answer_key,
            'id': group_id,
            'number': group_number,
            'children_content': children_content,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_GROUP)
        return template.render(**context)

    def _convert_group_separator(self,
            quiz: quizcomp.model.quiz.Quiz,
            parent: quizcomp.model.base.CoreType,
            previous: quizcomp.model.base.CoreType, previous_id: str, previous_number: typing.Union[int, None],
            next: quizcomp.model.base.CoreType, next_id: str, next_number: typing.Union[int, None],
            ) -> str:
        """ Create a group separator. """

        return self._convert_separator(
            TEMPLATE_FILENAME_GROUP_SEPARATOR,
            quiz, parent,
            previous, previous_id, previous_number,
            next, next_id, next_number,
        )

    def _convert_question(self,
            quiz: quizcomp.model.quiz.Quiz,
            question: quizcomp.model.question.Question, question_id: str, question_number: typing.Union[int, None],
            ) -> str:
        """ Convert a question. """

        context = {
            'this': question,
            'quiz': quiz,
            'answer_key': self.answer_key,
            'id': question_id,
            'number': question_number,
            'children_content': None,
            'custom_header': question.get_config(quizcomp.model.config.OPTION_CUSTOM_HEADER),
        }

        template = self.env.get_template(f"questions/{question.question_type}.template")
        return template.render(**context)

    def _convert_question_separator(self,
            quiz: quizcomp.model.quiz.Quiz,
            parent: quizcomp.model.base.CoreType,
            previous: quizcomp.model.base.CoreType, previous_id: str, previous_number: typing.Union[int, None],
            next: quizcomp.model.base.CoreType, next_id: str, next_number: typing.Union[int, None],
            ) -> str:
        """ Create a question separator. """

        return self._convert_separator(
            TEMPLATE_FILENAME_QUESTION_SEPARATOR,
            quiz, parent,
            previous, previous_id, previous_number,
            next, next_id, next_number,
        )

    def _convert_separator(self,
            template_name: str,
            quiz: quizcomp.model.quiz.Quiz,
            parent: quizcomp.model.base.CoreType,
            previous: quizcomp.model.base.CoreType, previous_id: str, previous_number: typing.Union[int, None],
            next: quizcomp.model.base.CoreType, next_id: str, next_number: typing.Union[int, None],
            ) -> str:
        """ Create a separator. """

        context = {
            'this': parent,
            'quiz': quiz,
            'answer_key': self.answer_key,
            'previous': previous,
            'previous_id': previous_id,
            'previous_number': previous_number,
            'next': next,
            'next_id': next_id,
            'next_number': next_number,
        }

        template = self.env.get_template(template_name)
        text = template.render(**context)

        return text

    # TEST
    ''' TEST
    def _convert_container(self, container: quizcomp.model.quiz.Quiz, container_type: typing.Type, container_label: str) -> str:
        """ Convert a quiz or variant. """

        if (not isinstance(container, container_type)):
            raise ValueError(f"Template {container_label} converter requires a {container_type}, found {type(container)}.")

        _, inner_text = self.create_groups(container)

        inner_context = container.to_pod()
        inner_context['total_points'] = container.get_points()
        inner_context['description_text'] = self._format_doc(container.description)

        context = {
            'quiz': inner_context,
            'answer_key': self.answer_key,
            'inner_text': inner_text,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_QUIZ)
        text = template.render(**context)

        return text

    def create_groups(self, quiz: quizcomp.model.quiz.Quiz) -> typing.Tuple[int, str]:
        """ Convert question groups. """

        return self._create_item_collection(quiz, 'group', 1, self.create_group)

    def _create_item_collection(self,
            container: typing.Union[quizcomp.model.quiz.Quiz, quizcomp.model.group.Group],
            label: str,
            question_number: int,
            item_creation_function: typing.Callable,
            id_prefix: typing.Union[str, None] = None,
            ) -> typing.Tuple[int, str]:
        """
        Create a collection of groups (for quizzes) or questions (for variants or inside groups)
        from a container (variant or quiz).
        """

        result = []
        for (index, item) in enumerate(container.children):
            item_id = str(index)
            if (id_prefix is not None):
                item_id = self.id_delim.join([id_prefix, item_id])

            if (index != 0):
                result.append(self.create_question_separatorarator(container))

            try:
                question_number, text = item_creation_function(item_id, question_number, item, container)
                result.append(text)
            except Exception as ex:
                raise ValueError(f"Failed to convert {label} {index} ({item_id}: {item.name}).") from ex

        return question_number, "\n\n".join(result)

    def create_group(self,
            group_index: str,
            question_number: int,
            group: quizcomp.model.group.Group,
            quiz: quizcomp.model.quiz.Quiz,
            ) -> typing.Tuple[int, str]:
        """ Convert a single group. """

        data = group.to_pod()
        data['id'] = group_index

        question_number, questions_text = self._create_item_collection(
                group, 'question', question_number, self.create_question,
                id_prefix = group_index)

        context = {
            'quiz': quiz,
            'group': data,
            'questions_text': questions_text,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_GROUP)
        text = template.render(**context)

        return question_number, text

    def create_question(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant) -> typing.Tuple[int, str]:
        """
        Convert a question to the target format.
        Return the new (current) question number and converted text.
        """

        question_type = question.question_type
        if (question_type not in self.answer_functions):
            raise ValueError(f"Unsupported question type: '{question_type}'.")

        data = question.to_pod()
        data['prompt_text'] = self._format_doc(question.prompt)
        data['id'] = question_id
        data['number'] = question_number

        # Stash the old answers and add in new ones.
        data['answers_raw'] = data['answers']
        answers_method = getattr(self, self.answer_functions[question_type])
        data['answers'] = answers_method(question_id, question_number, question, variant)

        data['feedback'] = {}
        for key, item in question.feedback.items():
            data['feedback'][key] = self._format_doc(item)

        context = {
            'quiz': variant,
            'answer_key': self.answer_key,
            'question': data,
        }

        template_name = f"{question_type}.template"
        template = self.env.get_template(template_name)

        context = self.modify_question_context(context, question, variant)
        text = template.render(**context)

        if (question.get_config(quizcomp.model.config.OPTION_SKIP_NUMBERING_KEY) is True):
            question_number += 1

        return question_number, text

    def modify_question_context(self,
            context: typing.Dict[str, typing.Any],
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant) -> typing.Dict[str, typing.Any]:
        """
        Provide an opportunity for children to modify the question context.
        The new context reference (which may be new, unchanged, or modified version of the passed-in context).
        """

        return context

    def clean_solution_content(self, document: quizcomp.parser.document.ParsedDocument) -> str:
        """
        An opportunity for children to clean the text of a solution before it is entered into a key.
        For example, tex solutions are hacky and cannot use certain functions.
        """

        return self._format_doc(document)

    def create_question_separatorarator(self, quiz: typing.Union[quizcomp.model.quiz.Quiz, quizcomp.model.group.Group]) -> str:
        """ Create a question separator. """

        context = {
            'quiz': quiz,
            'answer_key': self.answer_key,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_QUESTION_SEPARATOR)
        text = template.render(**context)

        return text

    def create_answers_tf(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.List[typing.Dict[str, typing.Any]]:
        """ Create the template data for a TF question answers. """

        return question.answers  # type: ignore[no-any-return]

    def create_answers_matching(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.Dict[str, typing.Any]:
        """ Create the template data for a matching question answers. """

        lefts: typing.List[typing.Dict[str, typing.Any]] = []
        rights: typing.List[typing.Dict[str, typing.Any]] = []

        # {left_index: right_index, ...}
        matches = {}

        for items in question.answers['matches']:
            matches[len(lefts)] = len(rights)

            lefts.append({
                'initial_text': items['left'].text,
                'raw_text': self._format_doc(items['left'], doc_format = quizcomp.constants.FORMAT_TEXT),
                'text': self._format_doc(items['left']),
            })

            rights.append({
                'initial_text': items['right'].text,
                'raw_text': self._format_doc(items['right'], doc_format = quizcomp.constants.FORMAT_TEXT),
                'text': self._format_doc(items['right']),
            })

        for right in question.answers['distractors']:
            rights.append({
                'initial_text': right.text,
                'raw_text': self._format_doc(right, doc_format = quizcomp.constants.FORMAT_TEXT),
                'text': self._format_doc(right),
            })

        left_ids = self.get_matching_left_ids()
        right_ids = self.get_matching_right_ids()

        if (len(lefts) > len(left_ids)):
            raise ValueError(f"Too many left-hand values for a matching question. Found: {len(lefts)}, Max {len(left_ids)}.")

        if (len(rights) > len(right_ids)):
            raise ValueError(f"Too many right-hand values for a matching question. Found: {len(rights)}, Max {len(right_ids)}.")

        if (question.answers.get('shuffle', False)):
            seed = question.answers.get('shuffle_seed', None)
            rng = random.Random(seed)

            # Shuffle the left and right options while maintining the match mapping.
            left_indexes = list(range(len(lefts)))
            right_indexes = list(range(len(rights)))

            rng.shuffle(left_indexes)
            rng.shuffle(right_indexes)

            new_lefts = [lefts[index] for index in left_indexes]
            lefts = new_lefts

            new_rights = [rights[index] for index in right_indexes]
            rights = new_rights

            new_matches = {
                left_indexes.index(old_left_index): right_indexes.index(old_right_index)
                for (old_left_index, old_right_index)
                in matches.items()
            }
            matches = new_matches

        # Augment the left and rights with more information for the template.
        for left_index in range(len(lefts)):  # pylint: disable=consider-using-enumerate
            right_index = matches[left_index]

            lefts[left_index] = {
                'id': self.id_delim.join([question_id, left_ids[left_index]]),
                'text': lefts[left_index]['text'],
                'initial_text': lefts[left_index]['initial_text'],
                'raw_text': lefts[left_index]['raw_text'],
                'solution': right_ids[right_index],
                'solution_id': self.id_delim.join([question_id, right_ids[right_index]]),
                'index': left_index,
                'solution_index': right_index,
                'one_index': left_index + 1,
                'solution_one_index': right_index + 1,
            }

        for right_index in range(len(rights)):  # pylint: disable=consider-using-enumerate
            rights[right_index] = {
                'id': self.id_delim.join([question_id, right_ids[right_index]]),
                'text': rights[right_index]['text'],
                'initial_text': rights[right_index]['initial_text'],
                'raw_text': rights[right_index]['raw_text'],
                'label': right_ids[right_index],
                'index': right_index,
                'one_index': right_index + 1,
            }

        return {
            'lefts': lefts,
            'rights': rights,
            'matches': matches,
        }

    def get_matching_left_ids(self) -> typing.List[str]:
        """ Get the IDs to use on the left side of a matching question. """

        return LEFT_IDS

    def get_matching_right_ids(self) -> typing.List[str]:
        """ Get the IDs to use on the right side of a matching question. """

        return RIGHT_IDS

    def create_answers_mcq(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.List[typing.Dict[str, typing.Any]]:
        """ Create the template data for an MCQ question answers. """

        return self._create_answers_mcq_list(question.answers)

    def _create_answers_mcq_list(self,
            # TEST
            # answers: typing.List[quizcomp.model.text.ParsedTextChoice],
            answers: typing.List[typing.Any],
            ) -> typing.List[typing.Dict[str, typing.Any]]:
        choices = []

        for (i, answer) in enumerate(answers):
            choice = self._create_answers_text_value(answer)
            choice['correct'] = answer.is_correct()
            choice['marker'] = string.ascii_uppercase[i]

            choices.append(choice)

        return choices

    def create_answers_text_only(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> None:
        """ Create the template data for a text only question answers. """

        return None

    def create_answers_numerical(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.Dict[str, typing.Any]:
        """ Create the template data for a numerical question answers. """

        answer = question.answers[0]

        if (answer.type == quizcomp.constants.NUMERICAL_ANSWER_TYPE_EXACT):
            if (math.isclose(answer.margin, 0.0)):
                content = str(answer.value)
            else:
                content = f"{answer.value} ± {answer.margin}"
        elif (answer.type == quizcomp.constants.NUMERICAL_ANSWER_TYPE_RANGE):
            content = f"[{answer.min}, {answer.max}]"
        elif (answer.type == quizcomp.constants.NUMERICAL_ANSWER_TYPE_PRECISION):
            content = f"{answer.value} (precision: {answer.precision})"
        else:
            raise ValueError(f"Unknown numerical answer type: '{answer.type}'.")

        document = quizcomp.parser.document.ParsedDocument.parse_text(content)

        return {
            'solution': self.clean_solution_content(document),
            'dirty_solution': self._format_doc(document),
            'raw_solution': self._format_doc(document, doc_format = quizcomp.constants.FORMAT_TEXT),
            'raw_answers': question.answers,
        }

    def create_answers_mdd(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.List[typing.Dict[str, typing.Any]]:
        """ Create the template data for a TF question answers. """

        answers = []

        for items in question.answers.values():
            answers.append({
                'label': self._format_doc(items['key']),
                'initial_label': items['key'].text,
                'raw_label': self._format_doc(items['key'], doc_format = quizcomp.constants.FORMAT_TEXT),
                'choices': self._create_answers_mcq_list(items['values']),
            })

        return answers

    def create_answers_ma(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.List[typing.Dict[str, typing.Any]]:
        """ Create the template data for a TF question answers. """

        return self._create_answers_mcq_list(question.answers)

    def create_answers_fimb(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.Dict[str, typing.Any]:
        """ Create the template data for a TF question answers. """

        answers = {}

        for (key, item) in question.answers.items():
            solutions = []
            for value in item['values']:
                solutions.append(self._create_answers_text_value(value))

            answers[key] = {
                'label': self._format_doc(item['key']),
                'raw_label': self._format_doc(item['key'], doc_format = quizcomp.constants.FORMAT_TEXT),
                'initial_label': item['key'].text,
                'solutions': solutions,
            }

        return answers

    def create_answers_fitb(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.Dict[str, typing.Any]:
        """ Create the template data for a TF question answers. """

        return self.create_answers_fimb(question_id, question_number, question, variant)['']['solutions']  # type: ignore[no-any-return]

    def create_answers_sa(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.List[typing.Dict[str, typing.Any]]:
        """ Create the template data for a TF question answers. """

        return self._create_answers_text(question_id, question_number, question, variant)

    def create_answers_essay(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.List[typing.Dict[str, typing.Any]]:
        """ Create the template data for a TF question answers. """

        return self._create_answers_text(question_id, question_number, question, variant)

    def _create_answers_text(self,
            question_id: str,
            question_number: int,
            question: quizcomp.model.question.Question,
            variant: quizcomp.model.quiz.Variant,
            ) -> typing.List[typing.Dict[str, typing.Any]]:
        """ Create the template data for a TF question answers. """

        solutions = []
        for value in question.answers:
            solutions.append(self._create_answers_text_value(value))

        return solutions

    # TEST
    # def _create_answers_text_value(self, value: quizcomp.model.text.ParsedTextChoice) -> typing.Dict[str, typing.Any]:
    def _create_answers_text_value(self, value: typing.Any) -> typing.Dict[str, typing.Any]:
        """
        Create an output dict for a value that was parsed from text (the result of a parsed string).
        """

        result = {
            'text': self._format_doc(value),
            'raw_text': self._format_doc(value, doc_format = quizcomp.constants.FORMAT_TEXT),
            'initial_text': value.text,
            'clean': self.clean_solution_content(value),
        }

        if (value.feedback is not None):
            result.update({
                'feedback': self._format_doc(value.feedback),
                'raw_feedback': self._format_doc(value.feedback, doc_format = quizcomp.constants.FORMAT_TEXT),
                'initial_feedback': value.feedback.text,
            })

        return result

    def _format_doc(self,
            doc: quizcomp.parser.document.ParsedDocument,
            doc_format: typing.Union[str, None] = None,
            format_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            ) -> str:
        """ Format a parsed document. """

        if (doc_format is None):
            doc_format = self.format

        if (format_options is None):
            format_options = self.parser_format_options

        return doc.to_format(doc_format, **format_options)

    def _store_images(self, link: str, base_dir: str) -> str:
        """ Store images for this quiz. """

        if (self.image_base_dir is None):
            self.image_base_dir = edq.util.dirent.get_temp_path(prefix = 'quizcomp-images-', rm = self.cleanup_images)

        os.makedirs(self.image_base_dir, exist_ok = True)

        if (re.match(r'^http(s)?://', link)):
            image_path = edq.util.dirent.get_temp_path(prefix = 'quizcomp-image-dl-')
            image_id = link

            response, _ = edq.net.request.make_get(link)
            edq.util.dirent.write_file_bytes(image_path, response.content)
        else:
            image_path = os.path.join(base_dir, link)
            image_id = image_path

        ext = os.path.splitext(image_path)[-1]
        filename = f"{len(self.image_paths):03d}{ext}"
        out_path = os.path.join(self.image_base_dir, filename)

        edq.util.dirent.copy(image_path, out_path)

        if (self.image_relative_root is not None):
            out_path = os.path.join(self.image_relative_root, filename)

        self.image_paths[image_id] = out_path

        return out_path

    '''
