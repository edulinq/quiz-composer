import html

import quizcomp.constants
import quizcomp.katex
import quizcomp.parser.common

_katex_available = None

def render(format, inline, tokens, idx, options, env):
    context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
    text = tokens[idx].content

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

def _render_tex(text, inline, context):
    text = text.replace('$', r'\$')

    if (inline):
        text = text.strip()
        return f"$ {text} $"

    return f"$$\n{text}\n$$"

def _render_html(text, inline, context):
    global _katex_available

    if (_katex_available is None):
        _katex_available = quizcomp.katex.is_available()

    if (inline):
        text = text.strip()

    if (_katex_available):
        content = quizcomp.katex.to_html(text)
    else:
        text = html.escape(text)
        content = f"<code>{text}</code>"

    element = 'span'
    attributes = 'class="qg-math"'
    if (not inline):
        element = 'p'

    return f"<{element} {attributes}>{content}</{element}>"

def _render_md(text, inline, context):
    if (inline):
        text = text.strip()
        return f"$ {text} $"

    return f"$$\n{text}\n$$"
