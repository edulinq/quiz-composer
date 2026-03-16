import copy
import os
import re
import typing

import edq.util.json
import markdown_it.token

import quizcomp.constants
import quizcomp.parser.ast
import quizcomp.parser.render
import quizcomp.parser.common

class ParsedDocument:
    """ The result of parsing some text. """

    def __init__(self,
            tokens: typing.List[markdown_it.token.Token],
            base_dir: str = '.',
            ) -> None:
        self._tokens: typing.List[markdown_it.token.Token] = tokens
        """ The tokens that were parsed from the starting text. """

        self._context: typing.Dict[str, str] = {
            quizcomp.parser.common.BASE_DIR_KEY: base_dir,
        }
        """ Context information for this document. """

    def set_context_value(self, key: str, value: typing.Any) -> None:
        """ Set a context value for this document. """

        self._context[key] = value

    def to_canvas(self, **kwargs: typing.Any) -> str:
        """ Render this document to Canvas-specific HTML. """

        return self._render(quizcomp.constants.FORMAT_CANVAS, **kwargs)

    def to_md(self, **kwargs: typing.Any) -> str:
        """ Render this document to Markdown. """

        return self._render(quizcomp.constants.FORMAT_MD, **kwargs)

    def to_tex(self, **kwargs: typing.Any) -> str:
        """ Render this document to TeX. """

        return self._render(quizcomp.constants.FORMAT_TEX, **kwargs)

    def to_text(self, **kwargs: typing.Any) -> str:
        """ Render this document to simple text. """

        return self._render(quizcomp.constants.FORMAT_TEXT, **kwargs)

    def to_html(self, **kwargs: typing.Any) -> str:
        """ Render this document to HTML. """

        return self._render(quizcomp.constants.FORMAT_HTML, **kwargs)

    def _render(self, format: str, **kwargs: typing.Any) -> str:
        """ Render this document to the specified format. """

        context = quizcomp.parser.common.prep_context(self._context, options = kwargs)
        env = {quizcomp.parser.common.CONTEXT_ENV_KEY: context}
        return quizcomp.parser.render.render(format, self._tokens, env = env, **kwargs)

    def to_pod(self, include_metadata: bool = True, **kwargs: typing.Any) -> typing.Dict[str, typing.Any]:
        """ Convert this document to a dict that contains only simple types. """

        data = {
            'type': 'document',
            'ast': self.get_ast(),
        }

        if (include_metadata):
            data["context"] = self._context

        return data

    def collect_placeholders(self) -> typing.Set[str]:
        """
        Fetch all the answer placeholders in this document.
        """

        return set(self._collect_placeholders_helper(self._tokens))

    def _collect_placeholders_helper(self, tokens: typing.Union[typing.List[markdown_it.token.Token], None]) -> typing.List[str]:
        """ Collect the placeholder in a sequence of tokens. """

        if ((tokens is None) or (len(tokens) == 0)):
            return []

        placeholders: typing.List[str] = []

        if ((tokens is None) or (len(tokens) == 0)):
            return placeholders

        for token in tokens:
            if (token.type == 'placeholder'):
                placeholders.append(token.content)

            placeholders += self._collect_placeholders_helper(token.children)

        return placeholders

    def collect_file_paths(self, base_dir: str) -> typing.Set[str]:
        """
        Fetch all the file paths in this document.
        """

        return set(self._collect_file_paths_helper(self._tokens, base_dir))

    def _collect_file_paths_helper(self, tokens: typing.Union[typing.List[markdown_it.token.Token], None], base_dir: str) -> typing.List[str]:
        """ Collect the file paths in a sequence of tokens. """

        if ((tokens is None) or (len(tokens) == 0)):
            return []

        file_paths: typing.List[str] = []

        if ((tokens is None) or (len(tokens) == 0)):
            return file_paths

        for token in tokens:
            if (token.type == 'image'):
                src = str(token.attrGet('src'))
                if ((not re.match(r'^http(s)?://', src)) and (not src.startswith('data:image'))):
                    file_paths.append(os.path.realpath(os.path.join(base_dir, src)))

            file_paths += self._collect_file_paths_helper(token.children, base_dir)

        return file_paths

    def is_empty(self) -> bool:
        return (len(self._tokens) == 0)

    def to_json(self, indent: int = 4, sort_keys: bool = True, **kwargs: typing.Any) -> str:
        """ Convert this document to JSON. """

        return edq.util.json.dumps(self.to_pod(**kwargs), indent = indent, sort_keys = sort_keys)

    def to_format(self, format: str, **kwargs: typing.Any) -> str:
        """ Convert this document to the specified format. """

        formatter = getattr(self, 'to_' + format)
        if (formatter is None):
            raise ValueError(f"Unknown format '{format}'.")

        return formatter(**kwargs)

    def get_ast(self) -> quizcomp.parser.ast.ASTNode:
        """
        Get a representation of this document's AST.
        """

        return quizcomp.parser.ast.build(self._tokens)
