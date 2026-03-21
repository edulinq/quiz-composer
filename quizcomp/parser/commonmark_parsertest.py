import os
import typing

import edq.util.json

import quizcomp.constants
import quizcomp.parser.public
import quizcomp.testing.base

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
TESTDATA_DIR: str = os.path.join(THIS_DIR, 'testdata')
COMMONMARK_TEST_DATA_PATH: str = os.path.join(TESTDATA_DIR, 'commonmark_test_cases.json.gz')

SKIP_COMMONMARK_TESTS: typing.Set[int] = {
    176,  # Has non-JSON HTML style.
}

class TestCommonMark(quizcomp.testing.base.BaseTest):
    """
    Test cases provided by CommonMark.
    """

def _add_commonmark_tests() -> None:
    """
    Add test cases that come directly from the CommonMark spec.
    We won't try to validate the output, we just want to make sure they parse and render cleanly.
    The main thing with these tests is ensuring that our custom rendering does not fail.
    """

    test_data = edq.util.json.load_path(COMMONMARK_TEST_DATA_PATH)

    for test_case in test_data:
        id = test_case['example']

        if (id in SKIP_COMMONMARK_TESTS):
            continue

        text = test_case['markdown']
        section = quizcomp.testing.base.clean_name_part(test_case['section'])

        for format in quizcomp.constants.PARSER_FORMATS:
            name = f"test_commonmark__{id:04d}__{section}__{format}"
            setattr(TestCommonMark, name, _get_commonmark_test(text, format))

def _get_commonmark_test(text: str, format: str) -> typing.Callable:
    """ Get a test method. """

    def __method(self: TestCommonMark) -> None:
        parsed_text = quizcomp.parser.public.parse_text(text)

        options = {
            # The examples use paths that we would try and encode.
            'force_raw_image_src': True,
        }
        parsed_text.document.to_format(format, **options)

    return __method

_add_commonmark_tests()
