import os
import shutil
import urllib.parse

import requests

def get(url, headers = {}, options = {}):
    response = requests.get(url, headers = headers, **options)
    response.raise_for_status()
    return response

def get_file(url, out_path, headers = {}):
    if (os.path.isdir(out_path)):
        parts = urllib.parse.urlsplit(url)
        filename = os.path.basename(parts.path)
        out_path = os.path.join(out_path, filename)

    response = get(url, headers = headers, options = {'stream': True})
    with open(out_path, 'wb') as file:
        shutil.copyfileobj(response.raw, file)

    return out_path
