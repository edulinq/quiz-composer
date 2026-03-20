"""
Upload quizzes to Google Forms.

This module provides the GoogleFormsUploader class and supporting utilities
for exporting QuizComp quizzes to Google Forms using the Google Forms API v1.

References:
    https://developers.google.com/forms/api/reference/rest
"""

import logging

import quizcomp.common
import quizcomp.constants

# ---------------------------------------------------------------------------
# OAuth 2.0 scopes required by this uploader.
# ---------------------------------------------------------------------------
SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
]

# ---------------------------------------------------------------------------
# Maps QuizComp question types to Google Forms API item types.
# Types that map to None require special expansion logic (multiple items).
# ---------------------------------------------------------------------------
QUESTION_TYPE_MAP = {
    # Direct mappings
    quizcomp.constants.QUESTION_TYPE_MCQ:       'RADIO',
    quizcomp.constants.QUESTION_TYPE_TF:        'RADIO',
    quizcomp.constants.QUESTION_TYPE_MA:        'CHECKBOX',
    quizcomp.constants.QUESTION_TYPE_FITB:      'SHORT_ANSWER',
    quizcomp.constants.QUESTION_TYPE_SA:        'PARAGRAPH',
    quizcomp.constants.QUESTION_TYPE_ESSAY:     'PARAGRAPH',
    quizcomp.constants.QUESTION_TYPE_NUMERICAL: 'SHORT_ANSWER',
    quizcomp.constants.QUESTION_TYPE_TEXT_ONLY: 'TEXT',
    # Expanded types – handled specially (one QuizComp question → N Google Forms items)
    quizcomp.constants.QUESTION_TYPE_FIMB:      None,  # expands to N SHORT_ANSWER
    quizcomp.constants.QUESTION_TYPE_MDD:       None,  # expands to N RADIO
    quizcomp.constants.QUESTION_TYPE_MATCHING:  None,  # GRID or N RADIO
}

# ---------------------------------------------------------------------------
# Default values for the google_forms quiz.json options block.
# ---------------------------------------------------------------------------
DEFAULT_GOOGLE_FORMS_OPTIONS = {
    'published':              True,
    'shuffle_questions':      False,
    'collect_email':          False,
    'one_response_per_user':  False,
    'matching_style':         'grid',  # 'grid' or 'radio'
}

# Allowed values for boolean/enum options (used by validate_options).
ALLOWED_VALUES = {
    'published':              [True, False],
    'shuffle_questions':      [True, False],
    'collect_email':          [True, False],
    'one_response_per_user':  [True, False],
    'matching_style':         ['grid', 'radio'],
}

# ---------------------------------------------------------------------------
# Options validation (called by quiz.py during Quiz._validate)
# ---------------------------------------------------------------------------

def validate_options(old_options):
    """Validate and normalise the google_forms options dict from quiz.json.

    Merges caller-supplied options with DEFAULT_GOOGLE_FORMS_OPTIONS, warns
    on unknown keys, and raises QuizValidationError for invalid values.

    Args:
        old_options (dict): The raw google_forms dict from quiz.json.

    Returns:
        dict: Validated and normalised options dict.

    Raises:
        quizcomp.common.QuizValidationError: If any option has an invalid value.
    """
    options = DEFAULT_GOOGLE_FORMS_OPTIONS.copy()
    options.update(old_options)

    for (key, value) in options.items():
        if (key not in DEFAULT_GOOGLE_FORMS_OPTIONS):
            logging.warning("Unknown google_forms option: '%s'.", key)
            continue

        if (key in ALLOWED_VALUES):
            if (value not in ALLOWED_VALUES[key]):
                raise quizcomp.common.QuizValidationError(
                    "Google Forms option '%s' has value '%s' not in allowed values: %s."
                    % (key, value, ALLOWED_VALUES[key]))

    return options

# ---------------------------------------------------------------------------
# Uploader class (stub – full implementation in Milestones 2–5)
# ---------------------------------------------------------------------------

class GoogleFormsUploader:
    """Uploads a QuizComp Quiz to Google Forms via the Google Forms API v1.

    Authentication is handled via OAuth 2.0 (default) or a service account.
    Full implementation will be added in Milestone 2.
    """

    def __init__(self, credentials_path, token_path=None, force=False,
                 use_service_account=False, **kwargs):
        """Initialise the uploader.

        Args:
            credentials_path (str): Path to credentials.json (OAuth client
                secret file or service account key file).
            token_path (str | None): Path to the cached OAuth token file.
                Defaults to 'token.json' in the current directory.
            force (bool): When True, delete any existing form with the same
                title before creating a new one.
            use_service_account (bool): When True, use service account
                credentials instead of OAuth 2.0.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path or 'token.json'
        self.force = force
        self.use_service_account = use_service_account
        self._service = None  # Lazily initialised in _build_service()

    # ------------------------------------------------------------------
    # Stub methods – full bodies added in Milestones 2–5
    # ------------------------------------------------------------------

    def _build_service(self):
        """Build and cache the Google API service client. (Milestone 2)"""
        raise NotImplementedError("Authentication not yet implemented (Milestone 2).")

    def upload_quiz(self, quiz, **kwargs):
        """Upload *quiz* to Google Forms and return the result dict. (Milestone 3)"""
        raise NotImplementedError("upload_quiz not yet implemented (Milestone 3).")
