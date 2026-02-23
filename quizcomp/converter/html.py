"""
Convert a quiz into HTML using templates.
"""

import os

import quizcomp.constants
import quizcomp.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-html')

CSS_FILENAME = 'quiz.css'

class HTMLTemplateConverter(quizcomp.converter.template.TemplateConverter):
    def __init__(self,
            format = quizcomp.constants.FORMAT_HTML, template_dir = DEFAULT_TEMPLATE_DIR,
            **kwargs):
        super().__init__(format, template_dir, **kwargs)

        css_path = os.path.join(template_dir, CSS_FILENAME)
        if (not os.path.isfile(css_path)):
            raise ValueError("Could not find CSS file: '%s'" % (css_path))

        with open(css_path, 'r', encoding = 'utf-8') as css_file:
            self.env.globals['css_content'] = css_file.read()

    def clean_solution_content(self, document):
        return document.to_text()

class CanvasTemplateConverter(HTMLTemplateConverter):
    def __init__(self,
            template_dir = DEFAULT_TEMPLATE_DIR,
            **kwargs):
        super().__init__(quizcomp.constants.FORMAT_CANVAS, template_dir, **kwargs)
