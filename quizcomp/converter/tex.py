import os
import typing

import quizcomp.converter.template
import quizcomp.model.constants
import quizcomp.model.quiz

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR: str = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-tex')

JINJA_OPTIONS: typing.Dict[str, str] = {
    'block_start_string': '<%',
    'block_end_string': '%>',
    'variable_start_string': '<<',
    'variable_end_string': '>>',
    'comment_start_string': '<#',
    'comment_end_string': '#>',
}

class TexTemplateConverter(quizcomp.converter.template.TemplateConverter):
    """
    A converter to convert a quiz to TeX using templates.
    """

    def __init__(self,
            template_dir: str = DEFAULT_TEMPLATE_DIR,
            **kwargs: typing.Any) -> None:
        super().__init__(
            quizcomp.model.constants.Format.TEX,
            template_dir,
            jinja_options = JINJA_OPTIONS,
            **kwargs,
        )

    def prepare(self, quiz: quizcomp.model.quiz.Quiz) -> None:
        self._store_images(quiz)

    def finalize(self, quiz: quizcomp.model.quiz.Quiz, text: str) -> str:
        self._restore_image_sources(quiz)

        return text
