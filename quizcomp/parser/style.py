"""
Style constants and base functionality.
"""

KEY_CONTENT_ALIGN = 'content-align'
KEY_FONT_SIZE = 'font-size'
KEY_IMAGE_WIDTH = 'image-width'
KEY_TABLE_BORDER_CELLS = 'table-border-cells'
KEY_TABLE_BORDER_TABLE = 'table-border-table'
KEY_TABLE_CELL_HEIGHT = 'table-cell-height'
KEY_TABLE_CELL_WIDTH = 'table-cell-width'
KEY_TABLE_HEAD_BOLD = 'table-head-bold'
KEY_TABLE_HEAD_RULE = 'table-head-rule'
KEY_TEXT_ALIGN = 'text-align'

DEFAULT_IMAGE_WIDTH = 1.0
DEFAULT_TABLE_BORDER_CELLS = False
DEFAULT_TABLE_BORDER_TABLE = False
DEFAULT_TABLE_CELL_HEIGHT = 1.5
DEFAULT_TABLE_CELL_WIDTH = 1.5
DEFAULT_TABLE_HEAD_BOLD = True
DEFAULT_TABLE_HEAD_RULE = True

ALLOWED_VALUES_ALIGNMENT_LEFT = 'left'
ALLOWED_VALUES_ALIGNMENT_CENTER = 'center'
ALLOWED_VALUES_ALIGNMENT_RIGHT = 'right'
ALLOWED_VALUES_ALIGNMENT = [
    ALLOWED_VALUES_ALIGNMENT_LEFT,
    ALLOWED_VALUES_ALIGNMENT_CENTER,
    ALLOWED_VALUES_ALIGNMENT_RIGHT
]

FLEXBOX_ALIGNMENT = {
    ALLOWED_VALUES_ALIGNMENT_LEFT: 'flex-start',
    ALLOWED_VALUES_ALIGNMENT_CENTER: 'center',
    ALLOWED_VALUES_ALIGNMENT_RIGHT: 'flex-end',
}

TEX_BLOCK_ALIGNMENT = {
    ALLOWED_VALUES_ALIGNMENT_LEFT: 'flushleft',
    ALLOWED_VALUES_ALIGNMENT_CENTER: 'center',
    ALLOWED_VALUES_ALIGNMENT_RIGHT: 'flushright',
}

def get_alignment(style, key, default_value = None):
    alignment = style.get(key, None)
    if (alignment is None):
        return default_value

    alignment = str(alignment).lower()
    if (alignment not in ALLOWED_VALUES_ALIGNMENT):
        raise ValueError("Unknown value for '%s' style key '%s'. Allowed values: '%s'." % (key, alignment, ALLOWED_VALUES_ALIGNMENT))

    return alignment

def get_boolean_style_key(style, key, default_value = None):
    value = style.get(key, default_value)
    if (value is None):
        return default_value

    return (value is True)

def get_image_width(style):
    width = style.get(KEY_IMAGE_WIDTH, None)
    if (width is None):
        width = DEFAULT_IMAGE_WIDTH

    return float(width)

def compute_html_style_string(style):
    """
    Compute the attribute style string for an HTML tag.
    """

    attributes = []

    content_align = get_alignment(style, KEY_CONTENT_ALIGN)
    if (content_align is not None):
        attributes.append("display: flex")
        attributes.append("flex-direction: column")
        attributes.append("justify-content: flex-start")
        attributes.append("align-items: %s" % (FLEXBOX_ALIGNMENT[content_align]))

    text_align = get_alignment(style, KEY_TEXT_ALIGN)
    if (text_align is not None):
        attributes.append("text-align: %s" % (text_align))

    font_size = style.get(KEY_FONT_SIZE, None)
    if (font_size is not None):
        attributes.append("font-size: %.2fpt" % (float(font_size)))

    if (len(attributes) == 0):
        return ''

    return '; '.join(attributes)

def compute_tex_fixes(style):
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
