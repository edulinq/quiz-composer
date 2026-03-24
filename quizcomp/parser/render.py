import re
import typing

import edq.util.json
import lxml.etree
import markdown_it
import markdown_it.token
import mdit_py_plugins.container
import mdit_py_plugins.dollarmath

import quizcomp.parser.renderer.canvas
import quizcomp.parser.renderer.html
import quizcomp.parser.renderer.markdown
import quizcomp.parser.renderer.tex
import quizcomp.parser.renderer.text

EXTRA_OPTIONS: typing.List[str] = [
    'table',
]

PLUGINS: typing.List[typing.Tuple[typing.Callable, typing.Dict[str, typing.Any]]] = [
    (mdit_py_plugins.dollarmath.dollarmath_plugin, {}),
    (mdit_py_plugins.container.container_plugin, {'name': 'block'}),
]

HTML_TOKENS: typing.Set[str] = {
    'html_block',
    'html_inline',
}

def canvas(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        pretty: bool = False,
        **kwargs: typing.Any) -> str:
    """ Render tokens to Canvas-specific HTML. """

    if (env is None):
        env = {}

    _, options = _get_parser()

    renderer = quizcomp.parser.renderer.canvas.get_renderer(options)
    raw_html = renderer.render(tokens, options, env)

    return clean_html(raw_html, pretty = pretty)

def html(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        pretty: bool = False,
        **kwargs: typing.Any) -> str:
    """ Render tokens to HTML. """

    if (env is None):
        env = {}

    _, options = _get_parser()

    renderer = quizcomp.parser.renderer.html.get_renderer(options)
    raw_html = renderer.render(tokens, options, env)

    return clean_html(raw_html, pretty = pretty)

def md(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        **kwargs: typing.Any) -> str:
    """ Render tokens to Markdown. """

    if (env is None):
        env = {}

    _, options = _get_parser()

    renderer = quizcomp.parser.renderer.markdown.get_renderer(options)
    content = renderer.render(tokens, options, env)

    return content.strip()

def tex(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        **kwargs: typing.Any) -> str:
    """ Render tokens to TeX. """

    if (env is None):
        env = {}

    _, options = _get_parser()

    renderer = quizcomp.parser.renderer.tex.get_renderer(options)
    content = renderer.render(tokens, options, env)

    return content.strip()

def text(
        tokens: typing.List[markdown_it.token.Token],
        env: typing.Union[typing.Dict[str, typing.Any], None] = None,
        **kwargs: typing.Any) -> str:
    """ Render tokens to text. """

    if (env is None):
        env = {}

    _, options = _get_parser()

    renderer = quizcomp.parser.renderer.text.get_renderer(options)
    content = renderer.render(tokens, options, env)

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
        raise ValueError(f"Could not find render function: 'quizcomp.parser.render.{format}'.")

    return str(render_function(tokens, env = env, **kwargs))

# pylint: disable=c-extension-no-member
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

def _get_parser() -> typing.Tuple[markdown_it.MarkdownIt, markdown_it.utils.OptionsDict]:
    """ Get the standard parser and options. """

    parser = markdown_it.MarkdownIt('commonmark')

    for option in EXTRA_OPTIONS:
        parser.enable(option)

    for (plugin, options) in PLUGINS:
        parser.use(plugin, **options)

    return parser, parser.options

def _clean_text(content: str) -> str:
    """ Do some basic cleaning on text before parsing. """

    # Remove carriage returns.
    content = content.replace("\r", '')

    # Trim whitespace.
    content = content.strip()

    return content

# Returns (transformed text, tokens).
def _parse_text(raw_text: str, base_dir: str) -> typing.Tuple[str, typing.List[markdown_it.token.Token]]:
    """ Parse the text and returned the cleaned text and resulting parsed document. """

    clean_text = _clean_text(raw_text)

    if (len(clean_text) == 0):
        return '', []

    parser, _ = _get_parser()

    tokens = parser.parse(clean_text)
    tokens = _post_process(tokens)

    return clean_text.strip(), tokens

def _post_process(tokens: typing.List[markdown_it.token.Token]) -> typing.List[markdown_it.token.Token]:
    """
    Post-process the token stream.
    This allows us to edit the AST without needing the change the parser.
    """

    tokens = _add_root_block(tokens)
    tokens = _process_placeholders(tokens)
    tokens = _process_style(tokens)
    tokens = _process_html(tokens)
    tokens = _remove_empty_tokens(tokens)

    return tokens

