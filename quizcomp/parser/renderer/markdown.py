import argparse
import typing

import markdown_it
import mdformat.plugins
import mdformat.renderer

import quizcomp.parser.common
import quizcomp.parser.math

def math_inline(node: mdformat.renderer.RenderTreeNode, context: mdformat.renderer.RenderContext) -> str:
    """ Render inline math. """

    qg_context = context.env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
    return quizcomp.parser.math._render_md(node.content, True, qg_context)

def math_block(node: mdformat.renderer.RenderTreeNode, context: mdformat.renderer.RenderContext) -> str:
    """ Render a math block. """

    qg_context = context.env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
    return quizcomp.parser.math._render_md(node.content, False, qg_context)

def placeholder(node: mdformat.renderer.RenderTreeNode, context: mdformat.renderer.RenderContext) -> str:
    """ Render an answer placeholder. """

    return "<placeholder>%s</placeholder>" % (node.content)

def container_block(node: mdformat.renderer.RenderTreeNode, context: mdformat.renderer.RenderContext) -> str:
    """ Render a container block. """

    # We can ignore blocks when outputting markdown (since it is non-standard).
    # Just render the child node (there should only be one).
    if ((node.children is None) or (len(node.children) == 0)):
        return ''

    parts = []
    for child in node.children:
        parts.append(child.render(context))

    return "\n\n".join(parts)

class QuizComposerMDformatExtension(mdformat.plugins.ParserExtensionInterface):
    """ A plugin for out Markdown extensions. """

    CHANGES_AST = False
    POSTPROCESSORS = {}
    RENDERERS = {
        'container_block': container_block,
        'math_block': math_block,
        'math_inline': math_inline,
        'placeholder': placeholder,
    }

    @staticmethod
    def add_cli_options(parser: argparse.ArgumentParser) -> None:
        return

    @staticmethod
    def add_cli_argument_group(group: argparse._ArgumentGroup) -> None:
        return

    @staticmethod
    def update_mdit(mdit: markdown_it.MarkdownIt) -> None:
        return

def get_renderer(options: typing.Dict[str, typing.Any]) -> typing.Tuple[mdformat.renderer.MDRenderer, typing.Dict[str, typing.Any]]:
    """ Get this renderer and options. """

    extensions = options.get('parser_extension', [])
    extensions += [
        mdformat.plugins.PARSER_EXTENSIONS['tables'],
        QuizComposerMDformatExtension(),
    ]
    options['parser_extension'] = extensions

    return mdformat.renderer.MDRenderer(), options
