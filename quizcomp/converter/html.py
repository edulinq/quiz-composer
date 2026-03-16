import logging
import os
import typing

import edq.util.dirent

import quizcomp.constants
import quizcomp.converter.template
import quizcomp.parser.document

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR: str = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-html')

CSS_FILENAME: str = 'quiz.css'

_logger = logging.getLogger(__name__)

class HTMLTemplateConverter(quizcomp.converter.template.TemplateConverter):
    """
    A converter to convert a quiz to HTML using templates.
    """

    def __init__(self,
            format: str = quizcomp.constants.FORMAT_HTML,
            template_dir: str = DEFAULT_TEMPLATE_DIR,
            **kwargs: typing.Any) -> None:
        super().__init__(format, template_dir, **kwargs)

        css_path = os.path.join(template_dir, CSS_FILENAME)
        if (not os.path.isfile(css_path)):
            _logger.warning("Could not find CSS file: '%s'. Continuing without external CSS.", css_path)
            self.env.globals['css_content'] = ''
        else:
            self.env.globals['css_content'] = edq.util.dirent.read_file(css_path)

    def clean_solution_content(self, document: quizcomp.parser.document.ParsedDocument) -> str:
        return document.to_text()

class CanvasTemplateConverter(HTMLTemplateConverter):
    """
    A converter to convert a quiz to Canvas-specific HTML using templates.
    """

    def __init__(self,
            template_dir: str = DEFAULT_TEMPLATE_DIR,
            **kwargs: typing.Any) -> None:
        super().__init__(quizcomp.constants.FORMAT_CANVAS, template_dir, **kwargs)
