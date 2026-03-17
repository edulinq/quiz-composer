import logging
import os
import urllib.parse
import re
import typing

import requests

import quizcomp.common
import quizcomp.constants
import quizcomp.group
import quizcomp.question.base
import quizcomp.question.common
import quizcomp.quiz
import quizcomp.util.hash

# TODO(eriq): This code assumes there will never be more than a page of items returned.
PAGE_SIZE: int = 75

CANVAS_QUIZCOMP_BASEDIR: str = '/quiz-composer'
CANVAS_QUIZCOMP_QUIZ_DIRNAME: str = 'quiz'

QUIZ_TYPE_ASSIGNMENT: str = 'assignment'
QUIZ_TYPE_PRACTICE: str = 'practice_quiz'

QUESTION_TYPE_MAP: typing.Dict[str, str] = {
    # Direct Mappings
    quizcomp.constants.QUESTION_TYPE_ESSAY: 'essay_question',
    quizcomp.constants.QUESTION_TYPE_FIMB: 'fill_in_multiple_blanks_question',
    quizcomp.constants.QUESTION_TYPE_MATCHING: 'matching_question',
    quizcomp.constants.QUESTION_TYPE_MA: 'multiple_answers_question',
    quizcomp.constants.QUESTION_TYPE_MCQ: 'multiple_choice_question',
    quizcomp.constants.QUESTION_TYPE_MDD: 'multiple_dropdowns_question',
    quizcomp.constants.QUESTION_TYPE_NUMERICAL: 'numerical_question',
    quizcomp.constants.QUESTION_TYPE_TEXT_ONLY: 'text_only_question',
    quizcomp.constants.QUESTION_TYPE_TF: 'true_false_question',
    # Indirect Mappings
    quizcomp.constants.QUESTION_TYPE_FITB: 'short_answer_question',
    quizcomp.constants.QUESTION_TYPE_SA: 'essay_question',
}

QUESTION_FEEDBACK_MAPPING: typing.Dict[str, str] = {
    'general': 'neutral_comments_html',
    'correct': 'correct_comments_html',
    'incorrect': 'incorrect_comments_html',
}

DEFAULT_CANVAS_OPTIONS: typing.Dict[str, typing.Any] = {
    'practice': True,
    'published': False,
    'hide_results': None,
    'show_correct_answers': True,
    'allowed_attempts': 1,
    'scoring_policy': 'keep_highest',
    'assignment_group_name': 'Quizzes',
}

ALLOWED_VALUES: typing.Dict[str, typing.List[typing.Any]] = {
    'practice': [True, False],
    'published': [True, False],
    'hide_results': [None, 'always', 'until_after_last_attempt'],
    'show_correct_answers': [True, False],
    'scoring_policy': ['keep_highest', 'keep_latest'],
}

class InstanceInfo:
    """ Info on how to connect to a Canvas instance. """

    def __init__(self, base_url: str, course_id: str, token: str) -> None:
        self.base_url: str = base_url
        """ URL for the target Canvas server. """

        self.course_id: str = course_id
        """ ID of the target Canvas course. """

        self.token: str = token
        """ Canvas authentication token. """

        self.context: typing.Dict[str, typing.Any] = {}
        """ Context informaation. """

    def base_headers(self) -> typing.Dict[str, str]:
        """ Get standard Canvas headers. """

        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json+canvas-string-ids",
        }

