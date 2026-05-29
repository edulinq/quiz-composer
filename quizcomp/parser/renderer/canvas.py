import re
import typing

import markdown_it.token

import quizcomp.model.constants
import quizcomp.parser.common
import quizcomp.parser.image
import quizcomp.parser.renderer.html

class QuizComposerRendererCanvas(quizcomp.parser.renderer.html.QuizComposerRendererHTML):  # pylint: disable=abstract-method
    """
    Render to Canvas-specific HTML.
    Canvas generally uses HTML, but has some special cases.
    """

    __output__ = quizcomp.model.constants.Format.CANVAS.value

    def placeholder(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            **kwargs: typing.Any) -> str:
        # Canvas placeholders cannot have spaces.
        text = tokens[token_index].content.strip()
        text = re.sub(r'\s+', ' ', text)
        text = text.replace(' ', '_')

        return f"[{text}]"

    def image(self,  # type: ignore[override] # pylint: disable=arguments-differ
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: markdown_it.utils.OptionsDict,
            env: typing.Dict[str, typing.Any],
            **kwargs: typing.Any) -> str:
        # Canvas requires files to be uploaded instead of embedded.
        # Those files should have already been uploaded and available.

        context = typing.cast(quizcomp.parser.common.RenderContext, env[quizcomp.parser.common.ENV_KEY_CONTEXT])

        force_raw_image_src = True
        process_token: typing.Union[quizcomp.parser.renderer.html.ProcessImageTokenFunction, None] = _process_image_token

        # If there is no canvas instance, we are probably just parsing and not uploading.
        if ((context.canvas_instance is None) or context.canvas_instance.testing):
            force_raw_image_src = False
            process_token = None

        return super().image(
            tokens, token_index, options, env,
            force_raw_image_src = force_raw_image_src,
            process_token = process_token,
        )

def _process_image_token(
        token: markdown_it.token.Token,
        context: quizcomp.parser.common.RenderContext,
        path: str,
        ) -> markdown_it.token.Token:
    """
    Process an image token for Canvas usage.
    This will rewrite the image's src/link.
    """

    if (context.canvas_instance is None):
        raise ValueError('Could not get canvas context.')

    file_id = context.canvas_instance.context.get('file_ids', {}).get(path)
    if (file_id is None):
        raise ValueError(f"Could not get canvas context file id of image '{path}'.")

    token.attrSet('src', f"{context.canvas_instance.base_url}/courses/{context.canvas_instance.course_id}/files/{file_id}/preview")
    return token

def get_renderer(options: markdown_it.utils.OptionsDict) -> QuizComposerRendererCanvas:
    """ Get this renderer and options. """

    return QuizComposerRendererCanvas()
