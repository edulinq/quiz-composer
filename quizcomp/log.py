import logging

DEFAULT_LOGGING_LEVEL = logging.getLevelName(logging.INFO)
DEFAULT_LOGGING_FORMAT = '%(asctime)s [%(levelname)-8s] - %(filename)s:%(lineno)s -- %(message)s'

LEVELS = [
    logging.getLevelName(logging.DEBUG),
    logging.getLevelName(logging.INFO),
    logging.getLevelName(logging.WARNING),
    logging.getLevelName(logging.ERROR),
    logging.getLevelName(logging.CRITICAL),
]

def init(level = DEFAULT_LOGGING_LEVEL, format = DEFAULT_LOGGING_FORMAT, **kwargs):
    """
    Initialize or re-initialize the logging infrastructure.
    """

    logging.basicConfig(level = level, format = format, force = True)

    # Ignore logging from third-party libraries.
    logging.getLogger("git").setLevel(logging.WARNING)
    logging.getLogger("markdown_it").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def set_cli_args(parser):
    """
    Set common logging args in an argparse parser.
    """

    parser.add_argument('--log-level', dest = 'log_level',
        action = 'store', type = str, default = logging.getLevelName(logging.INFO),
        choices = LEVELS,
        help = 'The logging level (default: %(default)s).')

    return parser

def init_from_args(args):
    """
    Take in args from a parser that was passed to set_cli_args(),
    and call init() with the appropriate arguments.
    """

    init(args.log_level)

    return args

# Load the default logging when this module is loaded.
init()
