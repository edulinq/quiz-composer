"""
The `quizcomp.cli` package contains tools for running the quizcomp.
Each package can be invoked to list the tools (or subpackages) it contains.
Each tool includes a help prompt that accessed with the `-h`/`--help` flag.
"""

import sys

import quizcomp.util.cli

def main():
    return quizcomp.util.cli.main()

if (__name__ == '__main__'):
    sys.exit(main())
