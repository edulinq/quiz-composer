import copy
import os
import re
import types
import typing

import edq.util.json

import quizcomp.constants
import quizcomp.parser.ast
import quizcomp.parser.render
import quizcomp.parser.common

class ParsedDocument(object):
    def __init__(self,
            tokens: typing.Union[typing.List, None] = None,
            base_dir: str = '.',
            ) -> None:
        if (tokens is None):
            tokens = []

        self._tokens: typing.List = tokens

        self._context = {
            quizcomp.parser.common.BASE_DIR_KEY: base_dir,
        }

    def set_context_value(self, key, value):
        self._context[key] = value

    def to_canvas(self, **kwargs):
        return self._render(quizcomp.constants.FORMAT_CANVAS, **kwargs)

    def to_md(self, **kwargs):
        return self._render(quizcomp.constants.FORMAT_MD, **kwargs)

    def to_tex(self, **kwargs):
        return self._render(quizcomp.constants.FORMAT_TEX, **kwargs)

    def to_text(self, **kwargs):
        return self._render(quizcomp.constants.FORMAT_TEXT, **kwargs)

    def to_html(self, **kwargs):
        return self._render(quizcomp.constants.FORMAT_HTML, **kwargs)

    def _render(self, format, **kwargs):
        context = quizcomp.parser.common.prep_context(self._context, options = kwargs)
        env = {quizcomp.parser.common.CONTEXT_ENV_KEY: context}
        return quizcomp.parser.render.render(format, self._tokens, env = env, **kwargs)

    def to_pod(self, include_metadata = True, **kwargs):
        data = {
            'type': 'document',
            'ast': self.get_ast(),
        }

        if (include_metadata):
            data["context"] = self._context

        return data

    def collect_placeholders(self):
        """
        Fetch all the answer placeholders in this document.
        """

        return set(self._collect_placeholders_helper(self._tokens))

    def _collect_placeholders_helper(self, tokens):
        placeholders = []

        if ((tokens is None) or (len(tokens) == 0)):
            return placeholders

        for token in tokens:
            if (token.type == 'placeholder'):
                placeholders.append(token.content)

            placeholders += self._collect_placeholders_helper(token.children)

        return placeholders

    def collect_file_paths(self, base_dir):
        """
        Fetch all the file paths in this document.
        """

        return set(self._collect_file_paths_helper(self._tokens, base_dir))

    def _collect_file_paths_helper(self, tokens, base_dir):
        file_paths = []

        if ((tokens is None) or (len(tokens) == 0)):
            return file_paths

        for token in tokens:
            if (token.type == 'image'):
                src = token.attrGet('src')
                if ((not re.match(r'^http(s)?://', src)) and (not src.startswith('data:image'))):
                    file_paths.append(os.path.realpath(os.path.join(base_dir, src)))

            file_paths += self._collect_file_paths_helper(token.children, base_dir)

        return file_paths

    def is_empty(self):
        return (len(self._tokens) == 0)

    def to_json(self, indent = 4, sort_keys = True, **kwargs):
        return edq.util.json.dumps(self.to_pod(**kwargs), indent = indent, sort_keys = sort_keys)

    def to_format(self, format, **kwargs):
        formatter = getattr(self, 'to_' + format)
        if (formatter is None):
            raise ValueError(f"Unknown format '{format}'.")

        return formatter(**kwargs)

    def get_ast(self):
        """
        Get a represetation of this document's AST.
        """

        return quizcomp.parser.ast.build(self._tokens)
