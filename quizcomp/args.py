"""
A place to handle common CLI arguments.
"parsers" in this file are always assumed to be argparse parsers.

The general idea is that callers can register callbacks to be called before and after parsing CLI arguments.
Pre-callbacks are generally intended to add arguments to the parser,
while post-callbacks are generally intended to act on the results of parsing.

Common args are registered at the bottom.
"""

import argparse

# Import modules that have common args to ensure they are loaded.
import quizcomp.katex
import quizcomp.latex
import quizcomp.log

# {module name: function(parser), ...}
_pre = {}

# {module name: function(args), ...}
_post = {}

class Parser(argparse.ArgumentParser):
    """
    Extend an argparse parser to call the pre and post functions.
    """

    def parse_args(self, *args, skip_modules = [], **kwargs):
        pre_parse(self, skip_modules)
        args = super().parse_args(*args, **kwargs)
        post_parse(args, skip_modules)

        return args

def pre_parse(parser, skip_modules = []):
    return _run(parser, _pre, skip_modules)

def post_parse(args, skip_modules = []):
    return _run(args, _post, skip_modules)

def _run(payload, functions, skip_modules):
    for (module_name, callback) in functions.items():
        if (module_name in skip_modules):
            continue

        callback(payload)

    return payload

# Register args under a module name.
def register(module_name, pre_callback = None, post_callback = None):
    if (pre_callback is not None):
        _pre[module_name] = pre_callback

    if (post_callback is not None):
        _post[module_name] = post_callback

# Register common args.
register('log', quizcomp.log.set_cli_args, quizcomp.log.init_from_args)
register('katex', quizcomp.katex.set_cli_args, quizcomp.katex.init_from_args)
register('latex', quizcomp.latex.set_cli_args, quizcomp.latex.init_from_args)
