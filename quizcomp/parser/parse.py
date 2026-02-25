import re

import markdown_it
import mdit_py_plugins.container
import mdit_py_plugins.dollarmath

import quizcomp.parser.document
import quizcomp.util.json

_parser = None
_options = None

EXTRA_OPTIONS = [
    'table',
]

PLUGINS = [
    (mdit_py_plugins.dollarmath.dollarmath_plugin, {}),
    (mdit_py_plugins.container.container_plugin, {'name': 'block'}),
]

HTML_TOKENS = {
    'html_block',
    'html_inline',
}

def _get_parser():
    _parser = markdown_it.MarkdownIt('commonmark')

    for option in EXTRA_OPTIONS:
        _parser.enable(option)

    for (plugin, options) in PLUGINS:
        _parser.use(plugin, **options)

    _options = _parser.options

    return _parser, _options

def _clean_text(text):
    # Remove carriage returns.
    text = text.replace("\r", '')

    # Trim whitespace.
    text = text.strip();

    return text

# Returns (transformed text, tokens).
def _parse_text(text, base_dir):
    text = _clean_text(text)

    parser, _ = _get_parser()

    tokens = parser.parse(text)
    tokens = _post_process(tokens)

    document = quizcomp.parser.document.ParsedDocument(tokens, base_dir = base_dir)

    return (text.strip(), document)

def _post_process(tokens):
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

def _add_root_block(tokens):
    """
    Add a root block element to the document.
    """

    if (len(tokens) == 0):
        return []

    open_token = markdown_it.token.Token('container_block_open', 'div', 1)
    open_token.block = True
    open_token.map = list(tokens[0].map)
    open_token.attrJoin('class', 'qg-root-block')
    open_token.meta[quizcomp.parser.common.TOKEN_META_KEY_ROOT] = True

    close_token = markdown_it.token.Token('container_block_close', 'div', -1)

    return [open_token] + tokens + [close_token]

def _process_style(tokens, containing_block = None):
    """
    Locate any style nodes, parse them, remove them, and hoist their content to the containing block.
    """

    remove_indexes = []
    for i in range(len(tokens)):
        token = tokens[i]

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

def _process_style_content(raw_content):
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
        style = quizcomp.util.json.loads(content)
        if (not isinstance(style, dict)):
            raise ValueError("Style is not a JSON object, found: '%s'." % (type(style)))
    except Exception as ex:
        raise ValueError(('Failed to load style tag.'
                + ' Style content must be a JSON object (start/end braces may be omitted).'
                + " Original exception message: '%s'." % (ex)
                + " Found:\n---\n%s\n---" % (raw_content)))

    return style

def _remove_empty_tokens(tokens):
    """
    Remove any inline's without text or blocks without children.
    """

    # Keep looping until nothing is removed.
    while True:
        remove_indexes = []
        for i in range(len(tokens)):
            token = tokens[i]

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

def _process_placeholders(tokens):
    """
    Find any placeholder HTML tags and replace them with a placeholder token.
    plceholder tags must either be an HTML block or inline with the same parent.
    """

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

def _create_placeholder_token(token):
    # Fetch the label in the tag.
    label = re.sub(r'\s+', ' ', token.content.strip())
    label = re.sub(r'^<placeholder.*>(.*)</placeholder>$', r'\1', label).strip()
    if (len(label) == 0):
        raise ValueError("Found an empty '<placeholder>' tag.")

    return markdown_it.token.Token(
            type = 'placeholder', tag = '', nesting = 0,
            map = token.map, content = label)

def _process_html(tokens):
    """
    Remove or replacec all HTML tags.
    This will recursively descend to find all tags.
    Line breaks will be replaced with hard breaks.
    """

    remove_indexes = []
    for i in range(len(tokens)):
        token = tokens[i]

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

def _has_children(token):
    return ((token.children is not None) and (len(token.children) > 0))
