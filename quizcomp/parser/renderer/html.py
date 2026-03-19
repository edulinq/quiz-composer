import os
import re
import typing

import markdown_it.renderer
import markdown_it.token
import markdown_it.utils

import quizcomp.constants
import quizcomp.parser.common
import quizcomp.parser.image
import quizcomp.parser.math
import quizcomp.parser.renderer.base
import quizcomp.parser.style

HTML_BORDER_SPEC = '1px solid black'

@typing.runtime_checkable
class ProcessImageTokenFunction(typing.Protocol):
    """
    A function that is called when rendering an image to process the token before HTML rendering.
    """

    def __call__(self, token: markdown_it.token.Token, context: typing.Dict[str, typing.Any], path: str) -> markdown_it.token.Token:
        """ Process the image token before rendering. """

# pylint: disable=abstract-method
class QuizComposerRendererHTML(markdown_it.renderer.RendererHTML, quizcomp.parser.renderer.base.QuizComposerRendererBase):
    """
    A renderer for HTML.
    This builds of of the existing markdown_it.renderer.RendererHTML renderer.
    """

    __output__ = quizcomp.constants.FORMAT_HTML

    def image(self,  # type: ignore[override] # pylint: disable=arguments-renamed
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            force_raw_image_src: bool = False,
            process_token: typing.Union[ProcessImageTokenFunction, None] = None,
            **kwargs: typing.Any) -> str:
        """ Render an image. """

        # Do custom rendering and then pass onto super.

        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        base_dir = context.get(quizcomp.parser.common.BASE_DIR_KEY, '.')
        callback = context.get(quizcomp.parser.common.CONTEXT_KEY_IMAGE_CALLBACK, None)

        # Set width.
        width_float = quizcomp.parser.style.get_image_width(style)
        tokens[token_index].attrSet('width', f"{(width_float * 100.0):0.2f}%")

        original_src = str(tokens[token_index].attrGet('src'))
        src = quizcomp.parser.image.handle_callback(callback, original_src, base_dir)
        path = os.path.realpath(os.path.join(base_dir, src))
        tokens[token_index].attrSet('src', src)

        # Check the env to see if we need to force raw images.
        force_raw_image_src = force_raw_image_src or context.get(quizcomp.parser.common.CONTEXT_KEY_FORCE_RAW_IMAGE_SRC, False)

        if (force_raw_image_src or re.match(r'^http(s)?://', src) or src.startswith('data:image')):
            # Do not further modify the src if we are explicitly directed not to
            # or if it is an http or data URL.
            pass
        else:
            # Otherwise, do a base64 encoding of the image and embed it.
            mime, content = quizcomp.parser.image.encode_image(path)
            tokens[token_index].attrSet('src', f"data:{mime};base64,{content}")

        # Last chance to change the token before HTML rendering.
        if (process_token is not None):
            tokens[token_index] = process_token(tokens[token_index], context, path)

        result = super().image(tokens, token_index, options, env)

        # Reset the src so that future callback hits have the proper cache key.
        tokens[token_index].attrSet('src', original_src)

        return result

    def container_block_open(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            ) -> str:
        """ Render the opening of a block. """

        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})

        # Add on a specific class.
        tokens[token_index].attrJoin('class', 'qg-block')

        # Pull any style attached to this block and put it in a copy of the context.
        context, full_style, block_style = quizcomp.parser.common.handle_block_style(tokens[token_index].meta, context)
        env[quizcomp.parser.common.CONTEXT_ENV_KEY] = context

        # Attach style based on if we are the root block.
        # If root use all style, otherwise just use the style for this block.
        active_style = block_style
        if (tokens[token_index].meta.get(quizcomp.parser.common.TOKEN_META_KEY_ROOT, False)):
            active_style = full_style

        style_string = quizcomp.parser.style.compute_html_style_string(active_style)
        if (style_string != ''):
            tokens[token_index].attrSet('style', style_string)

        # Send to super for further rendering.
        return super().renderToken(tokens, token_index, options, env)

    def math_inline(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            ) -> str:
        """ Render inline math. """

        return quizcomp.parser.math.render(quizcomp.constants.FORMAT_HTML, True, tokens, token_index, options, env)

    def math_block(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            ) -> str:
        """ Render a math block. """

        return quizcomp.parser.math.render(quizcomp.constants.FORMAT_HTML, False, tokens, token_index, options, env)

    def placeholder(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            ) -> str:
        """ Render an answer placeholder. """

        return f"<placeholder>{tokens[token_index].content}</placeholder>"

    def table_open(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            ) -> str:
        """ Render the opening of a table. """

        token = tokens[token_index]
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        table_style = [
            'border-collapse: collapse',
        ]

        has_border = quizcomp.parser.style.get_boolean_style_key(
                style, quizcomp.parser.style.KEY_TABLE_BORDER_TABLE, quizcomp.parser.style.DEFAULT_TABLE_BORDER_TABLE)

        if (has_border):
            table_style.append(f"border: {HTML_BORDER_SPEC}")
        else:
            table_style.append('border-style: hidden')

        # HTML tables require extra encouragement to align.
        text_align = quizcomp.parser.style.get_alignment(style, quizcomp.parser.style.KEY_TEXT_ALIGN)
        if (text_align is not None):
            table_style.append(f"text-align: {text_align}")

        _join_html_style(token, table_style)

        return super().renderToken(tokens, token_index, options, env)

    def thead_open(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            ) -> str:
        """ Render the opening of a table header. """

        token = tokens[token_index]
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        has_head = quizcomp.parser.style.get_boolean_style_key(
                style, quizcomp.parser.style.KEY_TABLE_HEAD_RULE, quizcomp.parser.style.DEFAULT_TABLE_HEAD_RULE)

        if (has_head):
            _join_html_style(token, [f"border-bottom: {HTML_BORDER_SPEC}"])

        return super().renderToken(tokens, token_index, options, env)

    def th_open(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            ) -> str:
        """ Render the opening of a th. """

        token = tokens[token_index]
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        self._cell_html(token, style)

        weight = 'normal'
        use_bold = quizcomp.parser.style.get_boolean_style_key(
                style, quizcomp.parser.style.KEY_TABLE_HEAD_BOLD, quizcomp.parser.style.DEFAULT_TABLE_HEAD_BOLD)

        if (use_bold):
            weight = 'bold'

        _join_html_style(token, [f"font-weight: {weight}"])

        return super().renderToken(tokens, token_index, options, env)

    def td_open(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            ) -> str:
        """ Render the opening of a td. """

        token = tokens[token_index]
        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})
        style = context.get(quizcomp.parser.common.CONTEXT_KEY_STYLE, {})

        self._cell_html(token, style)

        return super().renderToken(tokens, token_index, options, env)

    def _cell_html(self, token: markdown_it.token.Token, style: typing.Dict[str, typing.Any]) -> None:
        """
        Common cell rendering.
        """

        height = max(1.0, float(style.get(quizcomp.parser.style.KEY_TABLE_CELL_HEIGHT, quizcomp.parser.style.DEFAULT_TABLE_CELL_HEIGHT)))
        vertical_padding = height - 1.0

        width = max(1.0, float(style.get(quizcomp.parser.style.KEY_TABLE_CELL_WIDTH, quizcomp.parser.style.DEFAULT_TABLE_CELL_WIDTH)))
        horizontal_padding = width - 1.0

        cell_style = {
            'padding-top': f"{(vertical_padding / 2):0.2f}em",
            'padding-bottom': f"{(vertical_padding / 2):0.2f}em",
            'padding-left': f"{(horizontal_padding / 2):0.2f}em",
            'padding-right': f"{(horizontal_padding / 2):0.2f}em",
        }

        if (quizcomp.parser.style.get_boolean_style_key(
                style, quizcomp.parser.style.KEY_TABLE_BORDER_CELLS, quizcomp.parser.style.DEFAULT_TABLE_BORDER_CELLS)):
            cell_style['border'] = HTML_BORDER_SPEC

        _join_html_style(token, [': '.join(item) for item in cell_style.items()])

def _join_html_style(token: markdown_it.token.Token, rules: typing.List[str]) -> None:
    """
    Take all style rules to apply, add in any existing style, and set the style attribute.
    """

    if (len(rules) == 0):
        return

    existing_style = token.attrGet('style')
    if (existing_style is not None):
        rules = [str(existing_style)] + rules

    style_string = '; '.join(rules)
    token.attrSet('style', style_string)

def get_renderer(options: markdown_it.utils.OptionsDict) -> QuizComposerRendererHTML:
    """ Get this renderer and options. """

    return QuizComposerRendererHTML()
