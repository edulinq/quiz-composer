import math
import os
import random
import re
import string

import quizcomp.constants
import quizcomp.converter.converter
import quizcomp.parser.public
import quizcomp.quiz
import quizcomp.util.dirent
import quizcomp.util.http
import quizcomp.variant

import jinja2

TEMPLATE_FILENAME_QUIZ = 'quiz.template'
TEMPLATE_FILENAME_QUESTION_SEP = 'question-separator.template'
TEMPLATE_FILENAME_GROUP = 'group.template'

RIGHT_IDS = string.ascii_uppercase
LEFT_IDS = [str(i + 1) for i in range(len(RIGHT_IDS))]

DEFAULT_JINJA_OPTIONS = {
    'trim_blocks': True,
    'lstrip_blocks': True,
    'autoescape': jinja2.select_autoescape(),
}

DEFAULT_ID_DELIM = '.'

class TemplateConverter(quizcomp.converter.converter.Converter):
    def __init__(self, format, template_dir,
            jinja_options = {}, jinja_filters = {}, jinja_globals = {},
            parser_format_options = {},
            image_base_dir = None, image_relative_root = None, cleanup_images = True,
            id_delim = DEFAULT_ID_DELIM,
            **kwargs):
        super().__init__(**kwargs)

        if (not os.path.isdir(template_dir)):
            raise ValueError("Provided template dir ('%s') does not exist or is not a dir." % (
                template_dir))

        self.format = format
        self.template_dir = template_dir

        self.parser_format_options = parser_format_options
        self.id_delim = id_delim

        # Some converters will need to store image paths.
        # Using the _store_images() callback will put the images inside image_base_dir.
        self.image_base_dir = image_base_dir

        # This will hold: {<abs_path or link>: <new path (based on image_base_dir)>, ...}
        self.image_paths = {}

        # If not None, override the default image output path with os.join(image_relative_root, filename).
        self.image_relative_root = image_relative_root

        # Remove any temp image directories.
        self.cleanup_images = cleanup_images

        self.jinja_options = DEFAULT_JINJA_OPTIONS.copy()
        self.jinja_options.update(jinja_options)

        self.env = jinja2.Environment(
            loader = jinja2.FileSystemLoader(self.template_dir, followlinks = True),
            **self.jinja_options,
        )

        self.env.globals.update(jinja_globals)

        for (name, function) in jinja_filters.items():
            self.env.filters[name] = function

        # Methods to generate answers.
        # Signature: func(self, question_id, question_number, question, variant)
        self.answer_functions = {
            quizcomp.constants.QUESTION_TYPE_ESSAY: 'create_answers_essay',
            quizcomp.constants.QUESTION_TYPE_FIMB: 'create_answers_fimb',
            quizcomp.constants.QUESTION_TYPE_FITB: 'create_answers_fitb',
            quizcomp.constants.QUESTION_TYPE_MA: 'create_answers_ma',
            quizcomp.constants.QUESTION_TYPE_MATCHING: 'create_answers_matching',
            quizcomp.constants.QUESTION_TYPE_MCQ: 'create_answers_mcq',
            quizcomp.constants.QUESTION_TYPE_MDD: 'create_answers_mdd',
            quizcomp.constants.QUESTION_TYPE_NUMERICAL: 'create_answers_numerical',
            quizcomp.constants.QUESTION_TYPE_SA: 'create_answers_sa',
            quizcomp.constants.QUESTION_TYPE_TEXT_ONLY: 'create_answers_text_only',
            quizcomp.constants.QUESTION_TYPE_TF: 'create_answers_tf',
        }

    def convert_quiz(self, quiz, **kwargs):
        return self._convert_container(quiz, quizcomp.quiz.Quiz, 'quiz')

    def convert_variant(self, variant, **kwargs):
        return self._convert_container(variant, quizcomp.variant.Variant, 'variant')

    def _convert_container(self, container, container_type, container_label):
        if (not isinstance(container, container_type)):
            raise ValueError("Template %s converter requires a %s, found %s." % (
                    container_label, str(container_type), type(container)))

        _, inner_text = self.create_groups(container)

        inner_context = container.to_dict()
        inner_context['total_points'] = container.total_points()
        inner_context['description_text'] = self._format_doc(container.description.document)

        context = {
            'quiz': inner_context,
            'answer_key': self.answer_key,
            'inner_text': inner_text,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_QUIZ)
        text = template.render(**context)

        return text

    def create_groups(self, quiz):
        return self._create_item_collection(quiz, 'groups', 'group', 1, self.create_group)

    def _create_item_collection(self, container, container_attr, label, question_number, item_creation_function, id_prefix = None):
        """
        Create a collection of groups (for quizzes) or questions (for variants or inside groups)
        from a container (variant or quiz).
        """

        result = []
        items = getattr(container, container_attr)

        for index in range(len(items)):
            item = items[index]

            item_id = str(index)
            if (id_prefix is not None):
                item_id = self.id_delim.join([id_prefix, item_id])

            if (index != 0):
                result.append(self.create_question_separator(container))

            try:
                question_number, text = item_creation_function(item_id, question_number, item, container)
                result.append(text)
            except Exception as ex:
                raise ValueError("Failed to convert %s %d (%s: %s)." % (label, index, item_id, item.name)) from ex

        return question_number, "\n\n".join(result)

    def create_group(self, group_index, question_number, group, quiz):
        data = group.to_dict()
        data['id'] = group_index

        question_number, questions_text = self._create_item_collection(group, 'questions', 'question', question_number, self.create_question, id_prefix = group_index)

        context = {
            'quiz': quiz,
            'group': data,
            'questions_text': questions_text,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_GROUP)
        text = template.render(**context)

        return question_number, text

    def create_question(self, question_id, question_number, question, variant):
        question_type = question.question_type
        if (question_type not in self.answer_functions):
            raise ValueError("Unsupported question type: '%s'." % (question_type))

        data = question.to_dict()
        data['prompt_text'] = self._format_doc(question.prompt.document)
        data['id'] = question_id
        data['number'] = question_number

        # Stash the old answers and add in new ones.
        data['answers_raw'] = data['answers']
        answers_method = getattr(self, self.answer_functions[question_type])
        data['answers'] = answers_method(question_id, question_number, question, variant)

        data['feedback'] = {}
        for key, item in question.feedback.items():
            data['feedback'][key] = self._format_doc(item.document)

        context = {
            'quiz': variant,
            'answer_key': self.answer_key,
            'question': data,
        }

        template_name = "%s.template" % (question_type)
        template = self.env.get_template(template_name)

        context = self.modify_question_context(context, question, variant)
        text = template.render(**context)

        if (not question.should_skip_numbering()):
            question_number += 1

        return question_number, text

    def modify_question_context(self, context, question, variant):
        """
        Provide an opportunity for children to modify the question context.
        The new context reference (which may be new, unchanged, or modified version of the passed-in context).
        """

        return context

    def clean_solution_content(self, document):
        """
        An opportunity for children to clean the text of a solution before it is entered into a key.
        For example, tex solutions are hacky and cannot use certain functions.
        """

        return self._format_doc(document)

    def create_question_separator(self, variant):
        context = {
            'quiz': variant,
            'answer_key': self.answer_key,
        }

        template = self.env.get_template(TEMPLATE_FILENAME_QUESTION_SEP)
        text = template.render(**context)

        return text

    def create_answers_tf(self, question_id, question_number, question, variant):
        return question.answers

    def create_answers_matching(self, question_id, question_number, question, variant):
        lefts = []
        rights = []

        # {left_index: right_index, ...}
        matches = {}

        for items in question.answers['matches']:
            matches[len(lefts)] = len(rights)

            lefts.append({
                'initial_text': items['left'].text,
                'raw_text': self._format_doc(items['left'].document, doc_format = quizcomp.constants.FORMAT_TEXT),
                'text': self._format_doc(items['left'].document),
            })

            rights.append({
                'initial_text': items['right'].text,
                'raw_text': self._format_doc(items['right'].document, doc_format = quizcomp.constants.FORMAT_TEXT),
                'text': self._format_doc(items['right'].document),
            })

        for right in question.answers['distractors']:
            rights.append({
                'initial_text': right.text,
                'raw_text': self._format_doc(right.document, doc_format = quizcomp.constants.FORMAT_TEXT),
                'text': self._format_doc(right.document),
            })

        left_ids = self.get_matching_left_ids()
        right_ids = self.get_matching_right_ids()

        if (len(lefts) > len(left_ids)):
            raise ValueError("Too many left-hand values for a matching question. Found: %d, Max %d." % (len(lefts) > len(left_ids)))

        if (len(rights) > len(right_ids)):
            raise ValueError("Too many right-hand values for a matching question. Found: %d, Max %d." % (len(rights) > len(right_ids)))

        if (question.answers.get('shuffle', False)):
            seed = question.answers.get('shuffle_seed', None)
            rng = random.Random(seed)

            # Shuffle the left and right options while maintining the match mapping.
            left_indexes = list(range(len(lefts)))
            right_indexes = list(range(len(rights)))

            rng.shuffle(left_indexes)
            rng.shuffle(right_indexes)

            new_lefts = [lefts[index] for index in left_indexes]
            lefts = new_lefts

            new_rights = [rights[index] for index in right_indexes]
            rights = new_rights

            new_matches = {left_indexes.index(old_left_index): right_indexes.index(old_right_index) for (old_left_index, old_right_index) in matches.items()}
            matches = new_matches

        # Augment the left and rights with more information for the template.
        for left_index in range(len(lefts)):
            right_index = matches[left_index]

            lefts[left_index] = {
                'id': self.id_delim.join([question_id, left_ids[left_index]]),
                'text': lefts[left_index]['text'],
                'initial_text': lefts[left_index]['initial_text'],
                'raw_text': lefts[left_index]['raw_text'],
                'solution': right_ids[right_index],
                'solution_id': self.id_delim.join([question_id, right_ids[right_index]]),
                'index': left_index,
                'solution_index': right_index,
                'one_index': left_index + 1,
                'solution_one_index': right_index + 1,
            }

        for right_index in range(len(rights)):
            rights[right_index] = {
                'id': self.id_delim.join([question_id, right_ids[right_index]]),
                'text': rights[right_index]['text'],
                'initial_text': rights[right_index]['initial_text'],
                'raw_text': rights[right_index]['raw_text'],
                'label': right_ids[right_index],
                'index': right_index,
                'one_index': right_index + 1,
            }

        return {
            'lefts': lefts,
            'rights': rights,
            'matches': matches,
        }

    def get_matching_left_ids(self):
        return LEFT_IDS

    def get_matching_right_ids(self):
        return RIGHT_IDS

    def create_answers_mcq(self, question_id, question_number, question, variant):
        return self._create_answers_mcq_list(question.answers)

    def _create_answers_mcq_list(self, answers):
        choices = []

        for i in range(len(answers)):
            answer = answers[i]
            choice = self._create_answers_text_value(answer)
            choice['correct'] = answer.is_correct()

            choices.append(choice)

        return choices

    def create_answers_text_only(self, question_id, question_number, question, variant):
        return None

    def create_answers_numerical(self, question_id, question_number, question, variant):
        answer = question.answers[0]

        if (answer.type == quizcomp.constants.NUMERICAL_ANSWER_TYPE_EXACT):
            if (math.isclose(answer.margin, 0.0)):
                content = "%s" % (str(answer.value))
            else:
                content = "%s ± %f" % (str(answer.value), answer.margin)
        elif (answer.type == quizcomp.constants.NUMERICAL_ANSWER_TYPE_RANGE):
            content = "[%s, %s]" % (str(answer.min), str(answer.max))
        elif (answer.type == quizcomp.constants.NUMERICAL_ANSWER_TYPE_PRECISION):
            content = "%s (precision: %s)" % (str(answer.value), str(answer.precision))
        else:
            raise ValueError(f"Unknown numerical answer type: '{answer.type}'.")

        document = quizcomp.parser.public.parse_text(content).document

        return {
            'solution': self.clean_solution_content(document),
            'dirty_solution': self._format_doc(document),
            'raw_solution': self._format_doc(document, doc_format = quizcomp.constants.FORMAT_TEXT),
            'raw_answers': question.answers,
        }

    def create_answers_mdd(self, question_id, question_number, question, variant):
        answers = []

        for key, items in question.answers.items():
            answers.append({
                'label': self._format_doc(items['key'].document),
                'initial_label': items['key'].text,
                'raw_label': self._format_doc(items['key'].document, doc_format = quizcomp.constants.FORMAT_TEXT),
                'choices': self._create_answers_mcq_list(items['values']),
            })

        return answers

    def create_answers_ma(self, question_id, question_number, question, variant):
        return self._create_answers_mcq_list(question.answers)

    def create_answers_fimb(self, question_id, question_number, question, variant):
        answers = {}

        for (key, item) in question.answers.items():
            solutions = []
            for value in item['values']:
                solutions.append(self._create_answers_text_value(value))

            answers[key] = {
                'label': self._format_doc(item['key'].document),
                'raw_label': self._format_doc(item['key'].document, doc_format = quizcomp.constants.FORMAT_TEXT),
                'initial_label': item['key'].text,
                'solutions': solutions,
            }

        return answers

    def create_answers_fitb(self, question_id, question_number, question, variant):
        return self.create_answers_fimb(question_id, question_number, question, variant)['']['solutions']

    def create_answers_sa(self, question_id, question_number, question, variant):
        return self._create_answers_text(question_id, question_number, question, variant)

    def create_answers_essay(self, question_id, question_number, question, variant):
        return self._create_answers_text(question_id, question_number, question, variant)

    def _create_answers_text(self, question_id, question_number, question, variant):
        solutions = []
        for value in question.answers:
            solutions.append(self._create_answers_text_value(value))

        return solutions

    def _create_answers_text_value(self, value):
        """
        Create an output dict for a value that was parsed from text (the result of a parsed string).
        """

        result = {
            'text': self._format_doc(value.document),
            'raw_text': self._format_doc(value.document, doc_format = quizcomp.constants.FORMAT_TEXT),
            'initial_text': value.text,
            'clean': self.clean_solution_content(value.document),
        }

        if (value.has_feedback()):
            result.update({
                'feedback': self._format_doc(value.feedback.document),
                'raw_feedback': self._format_doc(value.feedback.document, doc_format = quizcomp.constants.FORMAT_TEXT),
                'initial_feedback': value.feedback.text,
            })

        return result

    def _format_doc(self, doc, doc_format = None, format_options = None):
        if (doc_format is None):
            doc_format = self.format

        if (format_options is None):
            format_options = self.parser_format_options

        return doc.to_format(doc_format, **format_options)

    def _store_images(self, link, base_dir):
        if (self.image_base_dir is None):
            self.image_base_dir = quizcomp.util.dirent.get_temp_path(prefix = 'quizcomp-images-', rm = self.cleanup_images)

        os.makedirs(self.image_base_dir, exist_ok = True)

        if (re.match(r'^http(s)?://', link)):
            temp_dir = quizcomp.util.dirent.get_temp_path(prefix = 'quizcomp-image-dl-')
            in_path = quizcomp.util.http.get_file(link, temp_dir)
            image_id = link
        else:
            in_path = os.path.join(base_dir, link)
            image_id = in_path

        ext = os.path.splitext(in_path)[-1]
        filename = "%03d%s" % (len(self.image_paths), ext)
        out_path = os.path.join(self.image_base_dir, filename)

        quizcomp.util.dirent.copy_dirent(in_path, out_path)

        if (self.image_relative_root is not None):
            out_path = os.path.join(self.image_relative_root, filename)

        self.image_paths[image_id] = out_path

        return out_path
