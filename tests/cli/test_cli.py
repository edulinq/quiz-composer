import contextlib
import glob
import importlib
import io
import json
import os
import re
import sys

import tests.base
import quizcomp.util.dirent
import quizcomp.util.json

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TEST_CASES_DIR = os.path.join(THIS_DIR, "test_cases")
DATA_DIR = os.path.join(THIS_DIR, "data")

TEST_CASE_SEP = '---'
DATA_DIR_ID = '__DATA_DIR__'
TEMP_DIR_ID = '__TEMP_DIR__'
ESCAPE_JSON_STRING_ID = '__ESCAPE_JSON_STRING__'

DEFAULT_OUTPUT_CHECK = 'content_equals'

class CLITest(tests.base.BaseTest):
    """
    Test CLI tools.
    """

    _base_temp_dir = None

    @classmethod
    def setUpClass(cls):
        CLITest._base_temp_dir = quizcomp.util.dirent.get_temp_path('quizcomp_CLITest_')

    def _get_test_info(self, test_name, path):
        options, expected_output = _read_test_file(path)

        temp_dir = os.path.join(CLITest._base_temp_dir, test_name)

        module_name = options['cli']
        exit_status = options.get('exit_status', 0)
        is_error = options.get('error', False)

        output_check_name = options.get('output-check', DEFAULT_OUTPUT_CHECK)
        if (output_check_name not in globals()):
            raise ValueError("Could not find output check function: '%s'." % (output_check_name))
        output_check = globals()[output_check_name]

        if (is_error):
            expected_output = expected_output.strip()

        arguments = self.get_base_arguments()
        for key, value in options.get('overrides', {}).items():
            arguments[key] = value

        cli_arguments = []

        for key, value in arguments.items():
            cli_arguments += ["--%s" % (str(key)), str(value)]

        cli_arguments += options.get('arguments', [])

        # Make any substitutions.
        expected_output = _prepare_string(expected_output, temp_dir)
        for i in range(len(cli_arguments)):
            cli_arguments[i] = _prepare_string(cli_arguments[i], temp_dir)

        return module_name, cli_arguments, expected_output, output_check, exit_status, is_error

    def get_base_arguments(self):
        return {}

def _prepare_string(text, temp_dir):
    replacements = [
        (DATA_DIR_ID, DATA_DIR),
        (TEMP_DIR_ID, temp_dir),
    ]

    for (key, base_dir) in replacements:
        text = _replace_path(text, key, base_dir)

    # Check for any escape requests.
    text = _process_escapes(text)

    return text

def _replace_path(text, key, base_dir):
    match = re.search(r'%s\(([^)]*)\)' % (key), text)
    if (match is None):
        return text

    filename = match.group(1)

    # Normalize any path seperators.
    filename = os.path.join(*filename.split('/'))

    if (filename == ''):
        path = base_dir
    else:
        path = os.path.join(base_dir, filename)

    text = text.replace(match.group(0), path)

    return text

def _process_escapes(text):
    while True:
        match = re.search(r'%s\(([^)]*)\)' % (ESCAPE_JSON_STRING_ID), text)
        if (match is None):
            return text

        inner_text = match.group(1)

        # Encode as JSON.
        inner_text = json.dumps(inner_text)

        # Remove quotes.
        inner_text = inner_text[1:-1]

        text = text.replace(match.group(0), inner_text)

def _read_test_file(path):
    json_lines = []
    output_lines = []

    with open(path, 'r') as file:
        accumulator = json_lines
        for line in file:
            if (line.strip() == TEST_CASE_SEP):
                accumulator = output_lines
                continue

            accumulator.append(line)

    options = quizcomp.util.json.loads(''.join(json_lines))
    output = ''.join(output_lines)

    return options, output

def _discover_test_cases():
    for path in sorted(glob.glob(os.path.join(TEST_CASES_DIR, "**", "*.txt"), recursive = True)):
        try:
            _add_test_case(path)
        except Exception as ex:
            raise ValueError("Failed to parse test case '%s'." % (path)) from ex

def _add_test_case(path):
    test_name = 'test_cli__' + os.path.splitext(os.path.basename(path))[0]
    setattr(CLITest, test_name, _get_test_method(test_name, path))

def _get_test_method(test_name, path):
    def __method(self):
        module_name, cli_arguments, expected_output, output_check, expected_exit_status, is_error = self._get_test_info(test_name, path)
        module = importlib.import_module(module_name)

        old_args = sys.argv
        sys.argv = [module.__file__] + cli_arguments

        try:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                actual_exit_status = module.main()
            actual_output = output.getvalue()

            if (is_error):
                self.fail("No error was not raised when one was expected ('%s')." % (str(expected_output)))
        except BaseException as ex:
            if (not is_error):
                raise ex

            if (isinstance(ex, SystemExit)):
                if (ex.__context__ is None):
                    self.fail("Unexpected exit without context.")

                ex = ex.__context__

            output_check(self, expected_output, str(ex))
            return
        finally:
            sys.argv = old_args

        self.assertEqual(expected_exit_status, actual_exit_status)

        output_check(self, expected_output, actual_output)

    return __method

def content_equals(test_case, expected, actual, **kwargs):
    test_case.assertEqual(expected, actual)

def content_equals_choices(test_case, expected, actual, **kwargs):
    """
    Deal with a 3.12.8 update in argparse that quotes choices.
    """

    expected = _remove_choices_quotes(expected)
    actual = _remove_choices_quotes(actual)

    test_case.assertEqual(expected, actual)

def _remove_choices_quotes(text):
    matches = re.findall(r"\(choose from '[^)]+'\)", text)
    for match in matches:
        text = text.replace(match, match.replace("'", ''))

    return text

def has_content_100(test_case, expected, actual, **kwargs):
    return has_content(test_case, expected, actual, min_length = 100)

# Ensure that the output has content.
def has_content(test_case, expected, actual, min_length = 100):
    message = "Output does not meet minimum length of %d, it is only %d." % (min_length, len(actual))
    test_case.assertTrue((len(actual) >= min_length), msg = message)

_discover_test_cases()
