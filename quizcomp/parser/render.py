import re
import typing

import lxml.etree
import markdown_it.token
import markdown_it.token

import quizcomp.parser.parse
import quizcomp.parser.renderer.canvas
import quizcomp.parser.renderer.html
import quizcomp.parser.renderer.markdown
import quizcomp.parser.renderer.tex
import quizcomp.parser.renderer.text

def canvas(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        pretty: bool = False,
        **kwargs: typing.Any) -> str:
    """ Render tokens to Canvas-specific HTML. """

    if (env is None):
        env = {}

    _, options = quizcomp.parser.parse._get_parser()

    renderer = quizcomp.parser.renderer.canvas.get_renderer(options)
    raw_html = renderer.render(tokens, options, env)  # type: ignore[arg-type]

    return clean_html(raw_html, pretty = pretty)

def html(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        pretty: bool = False,
        **kwargs: typing.Any) -> str:
    """ Render tokens to HTML. """

    if (env is None):
        env = {}

    _, options = quizcomp.parser.parse._get_parser()

    renderer = quizcomp.parser.renderer.html.get_renderer(options)
    raw_html = renderer.render(tokens, options, env)  # type: ignore[arg-type]

    return clean_html(raw_html, pretty = pretty)

def md(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        **kwargs: typing.Any) -> str:
    """ Render tokens to Markdown. """

    if (env is None):
        env = {}

    _, options = quizcomp.parser.parse._get_parser()

    renderer = quizcomp.parser.renderer.markdown.get_renderer(options)
    content = renderer.render(tokens, options, env)  # type: ignore[arg-type]

    return content.strip()

def tex(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        **kwargs: typing.Any) -> str:
    """ Render tokens to TeX. """

    if (env is None):
        env = {}

    _, options = quizcomp.parser.parse._get_parser()

    renderer = quizcomp.parser.renderer.tex.get_renderer(options)
    content = renderer.render(tokens, options, env)  # type: ignore[arg-type]

    return content.strip()

def text(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        **kwargs: typing.Any) -> str:
    """ Render tokens to text. """

    if (env is None):
        env = {}

    _, options = quizcomp.parser.parse._get_parser()

    renderer = quizcomp.parser.renderer.text.get_renderer(options)
    content = renderer.render(tokens, options, env)  # type: ignore[arg-type]

    return content.strip()

def render(
        format: str,
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        **kwargs: typing.Any) -> str:
    """ Render tokens to the specified format. """

    if (env is None):
        env = {}

    render_function = globals().get(format, None)
    if (render_function is None):
        raise ValueError("Could not find render function: 'quizcomp.parser.render.%s'." % (format))

    return render_function(tokens, env = env, **kwargs)

def clean_html(raw_html: str, pretty: bool = False) -> str:
    """
    Clean up and standardize the HTML.
    If |pretty|, then the output will be indented properly, and extra space will be stripped (which may mess with some inline spacing).
    |pretty| should only be used when being read by a human for visual inspection.
    """

    raw_html = raw_html.strip()
    if (len(raw_html) == 0):
        return raw_html

    parser = lxml.etree.XMLParser(remove_blank_text = True)
    root = lxml.etree.fromstring(raw_html, parser)
    content = lxml.etree.tostring(root, pretty_print = pretty, encoding = 'unicode')

    return content.strip()
