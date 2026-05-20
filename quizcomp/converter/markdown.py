import os
import typing

import quizcomp.constants
import quizcomp.converter.template

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR: str = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-md')

class MarkdownTemplateConverter(quizcomp.converter.template.TemplateConverter):
    """
    A converter to convert a quiz to Markdown using templates.
    """

    def __init__(self,
            template_dir: str = DEFAULT_TEMPLATE_DIR,
            **kwargs: typing.Any) -> None:
        super().__init__(quizcomp.constants.FORMAT_MD, template_dir, **kwargs)
