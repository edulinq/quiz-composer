"""
CLI entrypoint for uploading quizzes to Google Forms.

Usage:
    python -m quizcomp.cli.google_forms.upload <path> --credentials <credentials.json>

This is a stub implementation. Full functionality will be added in Milestone 2.
"""

import sys

def _get_parser():
    """Return the argument parser for the google-forms upload CLI.

    Arguments (to be wired up in Milestone 2):
        path             - path to quiz.json
        --credentials    - path to credentials.json (OAuth client secret or SA key)
        --token          - path to cached OAuth token (default: token.json)
        --force          - delete and re-create an existing form with the same title
        --service-account - use service account auth instead of OAuth 2.0
    """
    import argparse
    parser = argparse.ArgumentParser(
        description='Parse a quiz and upload it to Google Forms. [STUB – not yet implemented]')

    parser.add_argument('path', metavar='PATH',
        type=str,
        help='The path to a quiz json file.')

    parser.add_argument('--credentials', dest='credentials',
        action='store', type=str, required=False, default=None,
        help='Path to Google API credentials.json (OAuth client secret or service account key).')

    parser.add_argument('--token', dest='token',
        action='store', type=str, required=False, default='token.json',
        help='Path to cached OAuth token file (default: %(default)s).')

    parser.add_argument('--force', dest='force',
        action='store_true', default=False,
        help='Delete and re-create any existing form with the same title.')

    parser.add_argument('--service-account', dest='service_account',
        action='store_true', default=False,
        help='Use service account authentication instead of OAuth 2.0.')

    return parser

def run(args):
    """Stub run() – full implementation coming in Milestone 2."""
    print("Not yet implemented: Google Forms upload is under development.")
    return 0

def main():
    args = _get_parser().parse_args()
    return run(args)

if (__name__ == '__main__'):
    sys.exit(main())
