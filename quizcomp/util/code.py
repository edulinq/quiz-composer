"""
Utilities for extracting and working with Python source code.
"""

import ast
import importlib.util
import os
import sys
import types
import uuid

import edq.util.dirent

import quizcomp.util.json

ALLOWED_EXTENSIONS = ['.py', '.ipynb']
AST_NODE_WHITELIST = [ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef]

# TODO(eriq): Code from a python file should be cleaned using an AST as well.
def extract_code(path):
    """
    Gets the source code out of a path (to either a notebook or vanilla python).
    """

    code = None

    if (path.endswith('.ipynb')):
        code = extract_notebook_code(path)
    elif (path.endswith('.py')):
        with open(path, 'r') as file:
            lines = file.readlines()
        lines = [line.rstrip() for line in lines]

        code = "\n".join(lines) + "\n"
    else:
        raise ValueError("Unknown extension for extracting code: '%s'." % (path))

    return code.strip()

def extract_notebook_code(path):
    """
    Extract all the code cells from an iPython notebook.
    A concatenation of all the cells (with a newline between each cell) will be output.
    """

    with open(path, 'r') as file:
        notebook = quizcomp.util.json.load(file)

    contents = []

    for cell in notebook['cells']:
        if (cell['cell_type'] != 'code'):
            continue

        cell_code = ''.join(cell['source']).strip()

        # Ignore empty cells.
        if (cell_code == ''):
            continue

        contents.append(cell_code)

    return "\n".join(contents) + "\n"

def import_path(path, module_name = None):
    if (module_name is None):
        module_name = str(uuid.uuid4()).replace('-', '')

    # If it's a notebook, extract the code first and put it in a temp file.
    if (path.endswith('.ipynb')):
        source_code = extract_code(path)
        path = edq.util.dirent.get_temp_path(suffix = '.py')
        with open(path, 'w') as file:
            file.write(source_code)

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def sanitize_and_import_path(path, syspath = None, **kwargs):
    """
    Get the code from a source file, sanitize it, exec it, and return it as a namespace (module).
    Sanitization in this context means removing things that are not
    imports, functions, constants, and classes.
    A "constant" will be considered an assignment where the LHS is a single variable all in caps.
    """

    if (syspath is None):
        syspath = os.path.dirname(os.path.abspath(path))

    source_code = extract_code(path)

    return sanitize_and_import_code(source_code, path, syspath = syspath, **kwargs)

def sanitize_and_import_code(source_code, path, as_dict = False, syspath = None):
    """
    See sanitize_and_import_path().
    """

    if (syspath is None):
        syspath = os.path.dirname(os.path.abspath(os.getcwd()))

    module_ast = sanitize_code(source_code)

    globals_defs = {}

    try:
        sys.path.append(syspath)
        exec(compile(module_ast, filename = path, mode = "exec"), globals_defs)
    finally:
        sys.path.pop()

    if (as_dict):
        return globals_defs

    return types.SimpleNamespace(**globals_defs)

def sanitize_code(source_code):
    module_ast = ast.parse(source_code)

    keep_nodes = []
    for node in module_ast.body:
        if (type(node) in AST_NODE_WHITELIST):
            keep_nodes.append(node)
            continue

        if (not isinstance(node, ast.Assign)):
            continue

        if ((len(node.targets) != 1) or (not isinstance(node.targets[0], ast.Name))):
            continue

        if (node.targets[0].id != node.targets[0].id.upper()):
            continue

        keep_nodes.append(node)

    module_ast.body = keep_nodes
    return module_ast

def ast_to_source(module_ast):
    """
    Get code from an AST.
    Note that this function requires Python 3.9 (greater than our declared Python version,
    and should not be used in any core functionality.
    """

    return ast.unparse(module_ast)
