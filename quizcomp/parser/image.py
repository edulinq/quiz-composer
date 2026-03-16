import base64
import os
import typing

import edq.util.dirent
import edq.util.encoding

import quizcomp.parser.common

@typing.runtime_checkable
class ImageCallback(typing.Protocol):
    """
    A function that is called by the parser when it encounters an image.
    The result of this callback (if it is set) will replace the contents of the original src/link value.
    This can be useful for saving or encoding images.
    """

    def __call__(self, original: str, base_dir: str) -> str:
        """ Override the original src/link value for an image. """

        ...

def handle_callback(callback: typing.Union[ImageCallback, None], original: str, base_dir: str) -> str:
    """
    Get the value to use as the src/link for an image.
    If the callback exists, it will be used.
    """

    if (callback is None):
        return original

    return callback(original, base_dir)

def encode_image(path: str) -> typing.Tuple[str, str]:
    """ Encode an image to Base64. """

    ext = os.path.splitext(path)[-1].lower()
    ext = ext.removeprefix('.')
    mime = f"image/{ext}"

    data = edq.util.dirent.read_file_bytes(path)
    content = edq.util.encoding.to_base64(data)

    return mime, content