def _add_root_block(tokens: typing.List[markdown_it.token.Token]) -> typing.List[markdown_it.token.Token]:
    """
    Add a root block element to the document.
    """

    if (len(tokens) == 0):
        return []

    open_token = markdown_it.token.Token('container_block_open', 'div', 1)
    open_token.block = True
    open_token.attrJoin('class', 'qg-root-block')
    open_token.meta[quizcomp.parser.common.TOKEN_META_KEY_ROOT] = True

    if (tokens[0].map is None):
        open_token.map = []
    else:
        open_token.map = list(tokens[0].map)

    close_token = markdown_it.token.Token('container_block_close', 'div', -1)

    return [open_token] + tokens + [close_token]

def _process_style(
        tokens: typing.Union[typing.List[markdown_it.token.Token], None],
        containing_block: typing.Union[markdown_it.token.Token, None] = None,
        ) -> typing.List[markdown_it.token.Token]:
    """
    Locate any style nodes, parse them, remove them, and hoist their content to the containing block.
    """

    if (tokens is None):
        return []

    remove_indexes = []
    for (i, token) in enumerate(tokens):
        # If this is a block, then mark it as the current block.
        # Any discovered style get's hoisted to the containing block.
        if (token.type == 'container_block_open'):
            containing_block = token
        elif ((token.type in HTML_TOKENS) and (token.content.strip().startswith('<style>'))):
            # Style nodes are HTML with a 'style' tag.

            if (containing_block is None):
                raise ValueError("Found a style node that does not have a containing block.")

            style = _process_style_content(token.content)
            containing_block.meta[quizcomp.parser.common.TOKEN_META_KEY_STYLE] = style

            # Mark this token for removal.
            remove_indexes.append(i)

        # Check all children.
        if (_has_children(token)):
            token.children = _process_style(token.children, containing_block = containing_block)

    for remove_index in sorted(list(set(remove_indexes)), reverse = True):
        tokens.pop(remove_index)

    return tokens

def _process_style_content(raw_content: str) -> typing.Dict[str, typing.Any]:
    """ Get the style content from some text. """

    raw_content = raw_content.strip()

    # Get content without tags ('<style>', '</style>').
    content = re.sub(r'\s+', ' ', raw_content)
    content = re.sub(r'^<style>(.*)</style>$', r'\1', content).strip()

    # Ignore empty style.
    if (len(content) == 0):
        return {}

    # If the content does not start with a '{', then assume the braces were left out and add them.
    # We will also ignore content that starts with a '[' (a JSON list), that will be handled later.
    if (content[0] not in ['{', '[']):
        content = "{%s}" % (content)

    try:
        style = edq.util.json.loads(content)
        if (not isinstance(style, dict)):
            raise ValueError(f"Style is not a JSON object, found: '{type(style)}'.")
    except Exception as ex:
        raise ValueError(('Failed to load style tag.'  # pylint: disable=raise-missing-from
                + ' Style content must be a JSON object (start/end braces may be omitted).'
                + f" Original exception message: '{ex}'."
                + f" Found:\n---\n{raw_content}\n---"))

    return style

def _remove_empty_tokens(tokens: typing.Union[typing.List[markdown_it.token.Token], None]) -> typing.List[markdown_it.token.Token]:
    """
    Remove any inline's without text or blocks without children.
    """

    if (tokens is None):
        return []

    # Keep looping until nothing is removed.
    while True:
        remove_indexes = []
        for (i, token) in enumerate(tokens):
            # Remove empty leaf content nodes.
            if ((token.type in quizcomp.parser.common.CONTENT_NODES) and (token.content == '')):
                remove_indexes.append(i)

            # Check children for removal.
            if (_has_children(token)):
                token.children = _remove_empty_tokens(token.children)

                # Remove nodes that have been emptied out.
                if (len(token.children) == 0):
                    remove_indexes.append(i)

            # Check for empty containers.
            # Look for this token being the open, and the next token being the close.
            if ((i < (len(tokens) - 1)) and (token.type.endswith('_open')) and (tokens[i + 1].type.endswith('_close'))):
                next_token = tokens[i + 1]
                base_type = re.sub('_open$', '', token.type)
                next_base_type = re.sub('_close$', '', next_token.type)

                # Remove if types match and neither has any kids (close should never have kids).
                if ((base_type == next_base_type) and (not _has_children(token)) and (not _has_children(next_token))):
                    remove_indexes += [i, i + 1]

        for remove_index in sorted(list(set(remove_indexes)), reverse = True):
            tokens.pop(remove_index)

        if (len(remove_indexes) == 0):
            break

    return tokens

