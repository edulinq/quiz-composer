import copy
import types

ENCODING = 'utf-8'

BASE_DIR_KEY = 'base_dir'

CONTEXT_ENV_KEY = 'qg_context'
CONTEXT_KEY_STYLE = 'style'
CONTEXT_KEY_IMAGE_CALLBACK = 'image_path_callback'
CONTEXT_KEY_FORCE_RAW_IMAGE_SRC = 'force_raw_image_src'
CONTEXT_KEY_TEXT_ALLOW_ALL_CHARACTERS = 'text_allow_all_characters'
CONTEXT_KEY_TEXT_ALLOW_SPECIAL_TEXT = 'text_allow_special_text'

TOKEN_META_KEY_ROOT = 'qg_root'
TOKEN_META_KEY_STYLE = 'qg_style'

CONTENT_NODES = {
    'code_block',
    'code_inline',
    'fence',
    'math_block',
    'math_inline',
    'placeholder',
    'text',
    'text_special',
}

def handle_block_style(block_info, context):
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

def prep_context(context, options = {}):
    """
    Return an immutable copy of the context with any of the specified additional value.
    Will make a deep copy if necessary.
    """

    if (isinstance(context, types.MappingProxyType) and (len(options) == 0)):
        return context

    context = dict(context)
    if (len(options) > 0):
        context = _partial_deep_copy(context)
        context.update(options)

    return types.MappingProxyType(context)

def _partial_deep_copy(source_dict):
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
