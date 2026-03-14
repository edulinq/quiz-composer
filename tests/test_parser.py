import os
import re

import edq.util.json

import quizcomp.constants
import quizcomp.parser.common
import quizcomp.parser.public
import tests.base

SKIP_COMMONMARK_TESTS = {
    176,  # Has non-JSON HTML style.
}

class TestParser(tests.base.BaseTest):
    """
    Test parsing.
    Good and bad situations will be loaded below into individual test cases.
    """

    pass

def _add_good_parse_questions():
    for path in tests.base.discover_good_document_files():
        with open(path, 'r') as file:
            documents = edq.util.json.load(file)

        base_dir = os.path.dirname(path)

        for document in documents:
            name = document['name']
            text = document['text']

            for (doc_format, expected) in document['formats'].items():
                test_name = _make_name('good_parse', path, name, doc_format)
                options = document.get('options', {}).get(doc_format, {})
                context = document.get('context', {})
                setattr(TestParser, test_name, _get_good_parse_test(text, doc_format, expected, base_dir, options, context))

def _get_good_parse_test(text, doc_format, base_expected, base_dir, options, context):
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
            self.assertLongStringEqual(expected, result)
        else:
            expected = base_expected.strip()
            result = result.strip()

            expected, result = _apply_text_options(options, expected, result)
            self.assertEqual(expected, result)

    return __method

def _add_bad_parse_questions():
    for path in tests.base.discover_bad_document_files():
        with open(path, 'r') as file:
            documents = edq.util.json.load(file)

        base_dir = os.path.dirname(path)

        for document in documents:
            name = document['name']
            text = document['text']
            options = document.get('options', {})

            test_name = _make_name('bad_parse', path, name)
            setattr(TestParser, test_name, _get_bad_parse_test(text, base_dir, options))

def _get_bad_parse_test(text, base_dir, options):
    def __method(self):
        try:
            quizcomp.parser.public.parse_text(text)
        except Exception:
            # Expected.
            return

        self.fail("Failed to raise an exception.")

    return __method

def _add_commonmark_tests():
    """
    Add test cases that come directly from the CommonMark spec.
    We won't try to validate the output, we just want to make sure they parse and render cleanly.
    The main thing with these tests is ensuring that our custom rendering does not fail.
    """

    with open(tests.base.COMMONMARK_TEST_DATA_PATH, 'r') as file:
        test_data = edq.util.json.load(file)

    for test_case in test_data:
        id = test_case['example']

        if (id in SKIP_COMMONMARK_TESTS):
            continue

        text = test_case['markdown']
        section = _clean_name_part(test_case['section'])

        for format in quizcomp.constants.PARSER_FORMATS:
            name = "test_commonmark__%04d__%s__%s" % (id, section, format)
            setattr(TestParser, name, _get_commonmark_test(text, format))

def _get_commonmark_test(text, format):
    def __method(self):
        parsed_text = quizcomp.parser.public.parse_text(text)

        options = {
            # The examples use paths that we would try and encode.
            'force_raw_image_src': True,
        }
        parsed_text.document.to_format(format, **options)

    return __method

def _make_name(prefix, path, name, doc_format = None):
    clean_name = _clean_name_part(name)

    filename = os.path.splitext(os.path.basename(path))[0]

    test_name = "test_%s__%s__%s" % (prefix, filename, clean_name)

    if (doc_format is not None):
        test_name += ('__' + doc_format)

    return test_name

def _clean_name_part(text):
    clean_text = text.lower().strip().replace(' ', '_')
    clean_text = re.sub(r'\W+', '', clean_text)
    return clean_text

def _apply_text_options(options, a, b):
    if (options.get("ignore-whitespace", False)):
        a = re.sub(r'\s+', '', a)
        b = re.sub(r'\s+', '', b)

    return a, b

_add_bad_parse_questions()
_add_good_parse_questions()
_add_commonmark_tests()
