# TEST
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
import quizcomp.model.constants
import quizcomp.model.question
import quizcomp.model.quiz

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DEFAULT_TEMPLATE_DIR: str = os.path.join(THIS_DIR, '..', 'data', 'templates', 'edq-qti')

TEMPLATE_FILENAME_ASSESSMENT_META: str = 'qti_assessment_meta.template'
TEMPLATE_FILENAME_MANIFEST: str = 'qti_imsmanifest.template'

OUT_DIR_IMAGES: str = 'images'
OUT_DIR_QUIZ: str = 'quiz'
OUT_FILENAME_QUIZ: str = 'quiz.xml'
OUT_FILENAME_ASSESSMENT_META: str = 'assessment_meta.xml'
OUT_FILENAME_MANIFEST: str = 'imsmanifest.xml'

QUESTION_TYPE_MAP: typing.Dict[str, str] = {
    # Direct Mappings
    quizcomp.model.constants.QuestionType.ESSAY: 'essay_question',
    quizcomp.model.constants.QuestionType.FIMB: 'fill_in_multiple_blanks_question',
    quizcomp.model.constants.QuestionType.MATCHING: 'matching_question',
    quizcomp.model.constants.QuestionType.MA: 'multiple_answers_question',
    quizcomp.model.constants.QuestionType.MCQ: 'multiple_choice_question',
    quizcomp.model.constants.QuestionType.MDD: 'multiple_dropdowns_question',
    quizcomp.model.constants.QuestionType.NUMERICAL: 'numerical_question',
    quizcomp.model.constants.QuestionType.TEXT_ONLY: 'text_only_question',
    quizcomp.model.constants.QuestionType.TF: 'true_false_question',
    # Indirect Mappings
    quizcomp.model.constants.QuestionType.FITB: 'short_answer_question',
    quizcomp.model.constants.QuestionType.SA: 'essay_question',
}
""" QTI-specific question types. """

class QTITemplateConverter(quizcomp.converter.template.TemplateConverter):
    """
    A converter to convert a quiz to QTI using templates.
    """

    def __init__(self,
            out_path: typing.Union[str, None] = None,
            template_dir: str = DEFAULT_TEMPLATE_DIR,
            **kwargs: typing.Any) -> None:
        super().__init__(quizcomp.constants.FORMAT_HTML, template_dir,
                jinja_filters = {
                    'to_xml': _to_xml,
                },
                jinja_globals = {
                    'question_type_map': QUESTION_TYPE_MAP,
                },
                **kwargs)

        self.out_path: typing.Union[str, None] = out_path
        """ The path to write the quiz conversion output file to. """

    def finalize(self, quiz: quizcomp.model.quiz.Quiz, text: str) -> str:
        self._restore_image_sources(quiz)

        return _format_xml(text)

    def convert_quiz(self, quiz: quizcomp.model.quiz.Quiz, **kwargs: typing.Any) -> str:
        if (self.out_path is None):
            out_path = f'{quiz.get_name()}.qti.zip'
        else:
            out_path = self.out_path

        out_path = os.path.abspath(out_path)

        temp_base_dir = edq.util.dirent.get_temp_dir(prefix = 'quizcomp-qti-')

        temp_dir = os.path.join(temp_base_dir, quiz.get_name())

        images_dir = os.path.join(temp_dir, OUT_DIR_IMAGES)
        edq.util.dirent.mkdir(images_dir)
        self.image_base_dir = images_dir
        self._store_images(quiz)

        quiz_dir = os.path.join(temp_dir, OUT_DIR_QUIZ)
        edq.util.dirent.mkdir(quiz_dir)

        quiz_xml_path = os.path.join(quiz_dir, OUT_FILENAME_QUIZ)
        text = super().convert_quiz(quiz, **kwargs)
        edq.util.dirent.write_file(quiz_xml_path, text)

        self._convert_assessment_meta(quiz, quiz_dir)
        self._convert_manifest(quiz, temp_dir)

        shutil.make_archive(os.path.splitext(out_path)[0], 'zip', temp_base_dir, quiz.get_name())

        logging.info("Created QTI quiz at '%s'.", out_path)
        return out_path

    def _convert_assessment_meta(self, quiz: quizcomp.model.quiz.Quiz, out_dir: str) -> None:
        """ Write a quiz's metadata. """

        template = self.env.get_template(TEMPLATE_FILENAME_ASSESSMENT_META)

        context = {
            'quiz': quiz,
        }

        text = template.render(**context)
        text = _format_xml(text)

        path = os.path.join(out_dir, OUT_FILENAME_ASSESSMENT_META)
        edq.util.dirent.write_file(path, text)

    def _convert_manifest(self, quiz: quizcomp.model.quiz.Quiz, out_dir: str) -> None:
        """ Write the manifest for the quiz. """

        template = self.env.get_template(TEMPLATE_FILENAME_MANIFEST)

        files = []
        for filename in os.listdir(self.image_base_dir):
            files.append({
                'type': 'image',
                'id': os.path.splitext(filename)[0],
                'path': '/'.join([quiz.get_name(), OUT_DIR_IMAGES, filename]),
                'filename': filename,
            })

        context: typing.Dict[str, typing.Any] = {
            'quiz': quiz,
            'files': files,
        }

        text = template.render(**context)
        text = _format_xml(text)

        path = os.path.join(out_dir, OUT_FILENAME_MANIFEST)
        edq.util.dirent.write_file(path, text)

    ''' TEST
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
    '''

def _format_xml(text: str) -> str:
    """ Format/Prettify the XML. """

    warnings.filterwarnings('ignore', category = bs4.builder.XMLParsedAsHTMLWarning)  # type: ignore[attr-defined]
    document = bs4.BeautifulSoup(text, 'html.parser')
    return document.prettify(formatter = bs4.formatter.HTMLFormatter(indent = 4))

def _to_xml(item: typing.Union[None, bool, typing.Any]) -> str:
    """
    Convert the item to an XML string.
    """

    if (item is None):
        return ''

    if (isinstance(item, bool)):
        return str(item).lower()

    return str(item)
