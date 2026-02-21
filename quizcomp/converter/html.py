"""
Convert a quiz into HTML using templates.
"""

import os

import quizcomp.constants
import quizcomp.converter.template

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-html')

CSS_FILENAME = 'quiz.css'

DEFAULT_HTML_STYLE_CONFIG = {
    # Embed the CSS inline as a <style> block (produces a self-contained HTML file).
    # Set to False to use a <link> tag pointing to the CSS file instead.
    'inline_css': True,

    # Include the built-in quiz.css stylesheet.
    # Set to False to opt out entirely (useful if you supply your own styles).
    'include_default_css': True,

    # Optional additional CSS string appended after the default styles.
    'extra_css': '',
}

class HTMLTemplateConverter(quizcomp.converter.template.TemplateConverter):
    def __init__(self,
            format = quizcomp.constants.FORMAT_HTML, template_dir = DEFAULT_TEMPLATE_DIR,
            style_config = None,
            **kwargs):
        super().__init__(format, template_dir, **kwargs)

        # Merge caller-supplied config over the defaults.
        resolved_config = DEFAULT_HTML_STYLE_CONFIG.copy()
        if style_config is not None:
            resolved_config.update(style_config)

        # Read the default CSS so the template can embed it inline.
        css_path = os.path.join(template_dir, CSS_FILENAME)
        default_css = ''
        if os.path.isfile(css_path):
            with open(css_path, 'r', encoding='utf-8') as fh:
                default_css = fh.read()

        resolved_config['_default_css'] = default_css
        resolved_config['_css_path'] = CSS_FILENAME

        # Expose to every template via Jinja globals.
        self.env.globals['style_config'] = resolved_config

    def clean_solution_content(self, document):
        return document.to_text()

class CanvasTemplateConverter(HTMLTemplateConverter):
    def __init__(self,
            template_dir = DEFAULT_TEMPLATE_DIR,
            **kwargs):
        super().__init__(quizcomp.constants.FORMAT_CANVAS, template_dir, **kwargs)
