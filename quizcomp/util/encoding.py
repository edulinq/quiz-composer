import base64

DEFAULT_ENCODING = 'utf-8'

def to_base64(data, encoding = DEFAULT_ENCODING):
    if (isinstance(data, str)):
        data = data.encode(encoding)

    data = base64.standard_b64encode(data)
    return data.decode(encoding)

def from_base64(data, encoding = DEFAULT_ENCODING):
    return base64.b64decode(data.encode(encoding), validate = True)
