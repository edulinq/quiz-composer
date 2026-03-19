"""
Style constants and base functionality.
"""

import typing

KEY_CONTENT_ALIGN: str = 'content-align'
KEY_FONT_SIZE: str = 'font-size'
KEY_IMAGE_WIDTH: str = 'image-width'
KEY_TABLE_BORDER_CELLS: str = 'table-border-cells'
KEY_TABLE_BORDER_TABLE: str = 'table-border-table'
KEY_TABLE_CELL_HEIGHT: str = 'table-cell-height'
KEY_TABLE_CELL_WIDTH: str = 'table-cell-width'
KEY_TABLE_HEAD_BOLD: str = 'table-head-bold'
KEY_TABLE_HEAD_RULE: str = 'table-head-rule'
KEY_TEXT_ALIGN: str = 'text-align'

DEFAULT_IMAGE_WIDTH: float = 1.0
DEFAULT_TABLE_BORDER_CELLS: bool = False
DEFAULT_TABLE_BORDER_TABLE: bool = False
DEFAULT_TABLE_CELL_HEIGHT: float = 1.5
DEFAULT_TABLE_CELL_WIDTH: float = 1.5
DEFAULT_TABLE_HEAD_BOLD: bool = True
DEFAULT_TABLE_HEAD_RULE: bool = True

ALLOWED_VALUES_ALIGNMENT_LEFT: str = 'left'
ALLOWED_VALUES_ALIGNMENT_CENTER: str = 'center'
ALLOWED_VALUES_ALIGNMENT_RIGHT: str = 'right'
ALLOWED_VALUES_ALIGNMENT: typing.List[str] = [
    ALLOWED_VALUES_ALIGNMENT_LEFT,
    ALLOWED_VALUES_ALIGNMENT_CENTER,
    ALLOWED_VALUES_ALIGNMENT_RIGHT
]

FLEXBOX_ALIGNMENT: typing.Dict[str, str] = {
    ALLOWED_VALUES_ALIGNMENT_LEFT: 'flex-start',
    ALLOWED_VALUES_ALIGNMENT_CENTER: 'center',
    ALLOWED_VALUES_ALIGNMENT_RIGHT: 'flex-end',
}

TEX_BLOCK_ALIGNMENT: typing.Dict[str, str] = {
    ALLOWED_VALUES_ALIGNMENT_LEFT: 'flushleft',
    ALLOWED_VALUES_ALIGNMENT_CENTER: 'center',
    ALLOWED_VALUES_ALIGNMENT_RIGHT: 'flushright',
}

def get_alignment(style: typing.Dict[str, typing.Any], key: str, default_value: typing.Union[str, None] = None) -> typing.Union[str, None]:
    """ Get the specified alignment, or None if there is no specified alignment (or default). """

    alignment = style.get(key, None)
    if (alignment is None):
        return default_value

    alignment = str(alignment).lower()
    if (alignment not in ALLOWED_VALUES_ALIGNMENT):
        raise ValueError(f"Unknown value for '{key}' style key '{alignment}'. Allowed values: {ALLOWED_VALUES_ALIGNMENT}.")

    return alignment

def get_boolean_style_key(style: typing.Dict[str, typing.Any], key: str, default_value: bool = False) -> bool:
    """ Get a boolean style key. """

    value = style.get(key, default_value)
    if (value is None):
        return default_value

    return (value is True)

def get_image_width(style: typing.Dict[str, typing.Any]) -> float:
    """ Get the image width. """

    width = style.get(KEY_IMAGE_WIDTH, None)
    if (width is None):
        width = DEFAULT_IMAGE_WIDTH

    return float(width)

def compute_html_style_string(style: typing.Dict[str, typing.Any]) -> str:
    """
    Compute the attribute style string for an HTML tag.
    """

    attributes = []

    content_align = get_alignment(style, KEY_CONTENT_ALIGN)
    if (content_align is not None):
        attributes.append("display: flex")
        attributes.append("flex-direction: column")
        attributes.append("justify-content: flex-start")
        attributes.append(f"align-items: {FLEXBOX_ALIGNMENT[content_align]}")

    text_align = get_alignment(style, KEY_TEXT_ALIGN)
    if (text_align is not None):
        attributes.append(f"text-align: {text_align}")

    font_size = style.get(KEY_FONT_SIZE, None)
    if (font_size is not None):
        attributes.append(f"font-size: {float(font_size):0.2f}pt")

    if (len(attributes) == 0):
        return ''

    return '; '.join(attributes)

def compute_tex_fixes(style: typing.Dict[str, typing.Any]) -> typing.Tuple[typing.List[str], typing.List[str]]:
    """
    Compute the fixes (prefixes, suffixes) for a portion of TeX.
    These are things like `\\begin{center}`/`\\end{center}`.
    The returned lists have matching indexes.
    """

    # The beginning and ends of groups.
    # These will match 1-1.
    prefixes = []
    suffixes = []

    content_align = get_alignment(style, KEY_CONTENT_ALIGN)
    if (content_align is not None):
        env_name = TEX_BLOCK_ALIGNMENT[content_align]
        prefixes.append("\\begin{%s}" % (env_name))
        suffixes.append("\\end{%s}" % (env_name))

    font_size = style.get(KEY_FONT_SIZE, None)
    if (font_size is not None):
        font_size = float(font_size)
        # 1.2 is the default size for baseline skip relative to font size.
        # See: https://ctan.math.illinois.edu/macros/latex/contrib/fontsize/fontsize.pdf
        baseline_skip = 1.2 * font_size

        prefixes.append('\\begingroup\\fontsize{%.2fpt}{%.2fpt}\\selectfont' % (font_size, baseline_skip))
        suffixes.append('\\endgroup')

    return prefixes, suffixes
