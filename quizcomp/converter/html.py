"""
Convert a quiz into HTML using templates.
"""

import logging
import os

import quizcomp.constants
import quizcomp.converter.template
import quizcomp.util.dirent

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-html')

CSS_FILENAME = 'quiz.css'

logger = logging.getLogger(__name__)

class HTMLTemplateConverter(quizcomp.converter.template.TemplateConverter):
    def __init__(self,
            format = quizcomp.constants.FORMAT_HTML, template_dir = DEFAULT_TEMPLATE_DIR,
            **kwargs):
        super().__init__(format, template_dir, **kwargs)

        css_path = os.path.join(template_dir, CSS_FILENAME)
        if (not os.path.isfile(css_path)):
            logger.warning("Could not find CSS file: '%s'. Continuing without external CSS.", css_path)
            self.env.globals['css_content'] = ''
        else:
            self.env.globals['css_content'] = quizcomp.util.dirent.read_file(css_path)

    def clean_solution_content(self, document):
        return document.to_text()

class CanvasTemplateConverter(HTMLTemplateConverter):
    def __init__(self,
            template_dir = DEFAULT_TEMPLATE_DIR,
            **kwargs):
        super().__init__(quizcomp.constants.FORMAT_CANVAS, template_dir, **kwargs)
