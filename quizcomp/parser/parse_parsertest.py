import glob
import os
import re
import typing

import edq.testing.unittest
import edq.util.json

import quizcomp.constants
import quizcomp.parser.common
import quizcomp.parser.public

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TESTDATA_DIR: str = os.path.join(THIS_DIR, 'testdata')
DOCUMENTS_DIR = os.path.join(TESTDATA_DIR, 'documents')
GOOD_DOCUMENTS_DIR = os.path.join(DOCUMENTS_DIR, "good")
BAD_DOCUMENTS_DIR = os.path.join(DOCUMENTS_DIR, "bad")

class TestParser(edq.testing.unittest.BaseTest):
    """
    Test parsing text.
    Good and bad situations will be loaded from files into individual test methods.
    """

def _add_good_parse_questions():
    """ Add test cases for parsing valid documents. """

    paths = sorted(glob.glob(os.path.join(GOOD_DOCUMENTS_DIR, "**", "*.json"), recursive = True))
    for path in paths:
        test_cases = edq.util.json.load_path(path)
        base_dir = os.path.dirname(path)

        for test_case in test_cases:
            name = test_case['name']
            text = test_case['text']

            for (doc_format, expected) in test_case['formats'].items():
                test_name = _make_name('good_parse', path, name, doc_format)
                options = test_case.get('options', {}).get(doc_format, {})
                context = test_case.get('context', {})
                setattr(TestParser, test_name, _get_good_parse_test(text, doc_format, expected, base_dir, options, context))

def _get_good_parse_test(
        text: str,
        doc_format: str,
        base_expected: typing.Union[str, typing.List[typing.Dict[str, typing.Any]], typing.Dict[str, typing.Any]],
        base_dir: str,
        options: typing.Union[str, typing.Any],
        context: typing.Union[str, typing.Any],
        ) -> typing.Callable:
    """ Get a test method for a valid document. """

    def __method(self):
        document = quizcomp.parser.public.parse_text(text).document
        result = document.to_format(doc_format, base_dir = base_dir, include_metadata = False, **context)

        if (doc_format == quizcomp.constants.FORMAT_JSON):
            result = edq.util.json.loads(result)
            expected = {
                'type': 'document',
                'ast': {
                    'type': 'root',
                },
            }

            expected_children = []
            if (len(base_expected) > 0):
                if (isinstance(base_expected, list)):
                    expected_children += base_expected
                elif (isinstance(base_expected, dict)):
                    expected_children.append(base_expected)
                else:
                    raise ValueError("Unkown type for expected children: '%s'.", type(base_expected))

            if (len(expected_children) > 0):
                # If the first node is not the root block, then automatically insert it.
                if (not expected_children[0].get(quizcomp.parser.common.TOKEN_META_KEY_ROOT, False)):
                    expected_children = [{
                        'type': 'container_block',
                        quizcomp.parser.common.TOKEN_META_KEY_ROOT: True,
                        'children': expected_children,
                    }]

                expected['ast']['children'] = expected_children

            self.assertJSONDictEqual(expected, result)
        elif (doc_format in {quizcomp.constants.FORMAT_CANVAS, quizcomp.constants.FORMAT_HTML}):
            # If the HTML does not have a root block, then add one.
            raw_expected = base_expected
            if (options.get('strip', True)):
                raw_expected = raw_expected.strip()

            if ((raw_expected != '') and ('qg-root-block' not in raw_expected)):
                raw_expected = '<div class="qg-root-block qg-block">' + raw_expected + '</div>'

            expected = quizcomp.parser.render.clean_html(raw_expected, pretty = options.get('pretty', True))
            result = quizcomp.parser.render.clean_html(result, pretty = options.get('pretty', True))

            expected, result = _apply_text_options(options, expected, result)
            self.assertEqual(expected, result)
        else:
            expected = base_expected.strip()
            result = result.strip()

            expected, result = _apply_text_options(options, expected, result)
            self.assertEqual(expected, result)

    return __method

def _add_bad_parse_questions():
    """ Add test cases for parsing invalid documents. """

    paths = sorted(glob.glob(os.path.join(BAD_DOCUMENTS_DIR, "**", "*.json"), recursive = True))
    for path in paths:
        test_cases = edq.util.json.load_path(path)
        base_dir = os.path.dirname(path)

        for test_case in test_cases:
            name = test_case['name']
            text = test_case['text']
            options = test_case.get('options', {})

            test_name = _make_name('bad_parse', path, name)
            setattr(TestParser, test_name, _get_bad_parse_test(text, base_dir, options))

def _get_bad_parse_test(text: str, base_dir: str, options: typing.Union[str, typing.Any]) -> typing.Callable:
    """ Get a test method for an invalid document. """

    def __method(self):
        try:
            quizcomp.parser.public.parse_text(text)
        except Exception:
            # Expected.
            return

        self.fail("Failed to raise an exception.")

    return __method

def _make_name(prefix: str, path: str, name: str, doc_format: typing.Union[str, None] = None) -> str:
    """ Create a name for a test case. """

    clean_name = _clean_name_part(name)

    filename = os.path.splitext(os.path.basename(path))[0]

    test_name = "test_%s__%s__%s" % (prefix, filename, clean_name)

    if (doc_format is not None):
        test_name += ('__' + doc_format)

    return test_name

def _clean_name_part(text: str) -> str:
    """ Clean a test name component. """

    clean_text = text.lower().strip().replace(' ', '_')
    clean_text = re.sub(r'\W+', '', clean_text)
    return clean_text

def _apply_text_options(options: typing.Dict[str, typing.Any], a: str, b: str) -> typing.Tuple[str, str]:
    """ Apply some custom text options. """

    if (options.get("ignore-whitespace", False)):
        a = re.sub(r'\s+', '', a)
        b = re.sub(r'\s+', '', b)

    return a, b

_add_bad_parse_questions()
_add_good_parse_questions()
