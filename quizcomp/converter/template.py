"""
The most common way to render Quiz Composer quizzes is via templates.
We use the [Jinja](https://jinja.palletsprojects.com) template system.

This comment describes the general information passed in the Jinja context for each object.
See the source code for full information.

The standard rendering context sent to most templates will always include:
 - `this: typing.Any` -- The context object being rendered (e.g., a quiz, group, or question).
 - `quiz: quizcomp.model.quiz.Quiz` -- The current quiz (often a variant) being rendered.
 - `answer_key: bool` -- Whether this conversion if for an answer key.

Core types (quiz, group, question) will additionally include:
 - `id: str` -- An identifier specific to this.
 - `children_content: str` -- The rendered content from this' children (if any).

 Questions will also have:
 - `custom_header: typing.Union[str, None]` -- An optional custom header to use for this question.
 - `number: int` -- The number that should be displayed for this object (if any), e.g., a question's number.
"""

import logging
import os
import re
import typing
import urllib.parse

import edq.net.request
import edq.util.dirent
import jinja2

import quizcomp.converter.converter
import quizcomp.errors
import quizcomp.model.base
import quizcomp.model.config
import quizcomp.model.group
import quizcomp.model.question
import quizcomp.model.quiz
import quizcomp.parser.document

_logger = logging.getLogger(__name__)

TEMPLATE_FILENAME_QUIZ: str = 'quiz.template'
TEMPLATE_FILENAME_QUESTION_SEPARATOR: str = 'question-separator.template'
TEMPLATE_FILENAME_GROUP: str = 'group.template'
TEMPLATE_FILENAME_GROUP_SEPARATOR: str = 'group-separator.template'

DEFAULT_JINJA_OPTIONS: typing.Dict[str, typing.Any] = {
    'trim_blocks': True,
    'lstrip_blocks': True,
    'autoescape': jinja2.select_autoescape(),
}

MAX_IMAGE_RENAMES: int = 1000

