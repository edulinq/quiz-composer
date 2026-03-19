import logging
import os
import re
import typing

import bs4
import edq.util.dirent
import edq.util.json
import requests

import quizcomp.constants
import quizcomp.variant

URL_BASE: str = 'https://www.gradescope.com'
URL_HOMEPAGE = URL_BASE
URL_LOGIN: str = f"{URL_BASE}/login"
URL_ASSIGNMENTS: str = f"{URL_BASE}/courses/%s/assignments"
URL_ASSIGNMENT: str = f"{URL_BASE}/courses/%s/assignments/%s"
URL_ASSIGNMENT_GROUP: str = f"{URL_BASE}/courses/%s/assignment_containers"
URL_ASSIGNMENT_EDIT: str = f"{URL_BASE}/courses/%s/assignments/%s/edit"
URL_ASSIGNMENT_RUBRIC: str = f"{URL_BASE}/courses/%s/assignments/%s/rubric/edit"
URL_ASSIGNMENT_ADD_RUBRIC_ITEM: str = f"{URL_BASE}/courses/%s/questions/%s/rubric_items"
URL_NEW_ASSIGNMENT_FORM: str = f"{URL_BASE}/courses/%s/assignments/new"
URL_EDIT_OUTLINE: str = f"{URL_BASE}/courses/%s/assignments/%s/outline/edit"
URL_PATCH_OUTLINE: str = f"{URL_BASE}/courses/%s/assignments/%s/outline"

NAME_BOX_ID: str = 'name'
ID_BOX_ID: str = 'id'
SIGNATURE_BOX_ID: str = 'signature'
MANUAL_GRADING_BOX_ID: str = 'manual_grading'

SPECIAL_QUESTION_TYPES: typing.List[str] = [
    NAME_BOX_ID,
    ID_BOX_ID,
    SIGNATURE_BOX_ID,
    MANUAL_GRADING_BOX_ID,
]

EXTEND_BOX_QUESTION_TYPES: typing.List[str] = [
    quizcomp.constants.QUESTION_TYPE_MA,
    quizcomp.constants.QUESTION_TYPE_MCQ,
    quizcomp.constants.QUESTION_TYPE_MDD,
    quizcomp.constants.QUESTION_TYPE_TF,
]

STANDARD_BOX_QUESTION_TYPES: typing.List[str] = [
    quizcomp.constants.QUESTION_TYPE_ESSAY,
    quizcomp.constants.QUESTION_TYPE_FIMB,
    quizcomp.constants.QUESTION_TYPE_FITB,
    quizcomp.constants.QUESTION_TYPE_MATCHING,
    quizcomp.constants.QUESTION_TYPE_NUMERICAL,
    quizcomp.constants.QUESTION_TYPE_SA,
]

BOX_TYPES: typing.List[str] = EXTEND_BOX_QUESTION_TYPES + STANDARD_BOX_QUESTION_TYPES + SPECIAL_QUESTION_TYPES

SP_PER_PT: int = 65536

SESSION_ID_CREATE_ASSIGNMENT_GROUP: str = 'gradescope_create_assignment_group'
SESSION_ID_UPLOAD: str = 'gradescope_upload'

