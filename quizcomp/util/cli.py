"""
Look in a package for CLI tools and list their information.
A package looks like a CLI package if it has a __main__.py file.
A module looks like a CLI tool if it either
has a _get_parser() method that returns an argparse parser,
or has a _modify_parser() method that takes a copy of the default (passed in)
argparse parser.
"""

import argparse
import copy
import importlib.util
import inspect
import os
import uuid

def main():
    """
    Run as if this process has been called as a executable.
    This will parse the command line and list the caller's dir.
    """

    args = _get_parser().parse_args()
    auto_list(recursive = args.recursive, skip_dirs = args.skip_dirs, callers_stack_index = 2)
    return 0

def add_out_arg(parser, default_filename,
        name = 'out', dest = 'out', default = '.'):
    """
    Add a standard output path argument to an argparse parser.
    """

    parser.add_argument(f'--{name}', dest = dest,
        action = 'store', type = str, default = default,
        help = ('The path specifying where to put the output.'
                + f' If the path points to an existing dir, the result will be written to `<{name}>/{default_filename}`.'
                + ' If the path point to an existing file, the file will be overwritten with the result.'
                + ' If the path points to a non-existing dir (denoted with a trailing path separator (e.g., slash)), the dir will be created and the output will be written as it is to an existing dir.'
                + ' Finally if the path does not exist, the result will be written to the full path (creating any parent directories along the way).'
                + ' (default: %(default)s).'))

def resolve_out_arg(raw_path, default_filename):
    """
    Resolve the out argument with the semantics of add_out_arg(),
    and return a resolved normalized path.
    """

    path = os.path.abspath(raw_path)

    if (os.path.isfile(path)):
        return path
    elif (os.path.isdir(path)):
        return os.path.join(path, default_filename)
    elif (raw_path.endswith(os.sep)):
        os.makedirs(path, exist_ok = True)
        return os.path.join(path, default_filename)
    else:
        os.makedirs(os.path.dirname(path), exist_ok = True)
        return path

def auto_list(recursive = False, skip_dirs = False,
        default_parser = None, callers_stack_index = 1):
    """
    Will print the caller's prompt and call _list_dir() on it,
    but will figure out the package's prompt (doc string), base_dir,
    and command_prefix automatically.
    This will use the inspect library, so only use in places that use code normally.
    """

    try:
        frameInfo = inspect.stack()[callers_stack_index]

        path = frameInfo.filename
        base_dir = os.path.dirname(path)

        module = inspect.getmodule(frameInfo.frame)
        package = module.__package__
    except Exception as ex:
        raise ValueError("Unable to get caller information for listing CLI information.") from ex

    if (default_parser is None):
        default_parser = argparse.ArgumentParser()

    print(module.__doc__.strip())
    _list_dir(base_dir, package, default_parser, recursive, skip_dirs)

def _list_dir(base_dir, command_prefix, default_parser, recursive, skip_dirs):
    for dirent in sorted(os.listdir(base_dir)):
        path = os.path.join(base_dir, dirent)
        cmd = command_prefix + '.' + os.path.splitext(dirent)[0]

        if (dirent.startswith('__')):
            continue

        if (os.path.isfile(path)):
            _handle_file(path, cmd, default_parser)
        else:
            if (not skip_dirs):
                _handle_dir(path, cmd)

            if (recursive):
                _list_dir(path, cmd, default_parser, recursive, skip_dirs)

def _handle_file(path, cmd, default_parser):
    if (not path.endswith('.py')):
        return

    try:
        module = _import_path(path)
    except Exception:
        print("ERROR Importing: ", path)
        return

    parser = None
    if ('_get_parser' in dir(module)):
        parser = module._get_parser()
    elif ('_modify_parser' in dir(module)):
        parser = copy.deepcopy(default_parser)
        module._modify_parser(parser)
    else:
        return

    parser.prog = 'python3 -m ' + cmd

    print()
    print(cmd)
    print(parser.description)
    parser.print_usage()

def _handle_dir(path, cmd):
    try:
        module = _import_path(os.path.join(path, '__main__.py'))
    except Exception:
        return

    description = module.__doc__.strip()

    print()
    print(cmd + '.*')
    print(description)
    print("See `python3 -m %s` for more information." % (cmd))

def _import_path(path, module_name = None):
    if (module_name is None):
        module_name = str(uuid.uuid4()).replace('-', '')

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module

def _get_parser():
    parser = argparse.ArgumentParser(
        description = 'Show the tools available in this package.',
        epilog = ("Note that you don't need to provide a package as an argument,"
            + " since you already called this on the target package."))

    parser.add_argument('-r', '--recursive', dest = 'recursive',
        action = 'store_true', default = False,
        help = 'Recur into each package to look for tools and subpackages (default: %(default)s).')

    parser.add_argument('--skip-dirs', dest = 'skip_dirs',
        action = 'store_true', default = False,
        help = ('Do not output information about directories/packages,'
            + ' only tools (default: %(default)s).'))

    return parser
