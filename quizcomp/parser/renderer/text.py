import re

import quizcomp.parser.common
import quizcomp.parser.renderer.base

DISALLOWED_CHARACTERS = re.compile(r'[^\w \-]')

class QuizComposerRendererText(quizcomp.parser.renderer.base.QuizComposerRendererBase):
    """
    The text renderer tries to output plan text that will then be used for special purposes like keys and identifiers.
    The output here is not meant to represent full documents or be sent to users.
    """

    def clean_final(self, text, context):
        allow_all_characters = context.get(quizcomp.parser.common.CONTEXT_KEY_TEXT_ALLOW_ALL_CHARACTERS, False)

        # Clean up whitespace.
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove bad disallowed characters.
        if (not allow_all_characters):
            text = re.sub(DISALLOWED_CHARACTERS, '', text)

            # Clean up whitespace once more.
            text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _text(self, node, context):
        return _clean_text(node.text())

    def _softbreak(self, node, context):
        return "\n"

    def _hardbreak(self, node, context):
        return "\n\n"

    def _em(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _strong(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _fence(self, node, context):
        return self._handle_special_text(node, context)

    def _code_block(self, node, context):
        return self._handle_special_text(node, context)

    def _code_inline(self, node, context):
        return self._handle_special_text(node, context)

    def _math_block(self, node, context):
        return self._handle_special_text(node, context)

    def _math_inline(self, node, context):
        return self._handle_special_text(node, context)

    def _image(self, node, context):
        return ''

    def _link(self, node, context):
        return ''

    def _placeholder(self, node, context):
        return _clean_text(node.text())

    def _table(self, node, context):
        return ''

    def _thead(self, node, context):
        return ''

    def _tbody(self, node, context):
        return ''

    def _tr(self, node, context):
        return ''

    def _th(self, node, context):
        return ''

    def _td(self, node, context):
        return ''

    def _bullet_list(self, node, context):
        return ''

    def _ordered_list(self, node, context):
        return ''

    def _list_item(self, node, context):
        return ''

    def _hr(self, node, context):
        return ''

    def _heading(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _blockquote(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _handle_special_text(self, node, context):
        """
        Special text is usually not allowed,
        but can be enabled with quizcomp.parser.common.CONTEXT_KEY_TEXT_ALLOW_SPECIAL_TEXT.
        """

        if (context.get(quizcomp.parser.common.CONTEXT_KEY_TEXT_ALLOW_SPECIAL_TEXT, False)):
            return node.text().strip()

        return ''

def get_renderer(options):
    return QuizComposerRendererText(), options

def _clean_text(text):
    return text
