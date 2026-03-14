import os

import quizcomp.cli.gradescope.upload
import quizcomp.latex
import quizcomp.uploader.gradescope
import quizcomp.util.httpsession
import tests.base

SIMPLE_SESSION_NAME = 'gradescope-simple'
ALREADY_EXISTS_SESSION_NAME = 'gradescope-already-exists'
VARIANT_FORCE_RUBRIC_A_SESSION_NAME = 'gradescope-variant-force-rubric-a'
VARIANT_FORCE_RUBRIC_B_SESSION_NAME = 'gradescope-variant-force-rubric-b'
VARIANT_FORCE_RUBRIC_GROUP_SESSION_NAME = 'gradescope-variant-force-rubric-group'

TEST_COURSE = '100001'
TEST_USER = 'test@test.edulinq.org'
TEST_PASS = 'abc123'

class TestUploaderGradescope(tests.base.BaseTest):
    """
    Test uploading GradeScope quizzes using recorded HTTP sessions.
    """

    def _run_session_upload_test(self, session_infos, quiz_path, extra_args = []):
        if (not quizcomp.latex.is_available()):
            self.skipTest("LaTeX is not available.")

        for (session_id, session_dirname) in session_infos:
            session_base_dir = os.path.join(tests.base.HTTP_SESSIONS_DIR, session_dirname)

            quizcomp.util.httpsession.load_test_session(session_id, session_base_dir)

        temp_dir = edq.util.dirent.get_temp_dir('quizcomp-test-')

        raw_args = [
            '--log-level', 'ERROR',
            '--course', TEST_COURSE,
            '--user', TEST_USER,
            '--pass', TEST_PASS,
            '--out', temp_dir,
            quiz_path,
        ]

        raw_args += extra_args

        parser = quizcomp.cli.gradescope.upload._get_parser()
        args = parser.parse_args(raw_args)

        quizcomp.cli.gradescope.upload.run(args)

    def test_simple(self):
        session_infos = [
            (quizcomp.uploader.gradescope.SESSION_ID_UPLOAD, SIMPLE_SESSION_NAME),
        ]

        quiz_path = os.path.abspath(os.path.join(tests.base.GOOD_QUIZZES_DIR, 'single-question', 'quiz.json'))

        self._run_session_upload_test(session_infos, quiz_path)

    def test_already_exists(self):
        session_infos = [
            (quizcomp.uploader.gradescope.SESSION_ID_UPLOAD, ALREADY_EXISTS_SESSION_NAME),
        ]

        quiz_path = os.path.abspath(os.path.join(tests.base.GOOD_QUIZZES_DIR, 'single-question', 'quiz.json'))

        self._run_session_upload_test(session_infos, quiz_path)

    def test_variant_force_rubric(self):
        session_infos = [
            (quizcomp.uploader.gradescope.SESSION_ID_UPLOAD, VARIANT_FORCE_RUBRIC_A_SESSION_NAME),
            (quizcomp.uploader.gradescope.SESSION_ID_UPLOAD, VARIANT_FORCE_RUBRIC_B_SESSION_NAME),
            (quizcomp.uploader.gradescope.SESSION_ID_CREATE_ASSIGNMENT_GROUP, VARIANT_FORCE_RUBRIC_GROUP_SESSION_NAME),
        ]

        quiz_path = os.path.abspath(os.path.join(tests.base.GOOD_QUIZZES_DIR, 'single-question', 'quiz.json'))

        extra_args = [
            '--variants', '2',
            '--force',
            '--rubric',
        ]

        self._run_session_upload_test(session_infos, quiz_path, extra_args = extra_args)
