import datetime
import logging
import os
import random

import quizcomp.common
import quizcomp.constants
import quizcomp.group
import quizcomp.parser.public
import quizcomp.uploader.canvas
import quizcomp.util.dirent
import quizcomp.util.git
import quizcomp.util.serial

class Quiz(quizcomp.util.serial.JSONSerializer):
    """
    A quiz object represents multiple possible assesments (called "variants").
    """

    def __init__(self, type = quizcomp.constants.TYPE_QUIZ,
            title = '',
            course_title = '', term_title = '',
            description = '', date = '',
            time_limit_mins = None,
            shuffle_answers = True, pick_with_replacement = True,
            groups = [],
            base_dir = '.',
            version = None, seed = None,
            canvas = {},
            ids = {},
            **kwargs):
        super().__init__(**kwargs)

        self.title = title
        self.course_title = course_title
        self.term_title = term_title
        self.date = date

        self.description = description

        self.time_limit_mins = time_limit_mins

        self.shuffle_answers = shuffle_answers
        self.pick_with_replacement = pick_with_replacement

        self.groups = groups

        self.base_dir = base_dir
        self.version = version

        self.seed = seed
        if (self.seed is None):
            self.seed = random.randint(0, 2**64)
        self._rng = random.Random(self.seed)

        self.canvas = canvas.copy()

        try:
            self.validate(cls = Quiz, **kwargs)
        except Exception as ex:
            ids = ids.copy()
            ids['title'] = self.title

            raise quizcomp.common.QuizValidationError('Error while validating quiz.', ids = ids) from ex

    def _validate(self, **kwargs):
        if ((self.title is None) or (self.title == "")):
            raise quizcomp.common.QuizValidationError("Title cannot be empty.")

        if ((self.description is None) or (self.description == "")):
            raise quizcomp.common.QuizValidationError("Description cannot be empty.")
        self.description = quizcomp.parser.public.parse_text(self.description, base_dir = self.base_dir)

        if (self.version is None):
            self.version = quizcomp.util.git.get_version(self.base_dir, throw = False)
            if (self.version == quizcomp.util.git.UNKNOWN_VERSION):
                logging.warning("Could not get a version for the quiz (is it in a git repo?).")

        self.canvas = quizcomp.uploader.canvas.validate_options(self.canvas)

        self._validate_time_limit()

        if (self.date == ''):
            self.date = datetime.date.today()
        elif (isinstance(self.date, str)):
            self.date = datetime.date.fromisoformat(self.date)
        else:
            raise quizcomp.common.QuizValidationError("Date should be a string or datetime.date, found '%s'." % (str(type(self.date))))

        for key in kwargs:
            logging.warning("Unknown quiz option: '%s'." % (key))

    def _validate_time_limit(self):
        if (self.time_limit_mins is None):
            return

        if (not isinstance(self.time_limit_mins, (str, int))):
            raise quizcomp.common.QuizValidationError("Time limit must be a positive int, found '%s'." % (str(self.time_limit_mins)))

        try:
            self.time_limit_mins = int(self.time_limit_mins)
        except:
            raise quizcomp.common.QuizValidationError("Time limit must be a positive int, found '%s'." % (str(self.time_limit_mins)))

        if (self.time_limit_mins < 0):
            raise quizcomp.common.QuizValidationError("Time limit must be a positive int, found '%s'." % (str(self.time_limit_mins)))

        if (self.time_limit_mins == 0):
            self.time_limit_mins = None

    @classmethod
    def from_path(cls, path, **kwargs):
        # Check for a description file.
        def _check_description_file(path, data):
            description_filename = os.path.splitext(os.path.basename(path))[0]
            description_path = os.path.join(os.path.dirname(path), description_filename + '.md')
            if (os.path.exists(description_path)):
                data['description'] = quizcomp.util.dirent.read_file(description_path)
                logging.debug("Loading quiz description from '%s'.", description_path)

            return data

        return super().from_path(path, data_callback = _check_description_file, **kwargs)

    @staticmethod
    def from_dict(quiz_info, base_dir = None, flatten_groups = False, ids = {}, **kwargs):
        groups = []
        group_infos = quiz_info.get('groups', [])
        for i in range(len(group_infos)):
            ids = ids.copy()
            ids['index'] = i
            groups.append(quizcomp.group.Group.from_dict(group_infos[i], base_dir, ids = ids))

        if (flatten_groups):
            new_groups = []

            for old_group in groups:
                for i in range(len(old_group.questions)):
                    info = {
                        'name': old_group.name,
                        'pick_count': 1,
                        'points': old_group.points,
                        'questions': [old_group.questions[i]],
                    }

                    new_groups.append(quizcomp.group.Group(**info))

            groups = new_groups

        quiz_info['groups'] = groups

        if (base_dir is not None):
            quiz_info['base_dir'] = base_dir
        elif ('base_dir' not in quiz_info):
            quiz_info['base_dir'] = '.'

        return Quiz(**quiz_info, ids = ids)

    def num_questions(self):
        count = 0

        for group in self.groups:
            count += group.pick_count

        return count

    def create_variant(self, identifier = None, seed = None, all_questions = False):
        if (seed is None):
            seed = self._rng.randint(0, 2**64)

        logging.debug("Creating variant with seed %s.", str(seed))
        rng = random.Random(seed)

        new_groups = []
        for group in self.groups:
            questions = group.choose_questions(all_questions = all_questions, rng = rng,
                    with_replacement = self.pick_with_replacement)

            group_data = group.__dict__.copy()
            group_data['questions'] = questions
            # Skip validation.
            group_data['_skip_all_validation'] = True

            new_groups.append(quizcomp.group.Group(**group_data))

        if (self.shuffle_answers):
            for group in new_groups:
                for question in group.questions:
                    question.shuffle(rng)

        title = self.title
        version = self.version

        if (identifier is not None):
            title = "%s - %s" % (title, identifier)
            version = "%s, Variant: %s" % (version, identifier)

        data = self.__dict__.copy()

        data['title'] = title
        data['version'] = version
        data['seed'] = seed
        data['groups'] = new_groups

        # Skip quiz validation.
        data['_skip_class_validations'] = [Quiz]

        return quizcomp.variant.Variant(**data)
    
    def total_points(self):
        """
        Calculate the total points for the quiz based on question groups.
        """

        total = 0

        for group in self.groups:
            total += group.pick_count * group.points

        return total