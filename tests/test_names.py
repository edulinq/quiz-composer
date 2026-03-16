import quizcomp.common
import quizcomp.converter.html
import quizcomp.converter.qti
import quizcomp.converter.tex
import quizcomp.parser.public
import tests.base

class NamesTest(tests.base.BaseTest):
    """
    Test name parsing and validation.
    """

    def test_valid_plain_text(self):
        result = quizcomp.parser.public.parse_name('simple-name')
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
            result = quizcomp.parser.public.parse_name(name)
            self.assertIsInstance(result, quizcomp.parser.public.ParsedText)
            self.assertEqual(result.text, name)

    def test_valid_unicode(self):
        names = [
            'café résumé',
            '测试名称',
        ]

        for name in names:
            result = quizcomp.parser.public.parse_name(name)
            self.assertEqual(result.text, name)

    def test_valid_empty(self):
        result = quizcomp.parser.public.parse_name('')
        self.assertIsInstance(result, quizcomp.parser.public.ParsedText)
        self.assertEqual(result.text, '')

    def test_none_becomes_empty(self):
        result = quizcomp.parser.public.parse_name(None)
        self.assertIsInstance(result, quizcomp.parser.public.ParsedText)
        self.assertEqual(result.text, '')

    def test_parsed_text_passthrough(self):
        original = quizcomp.parser.public.parse_name('Test')
        result = quizcomp.parser.public.parse_name(original)
        self.assertIs(result, original)

    def test_invalid_bold(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('**bold**')

    def test_invalid_italic(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('*italic*')

    def test_invalid_code_inline(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('`code`')

    def test_invalid_heading(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('# Heading')

    def test_invalid_image(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('![img](url)')

    def test_invalid_link(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('[link](url)')

    def test_invalid_list(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('- list item')

    def test_invalid_blockquote(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('> blockquote')

    def test_invalid_math_block(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('$$math$$')

    def test_invalid_math_inline(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('$x + 1$')

    def test_invalid_partial_formatting(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('name with **partial** bold')

    def test_invalid_container_block(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('::: block\ncontent\n:::')

    def test_invalid_horizontal_rule(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('---')

    def test_invalid_code_fence(self):
        with self.assertRaises(quizcomp.common.QuizValidationError):
            quizcomp.parser.public.parse_name('```\ncode\n```')

    def test_serialization_roundtrip(self):
        name = quizcomp.parser.public.parse_name('Test & Name')
        self.assertEqual(name.to_pod(), 'Test & Name')

    def test_escape_tex(self):
        conv = quizcomp.converter.tex.TexTemplateConverter()
        name = quizcomp.parser.public.parse_name('Quiz #1 $A')
        result = conv._format_name(name)
        self.assertIn('\\#', result)
        self.assertIn('\\$', result)

    def test_escape_html(self):
        conv = quizcomp.converter.html.HTMLTemplateConverter()
        name = quizcomp.parser.public.parse_name('Name "Final" <2024>')
        result = conv._format_name(name)
        self.assertIn('&quot;', result)
        self.assertIn('&lt;', result)
        self.assertIn('&gt;', result)

    def test_escape_qti(self):
        conv = quizcomp.converter.qti.QTITemplateConverter()
        name = quizcomp.parser.public.parse_name("Quiz 'Midterm' & <Test>")
        result = conv._format_name(name)
        self.assertIn('&#x27;', result)
        self.assertIn('&amp;', result)
        self.assertIn('&lt;', result)
