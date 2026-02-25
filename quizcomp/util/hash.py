import hashlib

ENCODING = 'utf-8'

def sha256(data):
    if (isinstance(data, str)):
        data = data.encode(ENCODING)

    return hashlib.sha256(data).hexdigest()
