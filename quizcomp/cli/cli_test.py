import os

import edq.testing.cli

import quizcomp.testing.base

THIS_DIR: str = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
ROOT_DIR: str = os.path.join(THIS_DIR, '..', '..')

CLI_TESTDATA_DIR: str = os.path.join(ROOT_DIR, 'quizcomp', 'cli', 'testdata')
CLI_TESTS_DIR: str = os.path.join(CLI_TESTDATA_DIR, 'tests')
CLI_DATA_DIR: str = os.path.join(CLI_TESTDATA_DIR, 'data')

class CLITest(quizcomp.testing.base.BaseTest):
    """
    CLI tests.
    """

    @classmethod
    def get_test_basename(cls, path: str) -> str:
        """ Get the test's name based off of its filename and location. """

        return edq.testing.cli.compute_ancestor_basename(path, CLI_TESTS_DIR)


# Attach CLI tests.
edq.testing.cli.discover_test_cases(CLITest, CLI_TESTS_DIR, CLI_DATA_DIR)
