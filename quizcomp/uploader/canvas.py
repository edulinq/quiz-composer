# pylint: disable=missing-timeout

import logging
import os
import urllib.parse
import typing

import requests

import quizcomp.model.answer
import quizcomp.model.base
import quizcomp.model.config
import quizcomp.model.constants
import quizcomp.model.group
import quizcomp.model.question
import quizcomp.model.quiz

_logger = logging.getLogger(__name__)

# TODO(eriq): This code assumes there will never be more than a page of items returned.
PAGE_SIZE: int = 75

CANVAS_QUIZCOMP_BASEDIR: str = '/quiz-composer'
CANVAS_QUIZCOMP_QUIZ_DIRNAME: str = 'quiz'

QUIZ_TYPE_ASSIGNMENT: str = 'assignment'
QUIZ_TYPE_PRACTICE: str = 'practice_quiz'

QUESTION_TYPE_MAP: typing.Dict[quizcomp.model.constants.QuestionType, str] = {
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

QUESTION_FEEDBACK_MAPPING: typing.Dict[str, str] = {
    'general': 'neutral_comments_html',
    'correct': 'correct_comments_html',
    'incorrect': 'incorrect_comments_html',
}

class CanvasUploader:
    """
    Upload quizes to Canvas.
    """

    def __init__(self,
            instance: quizcomp.uploader.instance.CanvasInstanceInfo,
            force: bool = False,
            **kwargs: typing.Any,
            ) -> None:
        super().__init__(**kwargs)

        if (instance is None):
            raise ValueError("Canvas instance information cannot be None.")

        self.instance: quizcomp.uploader.instance.CanvasInstanceInfo = instance
        """ The Canvas instance to connect to. """

        self.force = force
        """ Whether to remove existing quizzes while uploading. """

    def upload_quiz(self, quiz: quizcomp.model.quiz.Quiz, **kwargs: typing.Any) -> None:
        """ Upload a quiz to Canvas. """

        upload_quiz(quiz, self.instance, force = self.force)

def upload_quiz(
        quiz: quizcomp.model.quiz.Quiz,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        force: bool = False,
        ) -> bool:
    """
    Upload a quiz to Canvas.
    Data may be written into the instance context.
    """

    if (not isinstance(quiz, quizcomp.model.quiz.Quiz)):
        raise ValueError(f"Canvas quiz uploader requires a quizcomp.model.quiz.Quiz type, found {type(quiz)}.")

    existing_ids = get_matching_quiz_ids(quiz.get_name(), instance)
    if ((len(existing_ids) > 0) and (not force)):
        _logger.info("Found a quiz with a matching name '%s', skipping upload.", quiz.get_name())
        return False

    for existing_id in existing_ids:
        _logger.debug("Deleting existing quiz '%s' (%s).", quiz.get_name(), existing_id)
        delete_quiz(existing_id, instance)

    create_quiz(quiz, instance)

    return True

def upload_canvas_files(
        quiz: quizcomp.model.quiz.Quiz,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        ) -> typing.Dict[str, str]:
    """
    Upload a file to Canvas.
    Canvas requires that images (and other files) be uploaded to their side (instead of embedded),
    so upload all images in one method so we don't upload duplicates.
    """

    # NOTE(eq) - Removed. Will be implemented in LMS Toolkit.
    return {}

def get_matching_quiz_ids(title: str, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> typing.List[str]:
    """ Get Canvas IDs for any quizzes that match the given title. """

    response = requests.request(
        method = "GET",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/quizzes?per_page={PAGE_SIZE}",
        headers = instance.base_headers())  # type: ignore[arg-type]
    response.raise_for_status()

    ids = []
    for quiz in response.json():
        if (quiz['title'] == title):
            ids.append(str(quiz['id']))

    return ids

def delete_quiz(quiz_id: str, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> None:
    """ Delete a quiz on Canvas. """

    response = requests.request(
        method = "DELETE",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/quizzes/{quiz_id}",
        headers = instance.base_headers())  # type: ignore[arg-type]
    response.raise_for_status()

def fetch_assignment_group(name: str, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> typing.Union[str, None]:
    """ Get the assignment group ID (if any) that has an assignment (e.g., quiz) that matches the given name. """

    if (name is None):
        return None

    response = requests.request(
        method = "GET",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/assignment_groups?per_page={PAGE_SIZE}",
        headers = instance.base_headers())  # type: ignore[arg-type]
    response.raise_for_status()

    for assignment in response.json():
        if (assignment['name'] == name):
            return str(assignment['id'])

    return None

def create_quiz(quiz: quizcomp.model.quiz.Quiz, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> None:
    """ Create a quiz (with all questions) on Canvas. """

    file_ids = upload_canvas_files(quiz, instance)
    instance.context['file_ids'] = file_ids

    assignment_group_id = fetch_assignment_group(quiz.canvas['assignment_group_name'], instance)

    quiz_type = QUIZ_TYPE_ASSIGNMENT
    if (quiz.canvas['practice']):
        quiz_type = QUIZ_TYPE_PRACTICE

    description = quiz.description.document.to_canvas(canvas_instance = instance, pretty = False)

    data = {
        'quiz[title]': quiz.get_name(),
        'quiz[description]': f"<p>{description}</p><br /><hr /><p>Version: {quiz.version}</p>",
        'quiz[quiz_type]': quiz_type,
        'quiz[published]': quiz.canvas['published'],
        'quiz[assignment_group_id]': assignment_group_id,
        'quiz[time_limit]': quiz.time_limit_mins,
        'quiz[allowed_attempts]': quiz.canvas['allowed_attempts'],
        'quiz[show_correct_answers]': str(quiz.canvas['show_correct_answers']).lower(),
        'quiz[hide_results]': quiz.canvas['hide_results'],
        'quiz[shuffle_answers]': str(quiz.shuffle_answers).lower(),
        'quiz[scoring_policy]': quiz.canvas['scoring_policy'],
    }

    response = requests.request(
        method = "POST",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/quizzes",
        headers = instance.base_headers(),  # type: ignore[arg-type]
        data = data)
    response.raise_for_status()

    quiz_id = response.json()['id']

    for question_group in quiz.groups:
        create_question_group(quiz_id, question_group, instance)

def create_question_group(
        quiz_id: str,
        group: quizcomp.model.group.Group,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        ) -> None:
    """ Create a question group for the given quiz. """

    data = {
        'quiz_groups[][name]': group.name,
        'quiz_groups[][pick_count]': group.pick_count,
        'quiz_groups[][question_points]': group.points,
    }

    response = requests.request(
        method = "POST",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/quizzes/{quiz_id}/groups",
        headers = instance.base_headers(),  # type: ignore[arg-type]
        data = data)
    response.raise_for_status()

    group_id = response.json()['quiz_groups'][0]['id']

    for (i, question) in enumerate(group.questions):
        create_question(quiz_id, group_id, question, i, instance)

def create_question(
        quiz_id: str,
        group_id: int,
        question: quizcomp.model.question.Question,
        index: int,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        ) -> None:
    """ Create a question within the given quiz/group. """

    data = _create_question_json(group_id, question, index, instance)

    response = requests.request(
        method = "POST",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/quizzes/{quiz_id}/questions",
        headers = instance.base_headers(),  # type: ignore[arg-type]
        data = data)
    response.raise_for_status()

def _create_question_json(
        group_id: int,
        question: quizcomp.model.question.Question,
        index: int,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        ) -> typing.Dict[str, typing.Any]:
    """ Create a dict that represent a question for a Canvas API request. """

    question_type = QUESTION_TYPE_MAP[question.question_type]

    name = question.name

    custom_header = question.get_config(quizcomp.model.config.OPTION_CUSTOM_HEADER)
    if (custom_header is not None):
        name = custom_header

    data = {
        'question[question_type]': question_type,
        'question[question_name]': name,
        'question[quiz_group_id]': group_id,
        # The actual points is taken from the group,
        # but put in a one here so people don't get scared when they see a zero.
        'question[points_possible]': 1,
        'question[position]': index,
        'question[question_text]': question.prompt.document.to_canvas(canvas_instance = instance, pretty = False),
    }

    _serialize_answers(data, question, instance)

    return data

def _serialize_answers(
        data: typing.Dict[str, typing.Any],
        question: quizcomp.model.question.Question,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        ) -> None:
    """ Convert a question's answers to Canvas JSON. """

    # In Canvas, short answer questions also get mapped to the essay Canvas type.
    if (question.question_type in [quizcomp.model.constants.QuestionType.ESSAY, quizcomp.model.constants.QuestionType.SA]):
        # Essay questions have no answers.
        pass
    elif (question.question_type == quizcomp.model.constants.QuestionType.FIMB):
        _serialize_fimb_answers(data, question, instance)
    elif (question.question_type == quizcomp.model.constants.QuestionType.FITB):
        _serialize_fimb_answers(data, question, instance)
    elif (question.question_type == quizcomp.model.constants.QuestionType.MATCHING):
        _serialize_matching_answers(data, question, instance)
    elif (question.question_type == quizcomp.model.constants.QuestionType.NUMERICAL):
        _serialize_numeric_answers(data, question.answers, instance)
    elif (question.question_type == quizcomp.model.constants.QuestionType.TEXT_ONLY):
        # Text-Only questions have no answers.
        pass
    elif (isinstance(question.answers, list)):
        use_text = (question.question_type == quizcomp.model.constants.QuestionType.TF)
        _serialize_answer_list(data, question.answers, instance, use_text = use_text)
    elif (isinstance(question.answers, dict)):
        count = 0
        for key, item in question.answers.items():
            _serialize_answer_list(data, item['values'], instance,
                    start_index = count, blank_id = key, use_text = True)
            count += len(item['values'])
    else:
        raise ValueError(f"Unknown answers type '{type(question.answers)}'.")

def _serialize_answer_list(
        data: typing.Dict[str, typing.Any],
        answers: typing.List[typing.Any],
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        start_index: int = 0,
        blank_id: typing.Union[str, None] = None,
        use_text: bool = False,
        ) -> None:
    """ Clean a list of answers for Canvas. """

    for (i, answer) in enumerate(answers):
        _serialize_answer(data, answer, start_index + i, instance,
            blank_id = blank_id, use_text = use_text)

def _serialize_answer(
        data: typing.Dict[str, typing.Any],
        answer: typing.Any,
        index: int,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        blank_id: typing.Union[str, None] = None,
        use_text: bool = False,
        ) -> None:
    """ Clean answer data for Canvas. """

    weight = 0
    if (answer.is_correct()):
        weight = 100

    data[f"question[answers][{index}][answer_weight]"] = weight

    if (use_text):
        text = answer.document.to_text(text_allow_special_text = True, text_allow_all_characters = True)
        data[f"question[answers][{index}][answer_text]"] = text
    else:
        html = answer.document.to_canvas(canvas_instance = instance, pretty = False)
        data[f"question[answers][{index}][answer_html]"] = html

    if (blank_id is not None):
        data[f"question[answers][{index}][blank_id]"] = blank_id

    if (answer.feedback is not None):
        feedback_html = answer.feedback.document.to_canvas(canvas_instance = instance, pretty = False)
        data[f"question[answers][{index}][answer_comment_html]"] = feedback_html

def _serialize_matching_answers(
        data: typing.Dict[str, typing.Any],
        question: quizcomp.model.question.Question,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        ) -> None:
    """ Concert the answers for a matching-type question to Canvas API data. """

    for i in range(len(question.answers['matches'])):
        left_content = question.answers['matches'][i]['left'].document.to_text(text_allow_special_text = True, text_allow_all_characters = True)
        right_content = question.answers['matches'][i]['right'].document.to_text(text_allow_special_text = True, text_allow_all_characters = True)

        data[f"question[answers][{i}][answer_match_left]"] = left_content
        data[f"question[answers][{i}][answer_match_right]"] = right_content

        if (question.answers['matches'][i]['left'].feedback is not None):
            text = question.answers['matches'][i]['left'].feedback.document.to_canvas(canvas_instance = instance, pretty = False)
            data[f"question[answers][{i}][answer_comment_html]"] = text

    if (len(question.answers['distractors']) > 0):
        distractors = [
            distractor.document.to_text(text_allow_special_text = True, text_allow_all_characters = True)
            for distractor
            in question.answers['distractors']
        ]
        data["question[matching_answer_incorrect_matches]"] = "\n".join(distractors)

def _serialize_fimb_answers(
        data: typing.Dict[str, typing.Any],
        question: quizcomp.model.question.Question,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        ) -> None:
    """ Concert the answers for a FIMB-type question to Canvas API data. """

    index = 0

    for item in question.answers.values():
        key_text = item['key'].document.to_text()

        for i in range(len(item['values'])):
            value_text = item['values'][i].document.to_text(text_allow_special_text = True, text_allow_all_characters = True)

            data[f"question[answers][{index}][blank_id]"] = key_text
            data[f"question[answers][{index}][answer_weight]"] = 100
            data[f"question[answers][{index}][answer_text]"] = value_text

            if (item['values'][i].feedback is not None):
                feedback_text = item['values'][i].feedback.document.to_canvas(canvas_instance = instance, pretty = False)
                data[f"question[answers][{index}][answer_comment_html]"] = feedback_text

            index += 1

def _serialize_numeric_answers(
        data: typing.Dict[str, typing.Any],
        answers: typing.List[typing.Any],
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        ) -> None:
    """ Concert the answers for a numeric-type question to Canvas API data. """

    # Note that the keys/constants for numerical answers are different than what the documentation says:
    # https://canvas.instructure.com/doc/api/quiz_questions.html#QuizQuestion

    for (i, answer) in enumerate(answers):
        data[f"question[answers][{i}][answer_weight]"] = 100
        data[f"question[answers][{i}][numerical_answer_type]"] = answer.type + '_answer'

        if (answer.type == quizcomp.model.answer.NumericAnswerType.EXACT):
            data[f"question[answers][{i}][answer_exact]"] = answer.value
            data[f"question[answers][{i}][answer_error_margin]"] = answer.margin
        elif (answer.type == quizcomp.model.answer.NumericAnswerType.RANGE):
            data[f"question[answers][{i}][answer_range_start]"] = answer.min
            data[f"question[answers][{i}][answer_range_end]"] = answer.max
        elif (answer.type == quizcomp.model.answer.NumericAnswerType.PRECISION):
            data[f"question[answers][{i}][answer_approximate]"] = answer.value
            data[f"question[answers][{i}][answer_precision]"] = answer.precision
        else:
            raise ValueError(f"Unknown numerical answer type: '{answer.type}'.")

        if (answer.feedback is not None):
            feedback_text = answer.feedback.document.to_canvas(canvas_instance = instance, pretty = False)
            data[f"question[answers][{i}][answer_comment_html]"] = feedback_text

def upload_file(path: str, canvas_path: str, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> str:
    """ Upload a file to Canvas and fetch its ID. """

    parent_id = ensure_folder(os.path.dirname(canvas_path), instance)
    upload_url, upload_params = _init_file_upload(path, canvas_path, parent_id, instance)
    file_id = _upload_file_contents(path, upload_url, upload_params)

    return file_id

def _init_file_upload(
        path: str,
        canvas_path: str,
        parent_id: str,
        instance: quizcomp.uploader.instance.CanvasInstanceInfo,
        ) -> typing.Tuple[str, typing.Dict[str, typing.Any]]:
    """ Prepare to upload a file to Canvas. """

    canvas_name = os.path.basename(canvas_path)

    size = os.stat(path).st_size

    data = {
        'name': canvas_name,
        'size': size,
        'parent_folder_id': parent_id,
        'on_duplicate': 'overwrite',
    }

    response = requests.request(
        method = "POST",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/files",
        headers = instance.base_headers(),  # type: ignore[arg-type]
        data = data)
    response.raise_for_status()

    response = response.json()

    upload_url = response['upload_url']
    upload_params = response['upload_params']

    return upload_url, upload_params

def _upload_file_contents(path: str, upload_url: str, upload_params: typing.Dict[str, typing.Any]) -> str:
    """ Upload the actual file contents to Canvas. """

    files = {
        'file': open(path, 'rb'),  # pylint: disable=consider-using-with
    }

    response = requests.request(
        method = "POST",
        url = upload_url,
        data = upload_params,
        files = files)
    response.raise_for_status()

    file_id = None

    location = response.headers.get('Location', None)
    if (location is not None):
        file_id = os.path.basename(urllib.parse.urlparse(location).path)
    else:
        # The location was not present in the header, check for a JSON body.
        try:
            body = response.json()
            file_id = str(body['id'])
        except Exception:
            pass

    if (file_id is None):
        raise ValueError(f"Could not find id for uploaded file in response from Canvas: '{path}'.")

    return str(file_id)

def ensure_folder(canvas_path: str, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> str:
    """ Ensure that a Canvas folder exists and fetch its ID. """

    folder_id = get_folder(canvas_path, instance)
    if (folder_id is not None):
        return folder_id

    folder_id = create_folder(canvas_path, instance)

    # Canvas will not hide created parents.
    hide_folder(CANVAS_QUIZCOMP_BASEDIR, instance)

    return folder_id

def get_folder(canvas_path: str, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> typing.Union[str, None]:
    """ Get a Canvas folder ID (if it exists). """

    # The canvas path should be absolute.
    response = requests.request(
        method = "GET",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/folders/by_path{canvas_path}",
        headers = instance.base_headers())  # type: ignore[arg-type]

    if (response.status_code == 404):
        return None

    response.raise_for_status()

    return str(response.json()[-1]['id'])

def create_folder(canvas_path: str, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> str:
    """ Create a folder in Canvas. """

    name = os.path.basename(canvas_path)
    parent_path = os.path.dirname(canvas_path)

    data = {
        'name': name,
        'parent_folder_path': parent_path,
        # Canvas wants a string here despite the documentation saying it is a bool.
        'hidden': 'true',
    }

    response = requests.request(
        method = "POST",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/folders",
        headers = instance.base_headers(),  # type: ignore[arg-type]
        data = data)
    response.raise_for_status()

    return str(response.json()['id'])

def hide_folder(canvas_path: str, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> None:
    """ Ensure that a Canvas folder (specified by path) is hidden. """

    folder_id = get_folder(canvas_path, instance)
    if (folder_id is None):
        raise ValueError(f"Could not find Canvas folder to hide: '{canvas_path}'.")

    hide_folder_id(folder_id, instance)

def hide_folder_id(folder_id: str, instance: quizcomp.uploader.instance.CanvasInstanceInfo) -> None:
    """ Ensure that a Canvas folder (specified by ID) is hidden. """

    data = {
        # Canvas wants a string here despite the documentation saying it is a bool.
        # TODO(eriq): Make a bug request?
        'hidden': 'true',
    }

    response = requests.request(
        method = "PUT",
        url = f"{instance.base_url}/api/v1/folders/{folder_id}",
        headers = instance.base_headers(),  # type: ignore[arg-type]
        data = data)
    response.raise_for_status()
