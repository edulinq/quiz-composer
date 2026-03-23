import html
import logging
import os
import shutil
import typing
import warnings

import bs4
import edq.util.dirent

import quizcomp.constants
import quizcomp.converter.template
import quizcomp.model.question
import quizcomp.quiz

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR: str = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-qti')

QUESTION_TYPE_MAP: typing.Dict[quizcomp.model.question.QuestionType, str] = {
    # Direct Mappings
    quizcomp.model.question.QuestionType.ESSAY: 'essay_question',
    quizcomp.model.question.QuestionType.FIMB: 'fill_in_multiple_blanks_question',
    quizcomp.model.question.QuestionType.MATCHING: 'matching_question',
    quizcomp.model.question.QuestionType.MA: 'multiple_answers_question',
    quizcomp.model.question.QuestionType.MCQ: 'multiple_choice_question',
    quizcomp.model.question.QuestionType.MDD: 'multiple_dropdowns_question',
    quizcomp.model.question.QuestionType.NUMERICAL: 'numerical_question',
    quizcomp.model.question.QuestionType.TEXT_ONLY: 'text_only_question',
    quizcomp.model.question.QuestionType.TF: 'true_false_question',
    # Indirect Mappings
    quizcomp.model.question.QuestionType.FITB: 'short_answer_question',
    quizcomp.model.question.QuestionType.SA: 'essay_question',
}

TEMPLATE_FILENAME_ASSESSMENT_META: str = 'qti_assessment_meta.template'
TEMPLATE_FILENAME_MANIFEST: str = 'qti_imsmanifest.template'

OUT_DIR_IMAGES: str = 'images'
OUT_DIR_QUIZ: str = 'quiz'
OUT_FILENAME_QUIZ: str = 'quiz.xml'
OUT_FILENAME_ASSESSMENT_META: str = 'assessment_meta.xml'
OUT_FILENAME_MANIFEST: str = 'imsmanifest.xml'

DEFAULT_ID_DELIM: str = '.'
CANVAS_ID_DELIM: str = 'f'

