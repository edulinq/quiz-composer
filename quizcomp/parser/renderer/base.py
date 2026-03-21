import typing

import markdown_it.renderer
import markdown_it.token
import markdown_it.utils

import quizcomp.parser.ast
import quizcomp.parser.common
import quizcomp.parser.style

class QuizComposerRendererBase(markdown_it.renderer.RendererProtocol):
    """ The base class for renderers (objects that take tokens and output strings in a specific format. """

    def render(self,
            tokens: typing.Sequence[markdown_it.token.Token],
            options: markdown_it.utils.OptionsDict,
            env: typing.MutableMapping[str, typing.Any],
            ) -> str:
        """ Render tokens to text. """

        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})

        # Work with an AST instead of tokens.
        ast = quizcomp.parser.ast.build(tokens)

        return self._render_node(ast, context)

    def clean_final(self, text: str, context: typing.Dict[str, typing.Any]) -> str:
        """
        Last chance for cleaning before leaving the renderer.
        """

        return text.strip()

    def _render_node(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """
        Route rendering to the method '_render_<type>(self, node, context)', e.g.: '_image'.
        """

        method_name = '_' + node.type
        method = getattr(self, method_name, None)
        if (method is None):
            raise TypeError(f"Could not find TeX render method: '{method_name}'.")

        return str(method(node, context))

    def _root(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'root' token. """

        content = "\n\n".join([self._render_node(child, context) for child in node.children])
        content = self.clean_final(content, context)
        return content

    def _container_block(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'container_block' token. """

        # Pull any style attatched to this block and put it in a copy of the context.
        context, _, _ = quizcomp.parser.common.handle_block_style(node.attributes, context)
        return "\n\n".join([self._render_node(child, context) for child in node.children])

    def _paragraph(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'paragraph' token. """

        return "\n".join([self._render_node(child, context) for child in node.children])

    def _inline(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'inline' token. """

        return ''.join([self._render_node(child, context) for child in node.children])

    def _text(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'text' token. """

        raise NotImplementedError()

    def _softbreak(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'softbreak' token. """

        raise NotImplementedError()

    def _hardbreak(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'hardbreak' token. """

        raise NotImplementedError()

    def _em(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'em' token. """

        raise NotImplementedError()

    def _strong(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'strong' token. """

        raise NotImplementedError()

    def _fence(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'fence' token. """

        raise NotImplementedError()

    def _code_block(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """
        Render the 'code_block' token.

        This token is poorly named, it is actually an indented code block.
        Treat it like a fence with no info string.
        """

        raise NotImplementedError()

    def _code_inline(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'code_inline' token. """

        raise NotImplementedError()

    def _math_block(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'math_block' token. """

        raise NotImplementedError()

    def _math_inline(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'math_inline' token. """

        raise NotImplementedError()

    def _image(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'image' token. """

        raise NotImplementedError()

    def _link(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'link' token. """

        raise NotImplementedError()

    def _placeholder(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'placeholder' token. """

        raise NotImplementedError()

    def _table(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'table' token. """

        raise NotImplementedError()

    def _thead(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'thead' token. """

        raise NotImplementedError()

    def _tbody(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'tbody' token. """

        raise NotImplementedError()

    def _tr(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'tr' token. """

        raise NotImplementedError()

    def _th(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'th' token. """

        raise NotImplementedError()

    def _td(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'td' token. """

        raise NotImplementedError()

    def _bullet_list(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'bullet_list' token. """

        raise NotImplementedError()

    def _ordered_list(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'ordered_list' token. """

        raise NotImplementedError()

    def _list_item(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'list_item' token. """

        raise NotImplementedError()

    def _hr(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'hr' token. """

        raise NotImplementedError()

    def _heading(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'heading' token. """

        raise NotImplementedError()

    def _blockquote(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """ Render the 'blockquote' token. """

        raise NotImplementedError()

    def parse_heading_level(self, node: quizcomp.parser.ast.ASTNode) -> int:
        """ Parse the level out of the HTML tag. """

        tag = node.get('tag', None)
        if (tag is None):
            raise ValueError("Failed to find a heading's level.")

        try:
            level = int(tag[1])
        except Exception as ex:
            raise ValueError(f"Failed to parse heading level from '{tag}'.") from ex

        return level
