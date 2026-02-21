import copy
import os
import re
import types

import markdown_it.renderer

import quizcomp.constants
import quizcomp.parser.common
import quizcomp.parser.image
import quizcomp.parser.math
import quizcomp.parser.style

HTML_BORDER_SPEC = '1px solid black'

ADDITIONAL_STYLE = {
    'paragraph_open': [
        'margin-top: 0',
    ],
    'fence_open': [
        'margin-top: 0',
    ],
    'code_block_open': [
        'margin-top: 0',
    ],
    'code_inline': [
        'font-family: SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace',
        'font-size: 0.875em',
        'background-color: #eef2ff',
        'color: #3730a3',
        'padding: 0.15em 0.4em',
        'border-radius: 4px',
        'border: 1px solid #c7d2fe',
        'margin-left: 0.15em',
        'margin-right: 0.15em',
    ],
    'math_inline': [
        'margin-left: 0.3em',
        'margin-right: 0.3em',
    ],
}

class QuizComposerRendererHTML(markdown_it.renderer.RendererHTML):
    def render(self, tokens, options, env):
        # Override the main rendering function to attatch style.
        self._style_override_helper(tokens)
        return super().render(tokens, options, env)

    def _style_override_helper(self, tokens):
        if (tokens is None):
            return

        for token in tokens:
            if (token.type in ADDITIONAL_STYLE):
                _join_html_style(token, ADDITIONAL_STYLE.get(token.type, []))

            self._style_override_helper(token.children)

    def image(self, tokens, idx, options, env,
            force_raw_image_src = False, process_token = None):
        # Do custom rendering and then pass onto super.

        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        base_dir = context.get(quizcomp.parser.common.BASE_DIR_KEY, '.')
        callback = context.get(quizcomp.parser.common.CONTEXT_KEY_IMAGE_CALLBACK, None)

        # Set width.
        width_float = quizcomp.parser.style.get_image_width(style)
        tokens[idx].attrSet('width', "%0.2f%%" % (width_float * 100.0))

        original_src = tokens[idx].attrGet('src')
        src = quizcomp.parser.image.handle_callback(callback, original_src, base_dir)
        path = os.path.realpath(os.path.join(base_dir, src))
        tokens[idx].attrSet('src', src)

        # Check the env to see if we need to force raw images.
        force_raw_image_src = force_raw_image_src or context.get(quizcomp.parser.common.CONTEXT_KEY_FORCE_RAW_IMAGE_SRC, False)

        if (force_raw_image_src or re.match(r'^http(s)?://', src) or src.startswith('data:image')):
            # Do not further modify the src if we are explicitly directed not to
            # or if it is an http or data URL.
            pass
        else:
            # Otherwise, do a base64 encoding of the image and embed it.
            mime, content = quizcomp.parser.image.encode_image(path)
            tokens[idx].attrSet('src', f"data:{mime};base64,{content}")

        # Last chance to change the token before HTML rendering.
        if (process_token is not None):
            tokens[idx] = process_token(tokens[idx], context, path)

        result = super().image(tokens, idx, options, env)

        # Reset the src so that future callback hits have the proper cache key.
        tokens[idx].attrSet('src', original_src)

        return result

    def container_block_open(self, tokens, idx, options, env):
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})

        # Add on a specific class.
        tokens[idx].attrJoin('class', 'qg-block')

        # Pull any style attatched to this block and put it in a copy of the context.
        context, full_style, block_style = quizcomp.parser.common.handle_block_style(tokens[idx].meta, context)
        env[quizcomp.parser.common.CONTEXT_ENV_KEY] = context

        # Attatch style based on if we are the root block.
        # If root use all style, otherwise just use the style for this block.
        active_style = block_style
        if (tokens[idx].meta.get(quizcomp.parser.common.TOKEN_META_KEY_ROOT, False)):
            active_style = full_style

        style_string = quizcomp.parser.style.compute_html_style_string(active_style)
        if (style_string != ''):
            tokens[idx].attrSet('style', style_string)

        # Send to super for further rendering.
        return super().renderToken(tokens, idx, options, env)

    def math_inline(self, tokens, idx, options, env):
        return quizcomp.parser.math.render(quizcomp.constants.FORMAT_HTML, True, tokens, idx, options, env)

    def math_block(self, tokens, idx, options, env):
        return quizcomp.parser.math.render(quizcomp.constants.FORMAT_HTML, False, tokens, idx, options, env)

    def placeholder(self, tokens, idx, options, env):
        return "<placeholder>%s</placeholder>" % (tokens[idx].content)

    def table_open(self, tokens, idx, options, env):
        token = tokens[idx]
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        table_style = [
            'border-collapse: collapse',
        ]

        if (quizcomp.parser.style.get_boolean_style_key(style, quizcomp.parser.style.KEY_TABLE_BORDER_TABLE, quizcomp.parser.style.DEFAULT_TABLE_BORDER_TABLE)):
            table_style.append("border: %s" % HTML_BORDER_SPEC)
        else:
            table_style.append('border-style: hidden')

        # HTML tables require extra encouragement to align.
        text_align = quizcomp.parser.style.get_alignment(style, quizcomp.parser.style.KEY_TEXT_ALIGN)
        if (text_align is not None):
            table_style.append("text-align: %s" % (text_align))

        _join_html_style(token, table_style)

        return super().renderToken(tokens, idx, options, env)

    def thead_open(self, tokens, idx, options, env):
        token = tokens[idx]
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        if (quizcomp.parser.style.get_boolean_style_key(style, quizcomp.parser.style.KEY_TABLE_HEAD_RULE, quizcomp.parser.style.DEFAULT_TABLE_HEAD_RULE)):
            _join_html_style(token, ["border-bottom: %s" % (HTML_BORDER_SPEC)])

        return super().renderToken(tokens, idx, options, env)

    def th_open(self, tokens, idx, options, env):
        token = tokens[idx]
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        self._cell_html(token, style)

        weight = 'normal'
        if (quizcomp.parser.style.get_boolean_style_key(style, quizcomp.parser.style.KEY_TABLE_HEAD_BOLD, quizcomp.parser.style.DEFAULT_TABLE_HEAD_BOLD)):
            weight = 'bold'

        _join_html_style(token, ["font-weight: %s" % (weight)])

        return super().renderToken(tokens, idx, options, env)

    def td_open(self, tokens, idx, options, env):
        token = tokens[idx]
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        self._cell_html(token, style)

        return super().renderToken(tokens, idx, options, env)

    def _cell_html(self, token, style):
        """
        Common cell rendering.
        """

        height = max(1.0, float(style.get(quizcomp.parser.style.KEY_TABLE_CELL_HEIGHT, quizcomp.parser.style.DEFAULT_TABLE_CELL_HEIGHT)))
        vertical_padding = height - 1.0

        width = max(1.0, float(style.get(quizcomp.parser.style.KEY_TABLE_CELL_WIDTH, quizcomp.parser.style.DEFAULT_TABLE_CELL_WIDTH)))
        horizontal_padding = width - 1.0

        cell_style = {
            'padding-top': "%0.2fem" % (vertical_padding / 2),
            'padding-bottom': "%0.2fem" % (vertical_padding / 2),
            'padding-left': "%0.2fem" % (horizontal_padding / 2),
            'padding-right': "%0.2fem" % (horizontal_padding / 2),
        }

        if (quizcomp.parser.style.get_boolean_style_key(style, quizcomp.parser.style.KEY_TABLE_BORDER_CELLS, quizcomp.parser.style.DEFAULT_TABLE_BORDER_CELLS)):
            cell_style['border'] = "%s" % (HTML_BORDER_SPEC)

        _join_html_style(token, [': '.join(item) for item in cell_style.items()])

def get_renderer(options):
    return QuizComposerRendererHTML(), options

def _join_html_style(token, rules):
    """
    Take all style rules to apply, add in any existing style, and set the style attribute.
    """

    if (len(rules) == 0):
        return

    existing_style = token.attrGet('style')
    if (existing_style is not None):
        rules = [existing_style] + rules

    style_string = '; '.join(rules)
    token.attrSet('style', style_string)
