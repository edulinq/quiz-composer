import re
import typing

import markdown_it.token

import quizcomp.model.constants
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

def get_renderer(options: markdown_it.utils.OptionsDict) -> QuizComposerRendererCanvas:
    """ Get this renderer and options. """

    return QuizComposerRendererCanvas()
