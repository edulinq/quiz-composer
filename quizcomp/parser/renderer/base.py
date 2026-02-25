import abc

import markdown_it.renderer

import quizcomp.parser.ast
import quizcomp.parser.common
import quizcomp.parser.style

class QuizComposerRendererBase(markdown_it.renderer.RendererProtocol, abc.ABC):
    def render(self, tokens, options, env):
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})

        # Work with an AST instead of tokens.
        ast = quizcomp.parser.ast.build(tokens)

        return self._render_node(ast, context)

    def clean_final(self, text, context):
        """
        Last chance for cleaning before leaving the renderer.
        """

        return text.strip()

    def _render_node(self, node, context):
        """
        Route rendering to a the method '_render_<type>(self, node, context)', e.g.: '_image'.
        """

        method_name = '_' + node.type()
        method = getattr(self, method_name, None)
        if (method is None):
            raise TypeError("Could not find TeX render method: '%s'." % (method_name))

        return method(node, context)

    def _root(self, node, context):
        content = "\n\n".join([self._render_node(child, context) for child in node.children()])
        content = self.clean_final(content, context)
        return content

    def _container_block(self, node, context):
        # Pull any style attatched to this block and put it in a copy of the context.
        context, _, _ = quizcomp.parser.common.handle_block_style(node, context)
        return "\n\n".join([self._render_node(child, context) for child in node.children()])

    def _paragraph(self, node, context):
        return "\n".join([self._render_node(child, context) for child in node.children()])

    def _inline(self, node, context):
        return ''.join([self._render_node(child, context) for child in node.children()])

    @abc.abstractmethod
    def _text(self, node, context):
        pass

    @abc.abstractmethod
    def _softbreak(self, node, context):
        pass

    @abc.abstractmethod
    def _hardbreak(self, node, context):
        pass

    @abc.abstractmethod
    def _em(self, node, context):
        pass

    @abc.abstractmethod
    def _strong(self, node, context):
        pass

    @abc.abstractmethod
    def _fence(self, node, context):
        pass

    @abc.abstractmethod
    def _code_block(self, node, context):
        """
        This token is poorly named, it is actually an indented code block.
        Treat it like a fence with no info string.
        """

        pass

    @abc.abstractmethod
    def _code_inline(self, node, context):
        pass

    @abc.abstractmethod
    def _math_block(self, node, context):
        pass

    @abc.abstractmethod
    def _math_inline(self, node, context):
        pass

    @abc.abstractmethod
    def _image(self, node, context):
        pass

    @abc.abstractmethod
    def _link(self, node, context):
        pass

    @abc.abstractmethod
    def _placeholder(self, node, context):
        pass

    @abc.abstractmethod
    def _table(self, node, context):
        pass

    @abc.abstractmethod
    def _thead(self, node, context):
        pass

    @abc.abstractmethod
    def _tbody(self, node, context):
        pass

    @abc.abstractmethod
    def _tr(self, node, context):
        pass

    @abc.abstractmethod
    def _th(self, node, context):
        pass

    @abc.abstractmethod
    def _td(self, node, context):
        pass

    @abc.abstractmethod
    def _bullet_list(self, node, context):
        pass

    @abc.abstractmethod
    def _ordered_list(self, node, context):
        pass

    @abc.abstractmethod
    def _list_item(self, node, context):
        pass

    @abc.abstractmethod
    def _hr(self, node, context):
        pass

    @abc.abstractmethod
    def _heading(self, node, context):
        pass

    @abc.abstractmethod
    def _blockquote(self, node, context):
        pass

    def parse_heading_level(self, node):
        # Parse the level out of the HTML tag.
        tag = node.get('tag', None)
        if (tag is None):
            raise ValueError("Failed to find a heading's level.")

        try:
            level = int(tag[1])
        except Exception as ex:
            raise ValueError("Failed to parse heading level from '%s'." % (tag)) from ex

        return level

def get_renderer(options):
    return QuizComposerRendererTex(), options
