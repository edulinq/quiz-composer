"""
Convert a quiz into TeX using templates.
"""

import os

import quizcomp.constants
import quizcomp.converter.template
import quizcomp.parser.renderer.tex

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-tex')

JINJA_OPTIONS = {
    'block_start_string': '<%',
    'block_end_string': '%>',
    'variable_start_string': '<<',
    'variable_end_string': '>>',
    'comment_start_string': '<#',
    'comment_end_string': '#>',
}

class TexTemplateConverter(quizcomp.converter.template.TemplateConverter):
    def __init__(self, template_dir = DEFAULT_TEMPLATE_DIR,
            cleanup_images = False,
            **kwargs):
        super().__init__(quizcomp.constants.FORMAT_TEX, template_dir,
                cleanup_images = cleanup_images,
                parser_format_options = {
                    'image_path_callback': self._store_images,
                },
                jinja_options = JINJA_OPTIONS, **kwargs)

    def _format_label(self, label):
        return quizcomp.parser.renderer.tex.tex_escape(label.text)

    def clean_solution_content(self, document):
        tex = document.to_format(quizcomp.constants.FORMAT_TEX)
        if ('\\' not in tex):
            return tex

        content = document.to_format(quizcomp.constants.FORMAT_TEXT)
        content = content.replace('\\', '\\textbackslash{}')

        return content
