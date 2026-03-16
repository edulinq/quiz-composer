import os
import typing

import quizcomp.constants
import quizcomp.converter.template
import quizcomp.parser.document

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
            cleanup_images: bool = False,
            **kwargs: typing.Any) -> None:
        super().__init__(
            quizcomp.constants.FORMAT_TEX,
            template_dir,
            cleanup_images = cleanup_images,
            parser_format_options = {
                'image_path_callback': self._store_images,
            },
            jinja_options = JINJA_OPTIONS,
            **kwargs,
        )

    def clean_solution_content(self, document: quizcomp.parser.document.ParsedDocument) -> str:
        tex = document.to_format(quizcomp.constants.FORMAT_TEX)
        if ('\\' not in tex):
            return tex

        content = document.to_format(quizcomp.constants.FORMAT_TEXT)
        content = content.replace('\\', '\\textbackslash{}')

        return content
