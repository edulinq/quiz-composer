import copy
import typing

ENCODING: str = 'utf-8'

ENV_KEY_CONTEXT: str = 'qg_context'

TOKEN_META_KEY_ROOT: str = 'qg_root'
TOKEN_META_KEY_STYLE: str = 'qg_style'

CONTENT_NODES: typing.Set[str] = {
    'code_block',
    'code_inline',
    'fence',
    'math_block',
    'math_inline',
    'placeholder',
    'text',
    'text_special',
}

class RenderContext:
    """ A simple struct for carrying around the context for rendering. """

    def __init__(self,
            base_dir: typing.Union[str, None] = None,
            source_path: typing.Union[str, None] = None,
            style: typing.Union[typing.Dict[str, typing.Any], None] = None,
            text_allow_all_characters: bool = False,
            text_allow_special_text: bool = False,
            force_raw_image_src: bool = False,
            **kwargs: typing.Any) -> None:
        if (base_dir is None):
            base_dir = '.'

        self.base_dir: str = base_dir
        """ A base directory to resolve any relative paths. """

        self.source_path: typing.Union[str, None] = source_path
        """ If the document to render was read from a file, this path points to that file. """

        if (style is None):
            style = {}

        self.style: typing.Dict[str, typing.Any] = style
        """ Style information to use for rendering. """

        self.text_allow_all_characters: bool = text_allow_all_characters
        """ Allow all characters when rendering as `text`. """

        self.text_allow_special_text: bool = text_allow_special_text
        """ Allow "special text" when when rendering as `text`. """

        self.force_raw_image_src: bool = force_raw_image_src
        """ Do not do any processing on an image's source. """

    def copy(self) -> 'RenderContext':
        """ Get a deep copy. """

        return copy.deepcopy(self)

def handle_block_style(
        block_info: typing.Dict[str, typing.Any],
        context: RenderContext,
        ) -> typing.Tuple[RenderContext, typing.Dict[str, typing.Any]]:
    """
    Handle style associated with a block by extracting the style,
    and creating a copy of the context with the new style (if any block style exists).
    Returns: (context, block style).
    """

    block_style = block_info.get(TOKEN_META_KEY_STYLE, None)
    if ((block_style is None) or (len(block_style) == 0)):
        return context, {}

    new_context = context.copy()
    new_context.style.update(block_style)

    return new_context, block_style
