import re
import typing

import markdown_it

import quizcomp.constants
import quizcomp.parser.ast
import quizcomp.parser.common
import quizcomp.parser.renderer.base

DISALLOWED_CHARACTERS: re.Pattern = re.compile(r'[^\w \-]')

class QuizComposerRendererText(quizcomp.parser.renderer.base.QuizComposerRendererBase):
    """
    The text renderer tries to output plan text that will then be used for special purposes like keys and identifiers.
    The output here is not meant to represent full documents or be sent to users.
    """

    __output__ = quizcomp.constants.FORMAT_TEXT

    def clean_final(self, text: str, context: typing.Dict[str, typing.Any]) -> str:
        allow_all_characters = context.get(quizcomp.parser.common.CONTEXT_KEY_TEXT_ALLOW_ALL_CHARACTERS, False)

        # Clean up whitespace.
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove bad disallowed characters.
        if (not allow_all_characters):
            text = re.sub(DISALLOWED_CHARACTERS, '', text)

            # Clean up whitespace once more.
            text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _text(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return _clean_text(node.text())

    def _softbreak(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return "\n"

    def _hardbreak(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return "\n\n"

    def _em(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _strong(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _fence(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return self._handle_special_text(node, context)

    def _code_block(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return self._handle_special_text(node, context)

    def _code_inline(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return self._handle_special_text(node, context)

    def _math_block(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return self._handle_special_text(node, context)

    def _math_inline(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return self._handle_special_text(node, context)

    def _image(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _link(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _placeholder(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return _clean_text(node.text())

    def _table(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _thead(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _tbody(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _tr(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _th(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _td(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _bullet_list(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _ordered_list(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _list_item(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _hr(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''

    def _heading(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _blockquote(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return ''.join([self._render_node(child, context) for child in node.children()])

    def _handle_special_text(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """
        Special text is usually not allowed,
        but can be enabled with quizcomp.parser.common.CONTEXT_KEY_TEXT_ALLOW_SPECIAL_TEXT.
        """

        if (context.get(quizcomp.parser.common.CONTEXT_KEY_TEXT_ALLOW_SPECIAL_TEXT, False)):
            return node.text().strip()

        return ''

def _clean_text(text: str) -> str:
    """ Internal text clean. """

    return text

def get_renderer(options: markdown_it.utils.OptionsDict) -> QuizComposerRendererText:
    """ Get this renderer and options. """

    return QuizComposerRendererText()
