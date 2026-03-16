import logging
import os
import typing

import quizcomp.constants
import quizcomp.parser.ast
import quizcomp.parser.common
import quizcomp.parser.image
import quizcomp.parser.renderer.base
import quizcomp.parser.style

TEX_REPLACEMENTS: typing.Dict[str, str] = {
    # Specially handle braces and slashes to avoid clobbering other replacements.
    '{': 'ZZZzzz  OPEN BRACE REPLACEMENT  zzzZZZ',
    '}': 'ZZZzzz  CLOSE BRACE REPLACEMENT  zzzZZZ',
    '\\': 'ZZZzzz  BACKSLASH REPLACEMENT  zzzZZZ',

    '|': '\\textbar{}',
    '$': '\\$',
    '#': '\\#',
    '%': '\\%',
    '^': '\\^',
    '_': '\\_',
    'π': '$\\pi$',
    '`': '\\`{}',

    'ZZZzzz  OPEN BRACE REPLACEMENT  zzzZZZ': '\\{',
    'ZZZzzz  CLOSE BRACE REPLACEMENT  zzzZZZ': '\\}',
    'ZZZzzz  BACKSLASH REPLACEMENT  zzzZZZ': '\\textbackslash{}',
}

VERB_CHARACTERS: typing.List[str] = ['|', '!', '@', '#', '$', '^', '&', '-', '_', '=', '+']

TEX_TEXT_TABLE_ALIGNMENT: typing.Dict[str, str] = {
    quizcomp.parser.style.ALLOWED_VALUES_ALIGNMENT_LEFT: 'l',
    quizcomp.parser.style.ALLOWED_VALUES_ALIGNMENT_CENTER: 'c',
    quizcomp.parser.style.ALLOWED_VALUES_ALIGNMENT_RIGHT: 'r',
}

# HTML and CommonMark support six levels of headings,
# we will use these analogues for TeX.
# The only standard TeX heading we are not using is \part{},
# which is before \chapter{}.
HEADINGS: typing.List[str] = [
    'chapter',
    'section',
    'subsection',
    'subsubsection',
    'paragraph',
    'subparagraph',
]