class GradeScopeUploader:
    """
    Upload quizzes to GradeScope.
    """

    def __init__(self,
            course_id: str,
            user: str,
            password: str,
            force: bool = False,
            rubric: bool = False,
            save_http: bool = False,
            **kwargs: typing.Any) -> None:
        super().__init__(**kwargs)

        self.course_id: str = course_id
        """ The GradeScope course ID. """

        self.user: str = user
        """ The GradeScope user/email to authenticate with. """

        self.password: str = password
        """ The GradeScope password to authenticate with. """

        self.force: bool = force
        """ Whether to remove existing quizzes before upload. """

        self.rubric: bool = rubric
        """ Whether to upload the rubric items for the quiz. """

        self.save_http = save_http
        """ Whether to save the HTTP exchanges to disk. """

    def upload_quiz(self,
            variant: quizcomp.variant.Variant,
            base_dir: typing.Union[str, None] = None,
            **kwargs: typing.Any,
            ) -> typing.Tuple[str, bool]:
        """
        Compile a quiz and upload it to GradeScope.

        If base_dir is left None, then a temp dir will be created which will be destroyed on exit.
        If supplied, the base_dir will be left alone when finished.
        """

        if (not isinstance(variant, quizcomp.variant.Variant)):
            raise ValueError(f"GradeScope quiz uploader requires a quizcomp.variant.Variant type, found {type(variant)}.")

        if (base_dir is None):
            base_dir = edq.util.dirent.get_temp_path(prefix = 'quizcomp-gradescope-')

        boxes, special_boxes = self.get_bounding_boxes(variant, base_dir)
        return self.upload(variant, base_dir, boxes, special_boxes)

    def create_assignment_group(self, title: str, gradescope_ids: typing.List[str]) -> None:
        """ Create an assignment group with the given IDs. """

        session = requests.Session()

        self.login(session)

        assignments_url = URL_ASSIGNMENTS % (self.course_id)
        csrf_token = self.get_csrf_token(session, assignments_url)

        headers = {
            'x-csrf-token': csrf_token,
        }

        post_url = URL_ASSIGNMENT_GROUP % (self. course_id)
        data = {
            'title': title,
            'assignment_ids[]': gradescope_ids,
        }

        response = session.post(post_url, params = data, headers = headers)
        response.raise_for_status()

    def get_bounding_boxes(self,
            variant: quizcomp.variant.Variant,
            base_dir: str,
            ) -> typing.Tuple[typing.Dict[str, typing.Dict[str, typing.Any]], typing.Dict[str, typing.Dict[str, typing.Any]]]:
        """ Get bounding boxes for answers. """

        # {<quetion id>: {<part id>: box, ...}, ...}
        boxes: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        # {NAME_BOX_ID: box, ID_BOX_ID: box, SIGNATURE_BOX_ID: box}
        special_boxes: typing.Dict[str, typing.Dict[str, typing.Any]] = {}

        path = os.path.join(base_dir, f"{variant.title}.pos")
        if (not os.path.exists(path)):
            raise ValueError(f"Could not find path for quiz bounding boxes: '{path}'.")

        with open(path, 'r', encoding = edq.util.dirent.DEFAULT_ENCODING) as file:
            for line in file:
                line = line.strip()
                if (line == ""):
                    continue

                parts = [part.strip() for part in line.split(',')]
                if (len(parts) != 12):
                    raise ValueError(f"Position file has row with bad number of parts. Expecting 11, found {len(parts)}.")

                # "ll" == "lower-left"
                # "ur" == "upper-right"
                (question_id, part_id, _, question_type, raw_page_number, ll_x, ll_y, ur_x, ur_y, page_width, page_height, origin) = parts

                if (origin != 'bottom-left'):
                    raise ValueError(f"Unknown bounding box origin: '{origin}'.")

                # Note that the position file and GradeScope use 1-indexed pages.
                page_number = int(raw_page_number)

                if (question_type not in BOX_TYPES):
                    raise ValueError(f"Unknown content type: '{question_type}'.")

                extend_box_right = False
                if (question_type in EXTEND_BOX_QUESTION_TYPES):
                    extend_box_right = True

                    # There is a special case for inline MA questions.
                    if (question_type == quizcomp.constants.QUESTION_TYPE_MA):
                        extend_box_right = False

                (x1, y1), (x2, y2) = self._compute_box(ll_x, ll_y, ur_x, ur_y, page_width, page_height, extend_box_right = extend_box_right)

                if (question_type in SPECIAL_QUESTION_TYPES):
                    # These boxes are special.
                    if (question_type in special_boxes):
                        raise ValueError(f"Multiple {question_type} bounding boxes found.")

                    special_boxes[question_type] = {
                        'page_number': page_number,
                        'x1': x1,
                        'y1': y1,
                        'x2': x2,
                        'y2': y2,
                    }

                    continue

                if (question_id not in boxes):
                    boxes[question_id] = {}

                # If there is an existing box, extend it.
                if (part_id in boxes[question_id]):
                    old_box = boxes[question_id][part_id]

                    old_x1 = old_box['x1']
                    old_y1 = old_box['y1']
                    old_x2 = old_box['x2']
                    old_y2 = old_box['y2']

                    old_page = old_box['page_number']
                    if (old_page != page_number):
                        raise ValueError(f"Question {question_id} has bounding boxes that span pages.")

                    x1 = min(x1, old_x1)
                    y1 = min(y1, old_y1)
                    x2 = max(x2, old_x2)
                    y2 = max(y2, old_y2)

                boxes[question_id][part_id] = {
                    'page_number': page_number,
                    'x1': x1,
                    'y1': y1,
                    'x2': x2,
                    'y2': y2,
                }

        return boxes, special_boxes

    def _compute_box(self,
            raw_ll_x: str,
            raw_ll_y: str,
            raw_ur_x: str,
            raw_ur_y: str,
            raw_page_width: str,
            raw_page_height: str,
            extend_box_right: bool = False,
            ) -> typing.Tuple[typing.Tuple[float, float], typing.Tuple[float, float]]:
        """ Compute a bounding box. """

        ll_x = float(raw_ll_x.removesuffix('sp'))
        ll_y = float(raw_ll_y.removesuffix('sp'))
        ur_x = float(raw_ur_x.removesuffix('sp'))
        ur_y = float(raw_ur_y.removesuffix('sp'))

        page_width = float(raw_page_width.removesuffix('pt')) * SP_PER_PT
        page_height = float(raw_page_height.removesuffix('pt')) * SP_PER_PT

        # Origin is upper-left, point 1 is upper-left, point 2 is lower-right.
        x1 = round(100.0 * (ll_x / page_width), 1)
        y1 = round(100.0 * (1.0 - (ur_y / page_height)), 1)
        # The lower right x should always extend (at least) to the end of the page (to capture the answers).
        x2 = round(100.0 * (ur_x / page_width), 1)
        y2 = round(100.0 * (1.0 - (ll_y / page_height)), 1)

        if (extend_box_right):
            # In some question types, we want to extend (at least) to the end of the page (to capture the answers).
            x2 = max(95.0, x2)

        return (x1, y1), (x2, y2)

    def create_outline(self,
            variant: quizcomp.variant.Variant,
            bounding_boxes: typing.Dict[str, typing.Dict[str, typing.Any]],
            special_boxes: typing.Dict[str, typing.Dict[str, typing.Any]],
            ) -> typing.Dict[str, typing.Any]:
        """ Create GradeScope outline data. """

        question_data = []
        for (question_id, parts) in bounding_boxes.items():
            question_index = int(float(question_id))

            if (len(parts) == 1):
                # Single-part question.
                question_data.append({
                    'title': variant.questions[question_index].name,
                    'weight': variant.questions[question_index].points,
                    'crop_rect_list': list(parts.values()),
                })
            else:
                # Multi-part question.
                children = []
                for (part_id, box) in parts.items():
                    children.append({
                        'title': f"{variant.questions[question_index].name} - {part_id}",
                        'weight': round(variant.questions[question_index].points / len(parts), 2),
                        'crop_rect_list': [box],
                    })

                question_data.append({
                    'title': variant.questions[question_index].name,
                    'weight': variant.questions[question_index].points,
                    # The top-level question just needs one of the bounding boxes.
                    'crop_rect_list': [list(parts.values())[0]],
                    'children': children,
                })

        name_box = None
        id_box = None

        for (question_type, box) in special_boxes.items():
            if (question_type == NAME_BOX_ID):
                name_box = special_boxes[NAME_BOX_ID]
            elif (question_type == ID_BOX_ID):
                id_box = special_boxes[ID_BOX_ID]
            else:
                question_data.append({
                    'title': question_type,
                    'weight': 0,
                    'crop_rect_list': [box],
                })

        outline = {
            'assignment': {
                'identification_regions': {
                    'name': name_box,
                    'sid': id_box
                }
            },
            'question_data': question_data,
        }

        return outline

    def upload(self,
            variant: quizcomp.variant.Variant,
            base_dir: str,
            bounding_boxes: typing.Dict[str, typing.Dict[str, typing.Any]],
            special_boxes: typing.Dict[str, typing.Dict[str, typing.Any]],
            ) -> typing.Tuple[str, bool]:
        """ Upload a variant. """

        path = os.path.join(base_dir, f"{variant.title}.pdf")
        if (not os.path.exists(path)):
            raise ValueError(f"Could not find path for quiz pdf: '{path}'.")

        outline = self.create_outline(variant, bounding_boxes, special_boxes)

        session = requests.Session()

        self.login(session)
        logging.debug("Logged in as '%s'.", self.user)

        assignment_id = self.get_assignment_id(session, variant)
        if (assignment_id is not None):
            if (not self.force):
                logging.info("Assignment '%s' (%s) already exists. Skipping upload.", variant.title, assignment_id)
                return assignment_id, False

            self.delete_assignment(session, assignment_id)
            logging.debug("Deleted assignment: '%s'", assignment_id)

        assignment_id = self.create_assignment(session, variant, base_dir)
        logging.debug("Created assignment: '%s'", assignment_id)

        self.submit_outline(session, assignment_id, outline)
        logging.debug('Submitted outline.')

        if (self.rubric):
            self.create_rubric(session, assignment_id, variant)
            logging.debug('Created assignment rubric.')

        return assignment_id, True

    def login(self, session: requests.Session):
        """ Login to GradeScope. """

        token = self.get_authenticity_token(session, URL_HOMEPAGE, action = '/login')

        data = {
            'utf8': '✓',
            'session[email]': self.user,
            'session[password]': self.password,
            'session[remember_me]': 0,
            'commit': 'Log+In',
            'session[remember_me_sso]': 0,
            'authenticity_token': token,
        }

        # Login.
        response = session.post(URL_LOGIN, params = data)
        response.raise_for_status()

    def get_authenticity_token(self, session: requests.Session, url: str, action: typing.Union[str, None] = None) -> str:
        """ Get a token from GradeScope. """

        response = session.get(url)
        response.raise_for_status()

        document = bs4.BeautifulSoup(response.text, 'html.parser')

        form_selector = 'form'
        if (action is not None):
            form_selector = f"form[action='{action}']"

        auth_input = document.select(f"{form_selector} input[name='authenticity_token']")
        if (len(auth_input) != 1):
            raise ValueError(f"Did not find exactly one authentication token input, found {len(auth_input)}.")

        return str(auth_input[0].get('value'))

    def get_csrf_token(self, session: requests.Session, url: str) -> str:
        """ Get a CSRF token. """

        # Get outline submission csrf token.
        response = session.get(url)
        response.raise_for_status()

        document = bs4.BeautifulSoup(response.text, 'html.parser')
        return self.parse_csrf_token(document)

    def parse_csrf_token(self, document: bs4.BeautifulSoup) -> str:
        """ Parse a CSRF token from a page. """

        meta_tag = document.select('meta[name="csrf-token"]')
        if (len(meta_tag) != 1):
            raise ValueError(f"Did not find exactly one CSRF meta tag, found {len(meta_tag)}.")

        return str(meta_tag[0].get('content'))

    def get_assignment_id(self, session: requests.Session, variant: quizcomp.variant.Variant) -> typing.Union[str, None]:
        """ Get an assignment ID for the given variant, or None if there is no matching variant. """

        url = URL_ASSIGNMENTS % (self.course_id)

        response = session.get(url)
        response.raise_for_status()

        document = bs4.BeautifulSoup(response.text, 'html.parser')

        nodes = document.select('div[data-react-class="AssignmentsTable"]')
        if (len(nodes) != 1):
            raise ValueError(f"Did not find exactly one assignments table, found {len(nodes)}.")

        assignment_data = edq.util.json.loads(nodes[0].get('data-react-props'))

        for row in assignment_data['table_data']:
            if (row['type'] != 'assignment'):
                continue

            id = row['id'].strip().removeprefix('assignment_')
            name = row['title'].strip()

            if (name == variant.title):
                return id

        return None

    def delete_assignment(self, session: requests.Session, assignment_id: str):
        """ Delete an assignment from GradeScope. """

        form_url = URL_ASSIGNMENT_EDIT % (self.course_id, assignment_id)
        token = self.get_csrf_token(session, form_url)

        data = {
            '_method': 'delete',
            'authenticity_token': token,
        }

        delete_url = URL_ASSIGNMENT % (self.course_id, assignment_id)
        response = session.post(delete_url, data = data)
        response.raise_for_status()

    def create_assignment(self, session: requests.Session, variant: quizcomp.variant.Variant, base_dir: str) -> str:
        """ Create an assignment in GradeScope and get its ID. """

        form_url = URL_NEW_ASSIGNMENT_FORM % (self.course_id)
        token = self.get_csrf_token(session, form_url)

        data = {
            'authenticity_token': token,
            'assignment[title]': variant.title,
            'assignment[submissions_anonymized]': 0,
            'assignment[student_submission]': "false",
            'assignment[when_to_create_rubric]': 'while_grading',
            'assignment[scoring_type]': 'negative',
        }

        path = os.path.join(base_dir, f"{variant.title}.pdf")
        files = {
            'template_pdf': (
                os.path.basename(path),
                open(path, 'rb'),  # pylint: disable=consider-using-with
            ),
        }

        create_url = URL_ASSIGNMENTS % (self.course_id)
        response = session.post(create_url, data = data, files = files)
        response.raise_for_status()

        if (len(response.history) == 0):
            raise ValueError(f"Failed to create assignment. Is the name ('{variant.title}') unique?")

        match = re.search(r'/assignments/(\d+)/outline/edit', response.history[0].text)
        if (match is None):
            logging.error("--- Create Body ---\n%s\n------", response.history[0].text)
            raise ValueError("Could not parse assignment ID from response body.")

        return match.group(1)

    def submit_outline(self, session: requests.Session, assignment_id: str, outline: typing.Dict[str, typing.Any]) -> None:
        """ Submit an output to a quiz. """

        edit_url = URL_EDIT_OUTLINE % (self.course_id, assignment_id)
        csrf_token = self.get_csrf_token(session, edit_url)

        headers = {
            'Content-Type': 'application/json',
            'x-csrf-token': csrf_token,
        }

        patch_outline_url = URL_PATCH_OUTLINE % (self.course_id, assignment_id)
        response = session.patch(patch_outline_url,
            data = edq.util.json.dumps(outline, separators = (',', ':')),
            headers = headers,
        )
        response.raise_for_status()

    def create_rubric(self, session: requests.Session, assignment_id: str, variant: quizcomp.variant.Variant) -> None:
        """ Create rubric items for a quiz. """

        questions_ids, csrf_token = self.fetch_question_ids(session, assignment_id)

        for question in variant.questions:
            if (question.name not in questions_ids):
                continue

            question_ids = questions_ids[question.name]
            score = round(question.points / len(question_ids), 2)

            for question_id in question_ids:
                self.add_rubric_item(session, csrf_token, question_id, "Incorrect", score)

    def add_rubric_item(self, session: requests.Session, csrf_token: str, question_id: str, description: str, score: float) -> None:
        """ Add a single rubric item to a quiz. """

        url = URL_ASSIGNMENT_ADD_RUBRIC_ITEM % (self.course_id, question_id)

        headers = {
            'Content-Type': 'application/json',
            'x-csrf-token': csrf_token,
        }

        data = {
            "rubric_item":{
                "description": description,
                "weight": str(score),
                "group_id": None,
            },
        }

        response = session.post(url, json = data, headers = headers)
        response.raise_for_status()

    def fetch_question_ids(self, session: requests.Session, assignment_id: str) -> typing.Tuple[typing.Dict[str, typing.List[str]], str]:
        """
        Get the GradeScope id of all questions/subquestions.

        Returns: {<question base name>: [question id, ...], ...}
        """

        url = URL_ASSIGNMENT_RUBRIC % (self.course_id, assignment_id)

        response = session.get(url)
        response.raise_for_status()

        document = bs4.BeautifulSoup(response.text, 'html.parser')

        csrf_token = self.parse_csrf_token(document)

        data_tag = document.select('div[data-react-class="AssignmentRubric"]')
        if (len(data_tag) != 1):
            raise ValueError(f"Did not find exactly one rubric data tag, found {len(data_tag)}.")

        data = edq.util.json.loads(str(data_tag[0].get('data-react-props')))

        ids = {}
        for question in data['questions']:
            question_ids = []

            children = question.get('children', None)
            if (children is None):
                question_ids.append(str(question['id']))
            else:
                question_ids = [str(child['id']) for child in children]

            ids[question['title']] = question_ids

        return ids, csrf_token
