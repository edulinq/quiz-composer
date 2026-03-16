import re
import typing

import markdown_it.token

import quizcomp.constants
import quizcomp.parser.common
import quizcomp.parser.image
import quizcomp.parser.renderer.html

class QuizComposerRendererCanvas(quizcomp.parser.renderer.html.QuizComposerRendererHTML):
    """
    Render to Canvas-specific HTML.
    Canvas generally uses HTML, but has some special cases.
    """

    __output__ = quizcomp.constants.FORMAT_CANVAS

    def placeholder(self,
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: typing.Dict[str, typing.Any],
            env: typing.Dict[str, typing.Any],
            **kwargs: typing.Any) -> str:
        # Canvas placeholders cannot have spaces.
        text = tokens[token_index].content.strip()
        text = re.sub(r'\s+', ' ', text)
        text = text.replace(' ', '_')

        return "[%s]" % (text)

    def image(self,  # type: ignore[override]
            tokens: typing.List[markdown_it.token.Token],
            token_index: int,
            options: typing.Dict[str, typing.Any],
            env: typing.Dict[str, typing.Any],
            **kwargs: typing.Any) -> str:
        # Canvas requires files to be uploaded instead of embedded.
        # Those files should have already been uploaded and available.

        context = env.get(quizcomp.parser.common.CONTEXT_ENV_KEY, {})

        force_raw_image_src = True
        process_token: typing.Union[quizcomp.parser.renderer.html.ProcessImageTokenFunction, None] = _process_image_token

        # If there is no canvas instance, we are probably just parsing and not uploading.
        canvas_instance = context.get('canvas_instance', None)
        if (canvas_instance is None):
            force_raw_image_src = False
            process_token = None

        return super().image(tokens, token_index, options, env,
                force_raw_image_src = force_raw_image_src,
                process_token = process_token)

def _process_image_token(token: markdown_it.token.Token, context: typing.Dict[str, typing.Any], path: str) -> markdown_it.token.Token:
    """
    Process an image token for Canvas usage.
    This will rewrite the image's src/link.
    """

    canvas_instance = context.get('canvas_instance', None)
    if (canvas_instance is None):
        raise ValueError('Could not get canvas context.')

    file_id = canvas_instance.context.get('file_ids', {}).get(path)
    if (file_id is None):
        raise ValueError(f"Could not get canvas context file id of image '{path}'.")

    token.attrSet('src', f"{canvas_instance.base_url}/courses/{canvas_instance.course_id}/files/{file_id}/preview")
    return token

def get_renderer(options: typing.Dict[str, typing.Any]) -> typing.Tuple[QuizComposerRendererCanvas, typing.Dict[str, typing.Any]]:
    """ Get this renderer and options. """

    return QuizComposerRendererCanvas(), options
