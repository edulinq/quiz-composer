"""
The `quizcomp.cli.google_forms` package contains tools for uploading quizzes to Google Forms.
Invoke with: python -m quizcomp.cli.google_forms
"""

import sys

import quizcomp.cli.google_forms.upload

def main():
    return quizcomp.cli.google_forms.upload.main()

if (__name__ == '__main__'):
    sys.exit(main())
