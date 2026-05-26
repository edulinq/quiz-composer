import html
import typing

import markdown_it
import markdown_it.token

import quizcomp.constants
import quizcomp.external.katex
import quizcomp.parser.common

_katex_available: typing.Union[bool, None] = None  # pylint: disable=invalid-name

def render(
        format: str,
        inline: bool,
        tokens: typing.List[markdown_it.token.Token],
        token_index: int,
        options: markdown_it.utils.OptionsDict,
        env: typing.Dict[str, typing.Any],
        ) -> str:
    """ Render the given token in the specified format. """

    context = typing.cast(quizcomp.parser.common.RenderContext, env[quizcomp.parser.common.ENV_KEY_CONTEXT])

    text = tokens[token_index].content

    if (format == quizcomp.constants.FORMAT_HTML):
        return _render_html(text, inline, context)
    elif (format == quizcomp.constants.FORMAT_MD):
        return _render_md(text, inline, context)
    elif (format == quizcomp.constants.FORMAT_TEX):
        return _render_tex(text, inline, context)
    elif (format == quizcomp.constants.FORMAT_TEXT):
        return _render_md(text, inline, context)
    else:
        raise ValueError(f"Unknown format '{format}'.")

def _render_tex(text: str, inline: bool, context: quizcomp.parser.common.RenderContext) -> str:
    """ Render the given token content as TeX. """

    text = text.replace('$', r'\$')

    if (inline):
        text = text.strip()
        return f"$ {text} $"

    return f"$$\n{text}\n$$"

def _render_html(text: str, inline: bool, context: quizcomp.parser.common.RenderContext) -> str:
    """ Render the given token content as HTML. """

    global _katex_available  # pylint: disable=global-statement

    if (_katex_available is None):
        _katex_available = quizcomp.external.katex.is_available()

    if (inline):
        text = text.strip()

    if (_katex_available):
        content = quizcomp.external.katex.to_html(text)
    else:
        text = html.escape(text)
        content = f"<code>{text}</code>"

    element = 'span'
    attributes = 'class="qg-math"'
    if (not inline):
        element = 'p'

    return f"<{element} {attributes}>{content}</{element}>"

def _render_md(text: str, inline: bool, context: quizcomp.parser.common.RenderContext) -> str:
    """ Render the given token content as Markdown. """

    if (inline):
        text = text.strip()
        return f"$ {text} $"

    return f"$$\n{text}\n$$"
