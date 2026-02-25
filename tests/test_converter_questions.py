import os

import quizcomp.converter.convert
import tests.base

class ConverterQuestionsTest(tests.base.BaseTest):
    """
    Use each standard converter/format on each "good" quiz question.
    """

    # Cache questions (by path) that have already been parased.
    _question_cache = {}

    def _get_question(self, path):
        path = os.path.abspath(path)
        if (path in ConverterQuestionsTest._question_cache):
            return ConverterQuestionsTest._question_cache[path]

        question = quizcomp.question.base.Question.from_path(path)
        ConverterQuestionsTest._question_cache[path] = question

        return question

def _add_converter_tests():
    good_paths, _ = tests.base.discover_question_tests()

    for path in good_paths:
        base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

        for format_name in quizcomp.converter.convert.SUPPORTED_FORMATS:
            for key in [True, False]:
                    test_name = 'test_converter_question__%s__%s__key_%s' % (base_test_name, format_name, str(key))
                    setattr(ConverterQuestionsTest, test_name, _get_template_test(path, format_name, key))

def _get_template_test(path, format_name, key):
    def __method(self):
        constructor_args = {'answer_key': key}

        question = self._get_question(path)
        content = quizcomp.converter.convert.convert_question(question, format = format_name,
                constructor_args = constructor_args)

        self.assertTrue(len(content) > 10)

    return __method

_add_converter_tests()
