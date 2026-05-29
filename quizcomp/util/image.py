import os
import typing

import edq.util.dirent
import edq.util.encoding

def b64_encode(path: str) -> typing.Tuple[str, str]:
    """ Encode an image to Base64. """

    ext = os.path.splitext(path)[-1].lower()
    ext = ext.removeprefix('.')
    mime = f"image/{ext}"

    data = edq.util.dirent.read_file_bytes(path)
    content = edq.util.encoding.to_base64(data)

    return mime, content