def _process_placeholders(tokens: typing.Union[typing.List[markdown_it.token.Token], None]) -> typing.List[markdown_it.token.Token]:
    """
    Find any placeholder HTML tags and replace them with a placeholder token.
    plceholder tags must either be an HTML block or inline with the same parent.
    """

    if (tokens is None):
        return []

    remove_indexes = []

    # Use a non-standard loop so that we can manually advance the index within the loop.
    i = -1
    while (i < (len(tokens) - 1)):
        i += 1
        token = tokens[i]

        if (token.type == 'html_block'):
            if ((not token.content) or (not token.content.strip().startswith('<placeholder'))):
                continue

            # Replace the HTML block token with a placeholder token.
            tokens[i] = _create_placeholder_token(token)
        elif (token.type == 'html_inline'):
            if ((not token.content) or (not token.content.strip().startswith('<placeholder'))):
                continue

            open_tag_index = i
            close_tag_index = None

            # Look for the close tag at this same level (under the same parent).
            for j in range(i + 1, len(tokens)):
                other_token = tokens[j]
                if (other_token.type != 'html_inline'):
                    continue

                if ((not other_token.content) or (not other_token.content.strip() == '</placeholder>')):
                    continue

                close_tag_index = j
                break

            if (close_tag_index is None):
                raise ValueError("Could not find closing tag for <placeholder>.")

            if ((close_tag_index - open_tag_index) < 2):
                raise ValueError("Did not find any content inside a <placeholder> tag.")

            if ((close_tag_index - open_tag_index) > 2):
                raise ValueError("Found too much content inside a <placeholder> tag, it shoud have only plain text.")

            text_token_index = open_tag_index + 1
            text_token = tokens[text_token_index]
            if (text_token.type != 'text'):
                raise ValueError("Found non-text content inside a <placeholder> tag, it shoud have only plain text.")

            # All tokens (open, content/label, close) are accounted for.
            # Replace the content node and remove the open/close tags.
            tokens[text_token_index] = _create_placeholder_token(text_token)
            remove_indexes += [open_tag_index, close_tag_index]

            # Advance to the close token.
            i = close_tag_index

        if (_has_children(token)):
            token.children = _process_placeholders(token.children)

    for remove_index in sorted(list(set(remove_indexes)), reverse = True):
        tokens.pop(remove_index)

    return tokens

def _create_placeholder_token(token: markdown_it.token.Token) -> markdown_it.token.Token:
    """ Create a tag for answer placeholders. """

    # Fetch the label in the tag.
    label = re.sub(r'\s+', ' ', token.content.strip())
    label = re.sub(r'^<placeholder.*>(.*)</placeholder>$', r'\1', label).strip()
    if (len(label) == 0):
        raise ValueError("Found an empty '<placeholder>' tag.")

    return markdown_it.token.Token(
            type = 'placeholder', tag = '', nesting = 0,
            map = token.map, content = label)

def _process_html(tokens: typing.Union[typing.List[markdown_it.token.Token], None]) -> typing.List[markdown_it.token.Token]:
    """
    Remove or replacec all HTML tags.
    This will recursively descend to find all tags.
    Line breaks will be replaced with hard breaks.
    """

    if (tokens is None):
        return []

    remove_indexes = []
    for (i, token) in enumerate(tokens):
        if (token.type in HTML_TOKENS):
            if (token.content.strip().startswith('<br')):
                tokens[i] = markdown_it.token.Token(
                        type = 'hardbreak', tag = 'br', nesting = 0,
                        map = token.map)
            else:
                remove_indexes.append(i)

        if (_has_children(token)):
            token.children = _process_html(token.children)

    for remove_index in sorted(list(set(remove_indexes)), reverse = True):
        tokens.pop(remove_index)

    return tokens

def _has_children(token: markdown_it.token.Token) -> bool:
    """ Check if the given token has children. """

    return ((token.children is not None) and (len(token.children) > 0))
