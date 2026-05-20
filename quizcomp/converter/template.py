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

# TEST
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

DEFAULT_JINJA_OPTIONS: typing.Dict[str, typing.Any] = {
    'trim_blocks': True,
    'lstrip_blocks': True,
    'autoescape': jinja2.select_autoescape(),
}

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
            image_base_dir: typing.Union[str, None] = None,
            image_relative_root: typing.Union[str, None] = None,
            cleanup_images: bool = True,
            **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

        if (not os.path.isdir(template_dir)):
            raise ValueError(f"Provided template dir ('{template_dir}') does not exist or is not a dir.")

        self.format: str = format
        """ The format being converted to. """

        self.template_dir: str = template_dir
        """ The directory containing the templates to use. """

        # TEST
        self.image_base_dir: typing.Union[str, None] = image_base_dir
        """
        The location images are to be stored.
        Some converters will need to store image paths.
        Using the _store_images() callback will put the images here.
        """

        # TEST
        self.image_paths: typing.Dict[str, str] = {}
        """ This will hold: {<abs_path or link>: <new path (based on image_base_dir)>, ...} """

        # TEST
        self.image_relative_root: typing.Union[str, None] = image_relative_root
        """ If not None, override the default image output path with os.join(image_relative_root, filename). """

        # TEST
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

    def convert_quiz(self, quiz: quizcomp.model.quiz.Quiz, **kwargs: typing.Any) -> str:
        """ Convert an entire quiz (including variants). """

        return self.finalize(self._convert_quiz(quiz))

    def convert_variant(self, variant: quizcomp.model.quiz.variant, **kwargs: typing.any) -> str:
        """ convert a a standard quiz variant. """

        return self.finalize(self._convert_quiz(variant))

    def finalize(self, text: str) -> str:
        """ A final chance for children to modify the output. """

        return text

    def _convert_quiz(self, quiz: quizcomp.model.quiz.Quiz) -> str:
        """ Convert a quiz (or variant). """

        quiz_id = '0'
        quiz_number = 1

        children_content, _ = self._convert_children(quiz, quiz, quiz_id, self._convert_group, self._convert_group_separator, 1)

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
            running_question_number: int,
            ) -> typing.Tuple[str, int]:
        """ Convert a list of children. """

        last_child = None
        last_child_id = None
        last_child_index = None

        children_content = []
        for (child_index, child) in enumerate(parent.children):
            child_id = f"{parent_id}.{child_index}"

            # Add in a separator if we are between two children.
            if (last_child is not None):
                children_content.append(convert_child_separator_func(quiz, parent, last_child, last_child_id, last_child_index, child, child_id, child_index))

            child_content, running_question_number = convert_child_func(quiz, child, child_id, child_index, running_question_number)
            children_content.append(child_content)

            last_child = child
            last_child_id = child_id
            last_child_index = child_index

            # TEST
            if (child_index >= 12):
                break

        return "\n".join(children_content), running_question_number

    def _convert_group(self,
            quiz: quizcomp.model.quiz.Quiz,
            group: quizcomp.model.group.Group, group_id: str, child_index: typing.Union[int, None],
            running_question_number: int,
            ) -> typing.Tuple[str, int]:
        """ Convert a group. """

        children_content, running_question_number = self._convert_children(quiz, group, group_id, self._convert_question, self._convert_question_separator, running_question_number)

        context = {
            'this': group,
            'quiz': quiz,
            'answer_key': self.answer_key,
            'id': group_id,
            'child_index': child_index,
            'children_content': children_content,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_GROUP)
        return template.render(**context), running_question_number

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
            question: quizcomp.model.question.Question, question_id: str, child_index: typing.Union[int, None],
            running_question_number: int,
            ) -> typing.Tuple[str, int]:
        """ Convert a question. """

        question_number = None
        if (question.get_config(quizcomp.model.config.OPTION_SKIP_NUMBERING_KEY) is not True):
            question_number = running_question_number
            running_question_number += 1

        context = {
            'this': question,
            'quiz': quiz,
            'answer_key': self.answer_key,
            'id': question_id,
            'child_index': child_index,
            'number': question_number,
            'children_content': None,
            'custom_header': question.get_config(quizcomp.model.config.OPTION_CUSTOM_HEADER),
        }

        template = self.env.get_template(f"questions/{question.question_type}.template")
        return template.render(**context), running_question_number

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
