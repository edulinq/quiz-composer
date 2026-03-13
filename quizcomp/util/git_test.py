import os

import edq.testing.unittest

import quizcomp.util.dirent
import quizcomp.util.git

THIS_DIR = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

class TestGit(edq.testing.unittest.BaseTest):
    """ Test git functionality. """

    def test_version_in_repo(self):
        """ Test getting a git version inside of a repo. """

        version = quizcomp.util.git.get_version(THIS_DIR)
        self.assertNotEqual(quizcomp.util.git.UNKNOWN_VERSION, version, 'Got an unknown version (assumes test is run in a repo).')

    def test_version_cwd(self):
        """ Test getting a git version using the current working directory. """

        version = quizcomp.util.git.get_version()
        self.assertNotEqual(quizcomp.util.git.UNKNOWN_VERSION, version, 'Got an unknown version (assumes test is run in a repo)')

    def test_version_not_in_repo(self):
        """ Test getting a git version when not inside of a repo. """

        path = quizcomp.util.dirent.get_temp_path(prefix = 'quizcomp-test-git-')
        version = quizcomp.util.git.get_version(path)
        self.assertEqual(quizcomp.util.git.UNKNOWN_VERSION, version)
