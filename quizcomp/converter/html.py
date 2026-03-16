import os
import typing

import quizcomp.constants
import quizcomp.converter.template
import quizcomp.parser.document

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR: str = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-html')

class HTMLTemplateConverter(quizcomp.converter.template.TemplateConverter):
    """
    A converter to convert a quiz to HTML using templates.
    """

    def __init__(self,
            format: str = quizcomp.constants.FORMAT_HTML,
            template_dir: str = DEFAULT_TEMPLATE_DIR,
            **kwargs: typing.Any) -> None:
        super().__init__(format, template_dir, **kwargs)

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