class QTITemplateConverter(quizcomp.converter.template.TemplateConverter):
    """
    A converter to convert a quiz to QTI using templates.
    """

    def __init__(self,
            template_dir: str = DEFAULT_TEMPLATE_DIR,
            canvas: bool = False,
            **kwargs: typing.Any) -> None:
        parser_format_options = {}
        id_delim = DEFAULT_ID_DELIM

        if (canvas):
            parser_format_options = {
                'image_path_callback': self._store_images,
                'force_raw_image_src': True,
            }
            id_delim = CANVAS_ID_DELIM

        super().__init__(quizcomp.constants.FORMAT_HTML, template_dir,
                parser_format_options = parser_format_options,
                id_delim = id_delim,
                jinja_filters = {
                    'to_xml': _to_xml,
                },
                jinja_globals = {
                    'canvas': canvas,
                },
                **kwargs)

        self.canvas = canvas

    def convert_variant(self, variant: quizcomp.quiz.Variant, **kwargs: typing.Any) -> str:
        # Parse and format the XML.
        text = super().convert_variant(variant, **kwargs)
        return self._format_xml(text)

    def modify_question_context(self,
            context: typing.Dict[str, typing.Any],
            question: quizcomp.question.base.Question,
            variant: quizcomp.quiz.Variant) -> typing.Dict[str, typing.Any]:
        context['question']['mapped_question_type'] = QUESTION_TYPE_MAP[question.question_type]
        return context

    def convert_quiz(self, quiz: quizcomp.quiz.Quiz, out_path: typing.Union[str, None] = None, **kwargs: typing.Any) -> str:
        """ Convert an entire quiz (including variants) to QTI. """

        if (out_path is None):
            out_path = f'{quiz.title}.qti.zip'

        temp_base_dir = edq.util.dirent.get_temp_dir(prefix = 'quizcomp-qti-')

        temp_out_path = os.path.join(temp_base_dir, 'out.zip')
        temp_dir = os.path.join(temp_base_dir, quiz.title)

        quiz_dir = os.path.join(temp_dir, OUT_DIR_QUIZ)
        os.makedirs(quiz_dir, exist_ok = True)

        if (self.canvas):
            self.image_base_dir = os.path.join(temp_dir, OUT_DIR_IMAGES)
            os.makedirs(self.image_base_dir)

        path = os.path.join(quiz_dir, OUT_FILENAME_QUIZ)
        text = super().convert_quiz(quiz, **kwargs)
        edq.util.dirent.write_file(path, self._format_xml(text))

        self._convert_assessment_meta(quiz, quiz_dir)
        self._convert_manifest(quiz, temp_dir)

        self._create_zip(quiz, temp_out_path, out_path, temp_dir)

        logging.info("Created QTI quiz at '%s'.", out_path)
        return path

    def _create_zip(self, quiz: quizcomp.quiz.Quiz, temp_out_path: str, out_path: str, temp_dir: str) -> None:
        """ Zip up the pending QTI. """

        shutil.make_archive(os.path.splitext(temp_out_path)[0], 'zip', os.path.dirname(temp_dir), os.path.basename(temp_dir))
        edq.util.dirent.copy(temp_out_path, out_path)

    def _format_xml(self, text: str) -> str:
        """ Format/Prettify the XML. """

        warnings.filterwarnings('ignore', category = bs4.builder.XMLParsedAsHTMLWarning)  # type: ignore[attr-defined]
        document = bs4.BeautifulSoup(text, 'html.parser')
        return document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

    def _convert_assessment_meta(self, quiz: quizcomp.quiz.Quiz, out_dir: str) -> None:
        """ Write a quiz's metadata. """

        template = self.env.get_template(TEMPLATE_FILENAME_ASSESSMENT_META)

        quiz_context = quiz.to_dict()

        description_text = quiz.description.document.to_format(self.format)
        description_text = f"<p>{description_text}</p><br /><hr /><p>Version: {quiz.version}</p>"

        if (self.canvas):
            description_text = html.escape(description_text)

        quiz_context['description_text'] = description_text

        text = template.render(quiz = quiz_context)

        if (not self.canvas):
            # Canvas has some very strange and undocumented formatting requirements for the assessment meta file.
            # Do not format/pretty when working with Canvas.
            text = self._format_xml(text)

        path = os.path.join(out_dir, OUT_FILENAME_ASSESSMENT_META)
        edq.util.dirent.write_file(path, text)

    def _convert_manifest(self, quiz: quizcomp.quiz.Quiz, out_dir: str) -> None:
        """ Write the manifest for the quiz. """

        template = self.env.get_template(TEMPLATE_FILENAME_MANIFEST)

        data: typing.Dict[str, typing.Any] = {
            'quiz': quiz.to_dict(),
            'files': [],
        }

        for new_path in self.image_paths.values():
            data['files'].append({
                'type': 'image',
                'id': os.path.splitext(os.path.basename(new_path))[0],
                'raw_path': new_path,
                'path': '/'.join([quiz.title, OUT_DIR_IMAGES, os.path.basename(new_path)]),
                'filename': os.path.basename(new_path),
            })

        text = template.render(**data)
        text = self._format_xml(text)

        path = os.path.join(out_dir, OUT_FILENAME_MANIFEST)
        edq.util.dirent.write_file(path, text)

    def _store_images(self, link: str, base_dir: str) -> str:
        """
        Override the final path that is returned to instead point to the Canvas path.
        Note that this method should only be called when (self.canvas == True).
        """

        path = super()._store_images(link, base_dir)

        if (self.image_base_dir is None):
            raise ValueError("Missing image base dir.")

        quiz_name = os.path.basename(os.path.dirname(self.image_base_dir))
        filename = os.path.basename(path)

        return '/'.join(['$IMS-CC-FILEBASE$', quiz_name, OUT_DIR_IMAGES, filename])

def _to_xml(item: typing.Union[None, bool, typing.Any]) -> str:
    """
    Convert the item to an XML string.
    """

    if (item is None):
        return ''

    if (isinstance(item, bool)):
        return str(item).lower()

    return str(item)
