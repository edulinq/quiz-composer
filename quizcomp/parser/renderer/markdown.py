import mdformat.plugins
import mdformat.renderer

import quizcomp.parser.common
import quizcomp.parser.math

def math_inline(node, context):
    qg_context = context.env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
    return quizcomp.parser.math._render_md(node.content, True, qg_context)

def math_block(node, context):
    qg_context = context.env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
    return quizcomp.parser.math._render_md(node.content, False, qg_context)

def placeholder(node, context):
    return "<placeholder>%s</placeholder>" % (node.content)

def container_block(node, context):
    # We can ignore blocks when outputting markdown (since it is non-standard).
    # Just render the child node (there should only be one).
    if ((node.children is None) or (len(node.children) == 0)):
        return ''

    parts = []
    for child in node.children:
        parts.append(child.render(context))

    return "\n\n".join(parts)

class QuizComposerMDformatExtension(mdformat.plugins.ParserExtensionInterface):
    CHANGES_AST = False
    POSTPROCESSORS = {}
    RENDERERS = {
        'container_block': container_block,
        'math_block': math_block,
        'math_inline': math_inline,
        'placeholder': placeholder,
    }

def get_renderer(options):
    extensions = options.get('parser_extension', [])
    extensions += [
        mdformat.plugins.PARSER_EXTENSIONS['tables'],
        QuizComposerMDformatExtension(),
    ]
    options['parser_extension'] = extensions

    return mdformat.renderer.MDRenderer(), options