class TemplateConverter(quizcomp.converter.converter.Converter):
    """
    The base class for a converter that uses templates.
    """

    def __init__(self,
            format: str,
            template_dir: str,
            jinja_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            jinja_filters: typing.Union[typing.Dict[str, typing.Any], None] = None,
            jinja_globals: typing.Union[typing.Dict[str, typing.Any], None] = None,
            image_base_dir: typing.Union[str, None] = None,
            **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

        if (not os.path.isdir(template_dir)):
            raise ValueError(f"Provided template dir ('{template_dir}') does not exist or is not a dir.")

        self.format: str = format
        """ The format being converted to. """

        self.template_dir: str = template_dir
        """ The directory containing the templates to use. """

        self.image_base_dir: typing.Union[str, None] = image_base_dir
        """
        The location images are to be stored.
        Some converters will need to store image paths.

        If set to None, then no images will be stored (even if their source strings get rewritten).
        """

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

        return self._convert_quiz(quiz)

    def convert_variant(self, variant: quizcomp.model.quiz.Variant, **kwargs: typing.Any) -> str:
        """ Convert a standard quiz variant. """

        return self._convert_quiz(variant)

    def prepare(self, quiz: quizcomp.model.quiz.Quiz) -> None:
        """ A first chance for children to prepare for converting the given quiz. """

    def finalize(self, quiz: quizcomp.model.quiz.Quiz, text: str) -> str:
        """ A final chance for children to modify the output. """

        return text

    def _convert_quiz(self, quiz: quizcomp.model.quiz.Quiz) -> str:
        """ Convert a quiz (or variant). """

        self.prepare(quiz)

        quiz_id = '0'
        quiz_number = 1

        children_content, _ = self._convert_children(quiz, quiz, quiz_id, self._convert_group, self._convert_group_separator, 1)

        context = {
            'this': quiz,
            'quiz': quiz,
            'answer_key': self.answer_key,
            'id': quiz_id,
            'children_content': children_content,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_QUIZ)
        output = template.render(**context)

        return self.finalize(quiz, output)

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

        raw_custom_header = question.get_config(quizcomp.model.config.OPTION_CUSTOM_HEADER)
        custom_header = None
        if (raw_custom_header is not None):
            custom_header = quizcomp.parser.document.ParsedDocument.parse_text(raw_custom_header)

        context = {
            'this': question,
            'quiz': quiz,
            'answer_key': self.answer_key,
            'id': question_id,
            'child_index': child_index,
            'number': question_number,
            'children_content': None,
            'custom_header': custom_header,
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

    def _store_images(self, quiz: quizcomp.model.quiz.Quiz) -> None:
        """
        Prepare images for conversions.
        Replace the source in image tokens.
        Write images to a common directory.
        """

        seen_sources: typing.Dict[str, str] = {}

        for document in quiz.collect_all_documents():
            image_tokens = document.collect_images()
            if (len(image_tokens) == 0):
                continue

            for image_token in image_tokens:
                original_source = image_token.attrGet('original_src')
                if (original_source is None):
                    original_source = image_token.attrGet('src')

                if ((original_source is None) or len(str(original_source)) == 0):
                    _logger.warning("Could not locate image source for '%s'.", image_token.content)

                original_source = str(original_source)

                if (original_source in seen_sources):
                    new_source = seen_sources[original_source]
                else:
                    new_source = self._handle_image(quiz, original_source, document.context.base_dir)
                    seen_sources[original_source] = new_source

                image_token.attrSet('original_src', original_source)
                image_token.attrSet('src', new_source)

    def _handle_image(self, quiz: quizcomp.model.quiz.Quiz, source: str, document_base_dir: str) -> str:
        """
        Handle an image that will be stored and return the new source for the image.

        By default, "handling" and image entails:
         - fetching an image (if it is not available locally),
         - copying it to the image directory (if an image directory exists),
         - and returning the new relative source path for the image.
        """

        is_http = re.match(r'^http(s)?://', source)
        if (is_http):
            url_path = urllib.parse.urlsplit(source).path
            filename = url_path.split('/')[-1]
        else:
            filename = os.path.basename(source)

        # If there is no image base dir to store images into, then just return with the newly formed source.
        if (self.image_base_dir is None):
            return self._form_image_source(filename, quiz)

        (basename, ext) = os.path.split(filename)
        path = os.path.join(self.image_base_dir, filename)

        count = 0
        while (os.path.exists(path)):
            filename = f"{basename}_{count:03d}{ext}"
            path = os.path.join(self.image_base_dir, filename)
            count += 1

            if (count >= MAX_IMAGE_RENAMES):
                raise quizcomp.errors.QuizValidationError(f"Cannot create unique filename for image: '{source}'.", context = quiz)

        new_source = self._form_image_source(filename, quiz)

        if (is_http):
            response, _ = edq.net.request.make_get(source)
            edq.util.dirent.write_file_bytes(path, response.content)
        else:
            if (not os.path.isabs(source)):
                source = os.path.join(document_base_dir, source)

            source = os.path.abspath(source)
            edq.util.dirent.copy(source, path)

        return new_source

    def _form_image_source(self, filename: str, quiz: quizcomp.model.quiz.Quiz) -> str:
        """ Create the image source string that will go inside stored image tokens using the base filename. """

        return os.path.join('images', filename)

    def _restore_image_sources(self, quiz: quizcomp.model.quiz.Quiz) -> None:
        """ Replace any modified image sources with their original source. """

        for document in quiz.collect_all_documents():
            image_tokens = document.collect_images()
            if (len(image_tokens) == 0):
                continue

            for image_token in image_tokens:
                original_source = image_token.attrGet('original_src')
                if (original_source is None):
                    continue

                image_token.attrSet('src', str(original_source))
                image_token.attrs.pop('original_src', None)
