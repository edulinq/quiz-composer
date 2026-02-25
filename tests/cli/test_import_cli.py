import glob
import os
import unittest

import quizcomp.util.code

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
ROOT_DIR = os.path.join(THIS_DIR, "..", "..")
CLI_DIRS = [
    os.path.join(ROOT_DIR, "quizcomp", "cli"),
]

SKIP_BASENNAMES = ['__init__', '__main__']

class CLIImportTest(unittest.TestCase):
    """
    Trivially test all the CLI executables by importing them.
    """

    pass

def _discover_cli_tests():
    for base_dir in CLI_DIRS:
        for path in sorted(glob.glob(os.path.join(base_dir, "**", "*.py"), recursive = True)):
            try:
                _add_cli_test(base_dir, path)
            except Exception as ex:
                raise ValueError("Failed to parse test case '%s'." % (path)) from ex

def _add_cli_test(base_dir, path):
    basename = os.path.splitext(os.path.basename(path))[0]
    if (basename in SKIP_BASENNAMES):
        return

    relpath = os.path.relpath(path, base_dir)
    test_basename = '.'.join(os.path.splitext(relpath)[0].split('/'))

    test_name = 'test_cli_import__%s' % (test_basename)

    cli_module = quizcomp.util.code.import_path(path)
    if ('_get_parser' not in dir(cli_module)):
        return

    setattr(CLIImportTest, test_name, _get_cli_test_method(path))

def _get_cli_test_method(path):
    def __method(self):
        quizcomp.util.code.import_path(path)

    return __method

_discover_cli_tests()
