import base64
import os

import quizcomp.parser.common

def handle_callback(callback, original_src, base_dir):
    if (callback is None):
        return original_src

    return callback(original_src, base_dir)

def encode_image(path):
    ext = os.path.splitext(path)[-1].lower()
    ext = ext.removeprefix('.')
    mime = f"image/{ext}"

    with open(path, 'rb') as file:
        data = file.read()

    content = base64.standard_b64encode(data)
    return mime, content.decode(quizcomp.parser.common.ENCODING)
