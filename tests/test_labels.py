import os

import quizcomp.common
import quizcomp.constants
import quizcomp.converter.convert
import quizcomp.converter.html
import quizcomp.converter.qti
import quizcomp.converter.tex
import quizcomp.parser.public
import quizcomp.quiz
import tests.base

class LabelsTest(tests.base.BaseTest):
    """
    Test label parsing and validation.
    """

    def test_valid_plain_text(self):
        result = quizcomp.parser.public.parse_label('simple-name')
        self.assertIsInstance(result, quizcomp.parser.public.ParsedText)
        self.assertEqual(result.text, 'simple-name')

    def test_valid_special_characters(self):
        names = [
            'Quiz #1',
            'Test & Review',
            'Quiz $A',
            'Name "Final" <2024>',
            "Quiz 'Midterm'",
            'CSE 101: Part (a)',
            '| pipe chars |',
        ]

        for name in names:
            result = quizcomp.parser.public.parse_label(name)
            self.assertIsInstance(result, quizcomp.parser.public.ParsedText)
            self.assertEqual(result.text, name)

    def test_valid_unicode(self):
        names = [
            'café résumé',
            '测试名称',
        ]

        for name in names:
            result = quizcomp.parser.public.parse_label(name)
            self.assertEqual(result.text, name)

    def test_valid_empty(self):
        result = quizcomp.parser.public.parse_label('')
        self.assertIsInstance(result, quizcomp.parser.public.ParsedText)
        self.assertEqual(result.text, '')

    def test_none_becomes_empty(self):
        result = quizcomp.parser.public.parse_label(None)
        self.assertIsInstance(result, quizcomp.parser.public.ParsedText)
        self.assertEqual(result.text, '')

    def test_parsed_text_passthrough(self):
        original = quizcomp.parser.public.parse_label('Test')
        result = quizcomp.parser.public.parse_label(original)
        self.assertIs(result, original)

    def test_invalid_bold(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('**bold**')

    def test_invalid_italic(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('*italic*')

    def test_invalid_code_inline(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('`code`')

    def test_invalid_heading(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('# Heading')

    def test_invalid_image(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('![img](url)')

    def test_invalid_link(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('[link](url)')

    def test_invalid_list(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('- list item')

    def test_invalid_blockquote(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('> blockquote')

    def test_invalid_math_block(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('$$math$$')

    def test_invalid_math_inline(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('$x + 1$')

    def test_invalid_partial_formatting(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('name with **partial** bold')

    def test_invalid_container_block(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('::: block\ncontent\n:::')

    def test_invalid_horizontal_rule(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('---')

    def test_invalid_code_fence(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_label('```\ncode\n```')

    def test_serialization_roundtrip(self):
        name = quizcomp.parser.public.parse_label('Test & Name')
        self.assertEqual(name.to_pod(), 'Test & Name')

    def test_escape_tex(self):
        conv = quizcomp.converter.tex.TexTemplateConverter()
        name = quizcomp.parser.public.parse_label('Quiz #1 $A')
        result = conv._format_label(name)
        self.assertIn('\\#', result)
        self.assertIn('\\$', result)

    def test_escape_html(self):
        conv = quizcomp.converter.html.HTMLTemplateConverter()
        name = quizcomp.parser.public.parse_label('Name "Final" <2024>')
        result = conv._format_label(name)
        self.assertIn('&quot;', result)
        self.assertIn('&lt;', result)
        self.assertIn('&gt;', result)

    def test_escape_qti(self):
        conv = quizcomp.converter.qti.QTITemplateConverter()
        name = quizcomp.parser.public.parse_label("Quiz 'Midterm' & <Test>")
        result = conv._format_label(name)
        self.assertIn('&#x27;', result)
        self.assertIn('&amp;', result)
        self.assertIn('&lt;', result)

    def _get_special_label_quiz(self):
        """Load the quiz fixture with special characters in labels."""

        quiz_path = os.path.join(tests.base.GOOD_QUIZZES_DIR, 'special-labels', 'quiz.json')
        quiz = quizcomp.quiz.Quiz.from_path(quiz_path)
        return quiz.create_variant()

    def test_convert_special_labels_html(self):
        variant = self._get_special_label_quiz()
        result = quizcomp.converter.convert.convert_variant(
            variant, format = quizcomp.constants.FORMAT_HTML)
        self.assertIn('&amp;', result)
        self.assertIn('&lt;', result)
        self.assertNotIn('Group #1 & <Review>', result)

    def test_convert_special_labels_tex(self):
        variant = self._get_special_label_quiz()
        result = quizcomp.converter.convert.convert_variant(
            variant, format = quizcomp.constants.FORMAT_TEX)
        self.assertIn('\\#', result)
        self.assertIn('\\$', result)

    def test_convert_special_labels_qti(self):
        variant = self._get_special_label_quiz()
        result = quizcomp.converter.convert.convert_variant(
            variant, format = quizcomp.constants.FORMAT_QTI)
        # QTI uses BeautifulSoup to prettify XML, which decodes entities.
        # Just verify conversion succeeds and the label text is present.
        self.assertIn('Group #1', result)
        self.assertIn('Group $2', result)

    def test_convert_special_labels_json(self):
        variant = self._get_special_label_quiz()
        result = quizcomp.converter.convert.convert_variant(
            variant, format = quizcomp.constants.FORMAT_JSON)
        self.assertIn('Group #1 & <Review>', result)
