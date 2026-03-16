import copy
import typing

ENCODING: str = 'utf-8'

BASE_DIR_KEY: str = 'base_dir'

CONTEXT_ENV_KEY: str = 'qg_context'
CONTEXT_KEY_STYLE: str = 'style'
CONTEXT_KEY_IMAGE_CALLBACK: str = 'image_path_callback'
CONTEXT_KEY_FORCE_RAW_IMAGE_SRC: str = 'force_raw_image_src'
CONTEXT_KEY_TEXT_ALLOW_ALL_CHARACTERS: str = 'text_allow_all_characters'
CONTEXT_KEY_TEXT_ALLOW_SPECIAL_TEXT: str = 'text_allow_special_text'

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

def handle_block_style(
        block_info: typing.Dict[str, typing.Any],
        context: typing.Dict[str, typing.Any],
        ) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Dict[str, typing.Any], typing.Dict[str, typing.Any]]:
    """
    Handle style associated with a block by extracting the style, prepping a context with that style,
    and returning (context, full style, block style).
    """

    block_style = block_info.get(TOKEN_META_KEY_STYLE, {})
    style = context.get(CONTEXT_KEY_STYLE, {})

    if (len(block_style) > 0):
        style.update(block_style)
        context_value = {CONTEXT_KEY_STYLE: style}
        context = prep_context(context, context_value)

    return context, style, block_style

def prep_context(
        context: typing.Dict[str, typing.Any],
        options: typing.Union[typing.Dict[str, typing.Any], None] = None,
        ) -> typing.Dict[str, typing.Any]:
    """
    Return a copy of the context with any of the specified additional value.
    Will make a deep copy if necessary.
    """

    if (options is None):
        options = {}

    if (len(options) > 0):
        context = _partial_deep_copy(context)
        context.update(options)

    return context

def _partial_deep_copy(source_dict: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    """
    Only deep copy values that are dicts or lists, shallow copy the rest.
    This is especially important for types that are fully or mostly imutable or callables.
    """

    result = {}
    for (key, value) in source_dict.items():
        if (isinstance(value, (dict, list))):
            value = copy.deepcopy(value)

        result[key] = value

    return result