class QuizComposerRendererTex(quizcomp.parser.renderer.base.QuizComposerRendererBase):
    """ A renderer for TeX. """

    __output__ = quizcomp.constants.FORMAT_TEX

    def _container_block(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        # Pull any style attatched to this block and put it in a copy of the context.
        context, full_style, block_style = quizcomp.parser.common.handle_block_style(node, context)

        # Compute fixes using different styles depending on if this block is root.
        # If we are root, then we need to use all style.
        # If we are not root, then earlier blocks would have already applied other style,
        # and we only need the block style.
        active_style = block_style
        if (node.get(quizcomp.parser.common.TOKEN_META_KEY_ROOT, False)):
            active_style = full_style

        prefixes, suffixes = quizcomp.parser.style.compute_tex_fixes(active_style)
        child_content = [self._render_node(child, context) for child in node.children()]

        content = prefixes + child_content + list(reversed(suffixes))

        return "\n\n".join(content)

    def _text(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return tex_escape(node.text())

    def _softbreak(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return "\n"

    def _hardbreak(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return '~\\newline\n'

    def _em(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return r"\textit{%s}" % (content)

    def _strong(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return r"\textbf{%s}" % (content)

    def _fence(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        language_string = ''

        info = node.get('info', None)
        if ((info is not None) and (len(info) > 0)):
            language_string = "[language=%s]" % (info)

        return "\\begin{lstlisting}%s\n%s\n\\end{lstlisting}" % (language_string, node.text().rstrip())

    def _code_block(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        """
        This token is poorly named, it is actually an indented code block.
        Treat it like a fence with no info string.
        """

        return self._fence(node, context)

    def _code_inline(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        text = node.text()

        delim = None
        for char in VERB_CHARACTERS:
            if (char not in text):
                delim = char
                break

        if (delim is None):
            raise ValueError("Could not find a delimiter to use with TeX's `\verb'.")

        return r"\verb%s%s%s" % (delim, text, delim)

    def _math_block(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        text = node.text().strip()
        return f"$$\n{text}\n$$"

    def _math_inline(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        text = node.text().strip()
        return f"$ {text} $"

    def _image(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})
        base_dir = context.get(quizcomp.parser.common.BASE_DIR_KEY, '.')
        callback = context.get(quizcomp.parser.common.CONTEXT_KEY_IMAGE_CALLBACK, None)

        src = node.get('src', '')
        src = quizcomp.parser.image.handle_callback(callback, src, base_dir)

        width_float = quizcomp.parser.style.get_image_width(style)
        path = os.path.realpath(os.path.join(base_dir, src))

        return r"\includegraphics[width=%0.2f\textwidth]{%s}" % (width_float, src)

    def _link(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        text = ''.join([self._render_node(child, context) for child in node.children()]).strip()
        url = node.get('href', '')

        if (len(text) == 0):
            return r"\url{%s}" % (url)

        return r"\href{%s}{%s}" % (url, text)

    def _placeholder(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        text = tex_escape(node.text())
        return r"\textsc{<%s>}" % (text)

    def _table(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        border_table = quizcomp.parser.style.get_boolean_style_key(style, quizcomp.parser.style.KEY_TABLE_BORDER_TABLE, quizcomp.parser.style.DEFAULT_TABLE_BORDER_TABLE)
        border_cells = quizcomp.parser.style.get_boolean_style_key(style, quizcomp.parser.style.KEY_TABLE_BORDER_CELLS, quizcomp.parser.style.DEFAULT_TABLE_BORDER_CELLS)
        default_alignment = quizcomp.parser.style.get_alignment(style, quizcomp.parser.style.KEY_TEXT_ALIGN, default_value = quizcomp.parser.style.ALLOWED_VALUES_ALIGNMENT_CENTER)

        column_infos = _discover_column_info(node)

        column_join = ''
        if (border_cells):
            column_join = '|'

        # Build column specifiers.
        column_specifiers = []
        for column_info in column_infos:
            raw_alignment = str(column_info.get('text-align', default_alignment))
            column_specifiers.append(TEX_TEXT_TABLE_ALIGNMENT.get(raw_alignment, quizcomp.parser.style.ALLOWED_VALUES_ALIGNMENT_LEFT))
        column_spec = column_join.join(column_specifiers)

        if (border_table):
            column_spec = '|' + column_spec + '|'

        lines = [
            r'\begin{tabular}{ ' + column_spec + ' }',
        ]

        if (border_table):
            lines.append(r'\hline')

        lines.append("\n".join([self._render_node(child, context) for child in node.children()]))

        if (border_table):
            lines.append(r'\hline')

        lines += [
            r'\end{tabular}',
        ]

        lines = _apply_tex_table_style(style, lines)

        return "\n".join(lines)

    def _thead(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})
        head_rule = quizcomp.parser.style.get_boolean_style_key(style, quizcomp.parser.style.KEY_TABLE_HEAD_RULE, quizcomp.parser.style.DEFAULT_TABLE_HEAD_RULE)

        content = "\n".join([self._render_node(child, context) for child in node.children()])

        if (head_rule):
            content += '\n\\hline'

        return content

    def _tbody(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})
        border_cells = quizcomp.parser.style.get_boolean_style_key(style, quizcomp.parser.style.KEY_TABLE_BORDER_CELLS, quizcomp.parser.style.DEFAULT_TABLE_BORDER_CELLS)

        delim = "\n"
        if (border_cells):
            delim = "\n\\hline\n"

        content = delim.join([self._render_node(child, context) for child in node.children()])
        return content

    def _tr(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        content = ' & '.join([self._render_node(child, context) for child in node.children()])
        return content + ' \\\\'

    def _th(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})
        bold = quizcomp.parser.style.get_boolean_style_key(style, quizcomp.parser.style.KEY_TABLE_HEAD_BOLD, quizcomp.parser.style.DEFAULT_TABLE_HEAD_BOLD)

        content = ''.join([self._render_node(child, context) for child in node.children()])

        if (bold):
            content = "\\textbf{%s}" % (content)

        return content

    def _td(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return content

    def _bullet_list(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        items = '\n'.join([self._render_node(child, context) for child in node.children()])
        return "\\begin{itemize}\n" + items + "\n\\end{itemize}"

    def _ordered_list(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        items = '\n'.join([self._render_node(child, context) for child in node.children()])
        return "\\begin{enumerate}\n" + items + "\n\\end{enumerate}"

    def _list_item(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return "    \\item " + content

    def _hr(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        return "\\hrulefill"

    def _heading(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        level = self.parse_heading_level(node)

        index = level - 1
        if ((index < 0) or (index >= len(HEADINGS))):
            raise ValueError("Heading index is out of range: %d." % (index))

        heading = HEADINGS[index]
        content = ''.join([self._render_node(child, context) for child in node.children()])

        return "\\%s{%s}" % (heading, content)

    def _blockquote(self, node: quizcomp.parser.ast.ASTNode, context: typing.Dict[str, typing.Any]) -> str:
        content = ''.join([self._render_node(child, context) for child in node.children()])
        return "\\begin{quote}\n%s\n\\end{quote}" % (content)

def get_renderer(options: typing.Dict[str, typing.Any]) -> typing.Tuple[QuizComposerRendererTex, typing.Dict[str, typing.Any]]:
    """ Get this renderer and options. """

    return QuizComposerRendererTex(), options

def tex_escape(text: str) -> str:
    """
    Prepare normal text for tex.
    """

    for key, value in TEX_REPLACEMENTS.items():
        text = text.replace(key, value)

    return text

def _apply_tex_table_style(style: typing.Dict[str, typing.Any], lines: typing.List[str]) -> typing.List[str]:
    """ Build the style for a table. """

    # Height
    height = max(1.0, float(style.get(quizcomp.parser.style.KEY_TABLE_CELL_HEIGHT, quizcomp.parser.style.DEFAULT_TABLE_CELL_HEIGHT)))
    prefix = [
        r'\begingroup',
        r'\renewcommand{\arraystretch}{%0.2f}' % (height),
    ]
    lines = prefix + lines
    lines.append(r'\endgroup')

    # Width
    width = max(1.0, float(style.get(quizcomp.parser.style.KEY_TABLE_CELL_WIDTH, quizcomp.parser.style.DEFAULT_TABLE_CELL_WIDTH)))
    prefix = [
        r'\begingroup',
        r'\setlength{\tabcolsep}{%0.2fem}' % (width),
    ]
    lines = prefix + lines
    lines.append(r'\endgroup')

    return lines

def _discover_column_info(
        node: quizcomp.parser.ast.ASTNode,
        info: typing.Union[typing.List[typing.Dict[str, typing.Any]], None] = None,
        ) -> typing.List[typing.Dict[str, typing.Any]]:
    """
    Descend into a table to figure out how many columns there are and if a column has alignment information.
    We will not make assumptions about symmetric rows or existence of headers.
    The largest row will determine width, and the last instance of styling information in a column will determine alignment.
    """

    if (info is None):
        info = []

    type = node.type()
    if (type not in {'table', 'thead', 'tbody', 'tr', 'td', 'th'}):
        return info

    children = node.children()

    if (type in {'table', 'thead', 'tbody'}):
        for child in children:
            info = _discover_column_info(child, info = info)
        return info

    if (type == 'tr'):
        for i in range(len(children)):
            if (i >= len(info)):
                info.append({})

            info[i] = _discover_column_info_cells(children[i], style = info[i])

        return info

    logging.warning("Unexpected table node type '%s'." % (type))
    return info

def _discover_column_info_cells(
        node: quizcomp.parser.ast.ASTNode,
        style: typing.Union[typing.Dict[str, typing.Any], None] = None,
        ) -> typing.Dict[str, typing.Any]:
    """ Get the style for the table cells in this node. """

    if (style is None):
        style = {}

    type = node.type()
    if (type not in {'td', 'th'}):
        return style

    raw_style = node.get('style', '').strip()
    if (len(raw_style) == 0):
        return style

    rules = [part.strip() for part in raw_style.split(';')]
    for raw_rule in rules:
        key, value = [part.strip() for part in raw_rule.split(':', maxsplit = 1)]
        style[key] = value

    return style
