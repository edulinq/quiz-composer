import os

import quizcomp.util.dirent
import quizcomp.util.git
import tests.base

class TestGit(tests.base.BaseTest):
    def test_in_repo(self):
        # This test should live inside a repo.
        version = quizcomp.util.git.get_version(tests.base.TESTS_DIR)
        self.assertNotEqual(quizcomp.util.git.UNKNOWN_VERSION, version, 'Got an unknown version. (This can also happen if this instance of the quizcomp project is not in a git repo.')

    def test_cwd(self):
        # The tests should be run in a repo (this project repo).
        version = quizcomp.util.git.get_version()
        self.assertNotEqual(quizcomp.util.git.UNKNOWN_VERSION, version, 'Got an unknown version. (This can also happen if the tests are not being run inside of a git repo.')

    def test_not_in_repo(self):
        # A new temp dir should not be in a git repo.
        path = quizcomp.util.dirent.get_temp_path(prefix = 'quizcomp-test-git-')
        version = quizcomp.util.git.get_version(path)
        self.assertEqual(quizcomp.util.git.UNKNOWN_VERSION, version)
