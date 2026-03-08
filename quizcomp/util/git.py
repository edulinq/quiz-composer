import os

import git

UNKNOWN_VERSION = 'UNKNOWN'
VERSION_LEN = 8
DIRTY_SIFFIX = '-d'

def get_version(path = '.', throw = False):
    """
    Get a version string from the git repo.
    This is just a commit hash with some dressup.
    """

    if (os.path.isfile(path)):
        path = os.path.dirname(path)

    try:
        repo = git.Repo(path, search_parent_directories = True)
        version = repo.head.commit.tree.hexsha[:VERSION_LEN]
    except Exception as ex:
        if (throw):
            raise ValueError(f"Path '{path}' is not a valid Git repo.") from ex

        return UNKNOWN_VERSION

    if (repo.is_dirty()):
        version += DIRTY_SIFFIX

    return version