class CanvasUploader:
    """
    Upload quizes to Canvas.
    """

    def __init__(self, instance: InstanceInfo, force: bool = False, **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

        if (instance is None):
            raise ValueError("Canvas instance information cannot be None.")

        self.instance: InstanceInfo = instance
        """ The Canvas instance to connect to. """

        self.force = force
        """ Whether to remove existing quizzes while uploading. """

    def upload_quiz(self, quiz: quizcomp.quiz.Quiz, **kwargs: typing.Any) -> None:
        """ Upload a quiz to Canvas. """

        upload_quiz(quiz, self.instance, force = self.force);

def validate_options(old_options: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
    """ Validate Canvas options and return a clean version of the options. """

    options = DEFAULT_CANVAS_OPTIONS.copy()
    options.update(old_options)

    for (key, value) in options.items():
        if (key not in DEFAULT_CANVAS_OPTIONS):
            logging.warning("Unknown canvas options: '%s'." % (key))
            continue

        if (key in ALLOWED_VALUES):
            if (value not in ALLOWED_VALUES[key]):
                raise quizcomp.common.QuizValidationError("Canvas option '%s' has value '%s' not in allowed values: %s." % (key, value, ALLOWED_VALUES[key]))

        if (key == 'allowed_attempts'):
            options['allowed_attempts'] = _validate_allowed_attempts(value)

    return options

def _validate_allowed_attempts(allowed_attempts: typing.Any) -> int:
    """ Validate and fetch the number of allowed attempts. """

    if (not isinstance(allowed_attempts, (str, int))):
        raise quizcomp.common.QuizValidationError("Allowed attempts must be a positive int (or -1), found '%s'." % (str(allowed_attempts)))

    try:
        allowed_attempts = int(allowed_attempts)
    except:
        raise quizcomp.common.QuizValidationError("Allowed attempts must be a positive int (or -1), found '%s'." % (str(allowed_attempts)))

    if ((allowed_attempts < -1) or (allowed_attempts == 0)):
        raise quizcomp.common.QuizValidationError("Allowed attempts must be a positive int (or -1), found '%s'." % (str(allowed_attempts)))

    return allowed_attempts

def upload_quiz(quiz: quizcomp.quiz.Quiz, instance: InstanceInfo, force: bool = False) -> bool:
    """
    Upload a quiz to Canvas.
    Data may be written into the instance context.
    """

    if (not isinstance(quiz, quizcomp.quiz.Quiz)):
        raise ValueError("Canvas quiz uploader requires a quizcomp.quiz.Quiz type, found %s." % (type(quiz)))

    existing_ids = get_matching_quiz_ids(quiz.title, instance)
    if ((len(existing_ids) > 0) and (not force)):
        logging.info("Found a quiz with a matching name '%s', skipping upload.", quiz.title)
        return False

    for existing_id in existing_ids:
        logging.debug("Deleting existing quiz '%s' (%s).", quiz.title, existing_id)
        delete_quiz(existing_id, instance)

    create_quiz(quiz, instance)

    return True

def upload_canvas_files(quiz: quizcomp.quiz.Quiz, instance: InstanceInfo):
    """
    Upload a file to Canvas.
    Canvas requires that images (and other files) be uploaded to their side (instead of embedded),
    so upload all images in one method so we don't upload duplicates.
    """

    # {path: <canvas file id>, ...}
    file_ids = {}

    paths = []
    for group in quiz.groups:
        paths += group.collect_file_paths()

    for path in sorted(set(paths)):
        canvas_path = '/'.join([
            CANVAS_QUIZCOMP_BASEDIR,
            CANVAS_QUIZCOMP_QUIZ_DIRNAME,
            quiz.title,
            quizcomp.util.hash.sha256(path) + os.path.splitext(path)[-1]
        ])

        file_id = upload_file(path, canvas_path, instance)
        file_ids[path] = file_id

    return file_ids

def get_matching_quiz_ids(title: str, instance: InstanceInfo) -> typing.List[str]:
    """ Get Canvas IDs for any quizzes that match the given title. """

    response = requests.request(
        method = "GET",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/quizzes?per_page={PAGE_SIZE}",
        headers = instance.base_headers())
    response.raise_for_status()

    ids = []
    for quiz in response.json():
        if (quiz['title'] == title):
            ids.append(str(quiz['id']))

    return ids

def delete_quiz(quiz_id: str, instance: InstanceInfo) -> None:
    """ Delete a quiz on Canvas. """

    response = requests.request(
        method = "DELETE",
        url = "%s/api/v1/courses/%s/quizzes/%s" % (instance.base_url, instance.course_id, quiz_id),
        headers = instance.base_headers())
    response.raise_for_status()

def fetch_assignment_group(name: str, instance: InstanceInfo) -> typing.Union[str, None]:
    """ Get the assignment group ID (if any) that has an assignment (e.g., quiz) that matches the given name. """

    if (name is None):
        return None

    response = requests.request(
        method = "GET",
        url = f"{instance.base_url}/api/v1/courses/{instance.course_id}/assignment_groups?per_page={PAGE_SIZE}",
        headers = instance.base_headers())
    response.raise_for_status()

    for assignment in response.json():
        if (assignment['name'] == name):
            return assignment['id']

    return None

def create_quiz(quiz: quizcomp.quiz.Quiz, instance: InstanceInfo) -> None:
    """ Create a quiz (with all questions) on Canvas. """

    file_ids = upload_canvas_files(quiz, instance)
    instance.context['file_ids'] = file_ids

    assignment_group_id = fetch_assignment_group(quiz.canvas['assignment_group_name'], instance)

    quiz_type = QUIZ_TYPE_ASSIGNMENT
    if (quiz.canvas['practice']):
        quiz_type = QUIZ_TYPE_PRACTICE

    description = quiz.description.document.to_canvas(canvas_instance = instance, pretty = False)

    data = {
        'quiz[title]': quiz.title,
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
        url = "%s/api/v1/courses/%s/quizzes" % (instance.base_url, instance.course_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

    quiz_id = response.json()['id']

    for question_group in quiz.groups:
        create_question_group(quiz_id, question_group, instance)

def create_question_group(quiz_id: str, group: quizcomp.group.Group, instance: InstanceInfo) -> None:
    """ Create a question group for the given quiz. """

    data = {
        'quiz_groups[][name]': group.name,
        'quiz_groups[][pick_count]': group.pick_count,
        'quiz_groups[][question_points]': group.points,
    }

    response = requests.request(
        method = "POST",
        url = "%s/api/v1/courses/%s/quizzes/%s/groups" % (instance.base_url, instance.course_id, quiz_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

    group_id = response.json()['quiz_groups'][0]['id']

    for i in range(len(group.questions)):
        create_question(quiz_id, group_id, group.questions[i], i, instance)

def create_question(quiz_id: str, group_id: str, question: quizcomp.question.base.Question, index: int, instance: InstanceInfo) -> None:
    """ Create a question within the given quiz/group. """

    data = _create_question_json(group_id, question, index, instance)

    response = requests.request(
        method = "POST",
        url = "%s/api/v1/courses/%s/quizzes/%s/questions" % (instance.base_url, instance.course_id, quiz_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

def _create_question_json(
        group_id: str,
        question: quizcomp.question.base.Question,
        index: int,
        instance: InstanceInfo,
        ) -> typing.Dict[str, typing.Any]:
    """ Create a dict that represent a question for a Canvas API request. """

    question_type = QUESTION_TYPE_MAP[question.question_type]

    name = question.name
    if (question.custom_header is not None):
        name = question.custom_header

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

    # Handle question-level feedback.
    for (key, canvas_key) in QUESTION_FEEDBACK_MAPPING.items():
        if (key not in question.feedback):
            continue

        data_key = "question[%s]" % (canvas_key)
        text = question.feedback[key].document.to_canvas(canvas_instance = instance, pretty = False)
        data[data_key] = text

    _serialize_answers(data, question, instance)

    return data

def _serialize_answers(data: typing.Dict[str, typing.Any], question: quizcomp.question.base.Question, instance: InstanceInfo) -> None:
    """ Convert a question's answers to Canvas JSON. """

    # In Canvas, short answer questions also get mapped to the essay Canvas type.
    if (question.question_type in [quizcomp.constants.QUESTION_TYPE_ESSAY, quizcomp.constants.QUESTION_TYPE_SA]):
        # Essay questions have no answers.
        pass
    elif (question.question_type == quizcomp.constants.QUESTION_TYPE_FIMB):
        _serialize_fimb_answers(data, question, instance)
    elif (question.question_type == quizcomp.constants.QUESTION_TYPE_FITB):
        _serialize_fimb_answers(data, question, instance)
    elif (question.question_type == quizcomp.constants.QUESTION_TYPE_MATCHING):
        _serialize_matching_answers(data, question, instance)
    elif (question.question_type == quizcomp.constants.QUESTION_TYPE_NUMERICAL):
        _serialize_numeric_answers(data, question.answers, instance)
    elif (question.question_type == quizcomp.constants.QUESTION_TYPE_TEXT_ONLY):
        # Text-Only questions have no answers.
        pass
    elif (isinstance(question.answers, list)):
        use_text = (question.question_type == quizcomp.constants.QUESTION_TYPE_TF)
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
        answers: typing.List[quizcomp.question.common.ParsedTextChoice],
        instance: InstanceInfo,
        start_index: int = 0,
        blank_id: typing.Union[str, None] = None,
        use_text: bool = False,
        ) -> None:
    """ Clean a list of answers for Canvas. """

    for i in range(len(answers)):
        _serialize_answer(data, answers[i], start_index + i, instance,
            blank_id = blank_id, use_text = use_text)

def _serialize_answer(
        data: typing.Dict[str, typing.Any],
        answer: quizcomp.question.common.ParsedTextChoice,
        index: int,
        instance: InstanceInfo,
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

def _serialize_matching_answers(data: typing.Dict[str, typing.Any], question: quizcomp.question.base.Question, instance: InstanceInfo):
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
        distractors = [distractor.document.to_text(text_allow_special_text = True, text_allow_all_characters = True) for distractor in question.answers['distractors']]
        data["question[matching_answer_incorrect_matches]"] = "\n".join(distractors)

def _serialize_fimb_answers(data: typing.Dict[str, typing.Any], question: quizcomp.question.base.Question, instance: InstanceInfo) -> None:
    """ Concert the answers for a FIMB-type question to Canvas API data. """

    index = 0

    for (key, item) in question.answers.items():
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
        answers: typing.List[quizcomp.question.common.NumericChoice],
        instance: InstanceInfo,
        ) -> None:
    """ Concert the answers for a numeric-type question to Canvas API data. """

    # Note that the keys/constants for numerical answers are different than what the documentation says:
    # https://canvas.instructure.com/doc/api/quiz_questions.html#QuizQuestion

    for i in range(len(answers)):
        answer = answers[i]

        data[f"question[answers][{i}][answer_weight]"] = 100
        data[f"question[answers][{i}][numerical_answer_type]"] = answer.type + '_answer'

        if (answer.type == quizcomp.constants.NUMERICAL_ANSWER_TYPE_EXACT):
            data[f"question[answers][{i}][answer_exact]"] = answer.value
            data[f"question[answers][{i}][answer_error_margin]"] = answer.margin
        elif (answer.type == quizcomp.constants.NUMERICAL_ANSWER_TYPE_RANGE):
            data[f"question[answers][{i}][answer_range_start]"] = answer.min
            data[f"question[answers][{i}][answer_range_end]"] = answer.max
        elif (answer.type == quizcomp.constants.NUMERICAL_ANSWER_TYPE_PRECISION):
            data[f"question[answers][{i}][answer_approximate]"] = answer.value
            data[f"question[answers][{i}][answer_precision]"] = answer.precision
        else:
            raise ValueError(f"Unknown numerical answer type: '{answer.type}'.")

        if (answer.feedback is not None):
            feedback_text = answer.feedback.document.to_canvas(canvas_instance = instance, pretty = False)
            data[f"question[answers][{i}][answer_comment_html]"] = feedback_text

def upload_file(path: str, canvas_path: str, instance: InstanceInfo) -> str:
    """ Upload a file to Canvas and fetch its ID. """

    parent_id = ensure_folder(os.path.dirname(canvas_path), instance)
    upload_url, upload_params = _init_file_upload(path, canvas_path, parent_id, instance)
    file_id = _upload_file_contents(path, upload_url, upload_params)

    return file_id

def _init_file_upload(
        path: str,
        canvas_path: str,
        parent_id: str,
        instance: InstanceInfo,
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
        url = "%s/api/v1/courses/%s/files" % (instance.base_url, instance.course_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

    response = response.json()

    upload_url = response['upload_url']
    upload_params = response['upload_params']

    return upload_url, upload_params

def _upload_file_contents(path: str, upload_url: str, upload_params: typing.Dict[str, typing.Any]) -> str:
    """ Upload the actual file contents to Canvas. """

    files = {
        'file': open(path, 'rb'),
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

    return file_id

def ensure_folder(canvas_path: str, instance: InstanceInfo) -> str:
    """ Ensure that a Canvas folder exists and fetch its ID. """

    folder_id = get_folder(canvas_path, instance)
    if (folder_id is not None):
        return folder_id

    folder_id = create_folder(canvas_path, instance)

    # Canvas will not hide created parents.
    hide_folder(CANVAS_QUIZCOMP_BASEDIR, instance)

    return folder_id

def get_folder(canvas_path: str, instance: InstanceInfo) -> typing.Union[str, None]:
    """ Get a Canvas folder ID (if it exists). """

    # The canvas path should be absolute.
    response = requests.request(
        method = "GET",
        url = "%s/api/v1/courses/%s/folders/by_path%s" % (instance.base_url, instance.course_id, canvas_path),
        headers = instance.base_headers())

    if (response.status_code == 404):
        return None

    response.raise_for_status()

    return response.json()[-1]['id']

def create_folder(canvas_path: str, instance: InstanceInfo) -> str:
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
        url = "%s/api/v1/courses/%s/folders" % (instance.base_url, instance.course_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()

    folder_id = response.json()['id']

    return folder_id

def hide_folder(canvas_path: str, instance: InstanceInfo) -> None:
    """ Ensure that a Canvas folder (specified by path) is hidden. """

    folder_id = get_folder(canvas_path, instance)
    if (folder_id is None):
        raise ValueError(f"Could not find Canvas folder to hide: '{canvas_path}'.")

    hide_folder_id(folder_id, instance)

def hide_folder_id(folder_id: str, instance: InstanceInfo) -> None:
    """ Ensure that a Canvas folder (specified by ID) is hidden. """

    data = {
        # Canvas wants a string here despite the documentation saying it is a bool.
        # TODO(eriq): Make a bug request?
        'hidden': 'true',
    }

    response = requests.request(
        method = "PUT",
        url = "%s/api/v1/folders/%s" % (instance.base_url, folder_id),
        headers = instance.base_headers(),
        data = data)
    response.raise_for_status()
