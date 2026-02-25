"""
This file standardizes how we write and read JSON files.
Specifically, we try to be flexible when reading (using JSON5),
and strict when writing (using vanilla JSON).
"""

import json

import json5

def load(file_obj, **kwargs):
    return json5.load(file_obj, **kwargs)

def loads(text, **kwargs):
    return json5.loads(text, **kwargs)

def load_path(path, **kwargs):
    try:
        with open(path, 'r') as file:
            return load(file, **kwargs)
    except Exception as ex:
        raise ValueError(f"Failed to read JSON file '{path}'.") from ex

def dump(data, file_obj, **kwargs):
    return json.dump(data, file_obj, **kwargs)

def dumps(data, **kwargs):
    return json.dumps(data, **kwargs)

def dump_path(data, path, **kwargs):
    with open(path, 'w') as file:
        dump(data, file, **kwargs)
