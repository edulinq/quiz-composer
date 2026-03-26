import os
import re
import typing

import edq.util.dirent
import edq.util.json
import markdown_it.token

import quizcomp.constants
import quizcomp.parser.ast
import quizcomp.parser.render
import quizcomp.parser.common

class ParsedDocument(edq.util.serial.PODConverter):
    """ The result of parsing some text. """

    def __init__(self,
            text: typing.Union[str, None] = None,
            tokens: typing.Union[typing.List[markdown_it.token.Token], None] = None,
            base_dir: typing.Union[str, None] = None,
            ) -> None:
        if (base_dir is None):
            base_dir = '.'

        if (text is None):
            text = ''

        if (tokens is None):
            tokens = []

        if ((len(text) == 0) and (len(tokens) > 0)):
            raise ValueError(f"Cannot create a document that contains tokens, but not text: {tokens}.")

        if ((len(text) > 0) and (len(tokens) == 0)):
            text, tokens = quizcomp.parser.render._parse_text(text, base_dir)

        self.text: str = text
        """ The cleaned text that was parsed to create this document. """

        self._tokens: typing.List[markdown_it.token.Token] = tokens
        """ The tokens that were parsed from the starting text. """

        # TEST - Remove
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

    def is_empty(self) -> bool:
        """ Check if this document contains any content (tokens). """

        return (len(self._tokens) == 0)

    def to_json(self, indent: int = 4, sort_keys: bool = True, **kwargs: typing.Any) -> str:
        """ Convert this document to JSON. """

        return edq.util.json.dumps(self.to_pod(**kwargs), indent = indent, sort_keys = sort_keys)

    def to_format(self, format: str, **kwargs: typing.Any) -> str:
        """ Convert this document to the specified format. """

        formatter = getattr(self, 'to_' + format)
        if (formatter is None):
            raise ValueError(f"Unknown format '{format}'.")

        return str(formatter(**kwargs))

    def get_ast(self) -> quizcomp.parser.ast.ASTNode:
        """
        Get a representation of this document's AST.
        """

        return quizcomp.parser.ast.build(self._tokens)

    def __repr__(self) -> str:
        return self.text

    def to_pod(self,
            serialization_options: typing.Union[typing.Dict[str, typing.Any], None] = None,
            # TEST
            # ) -> edq.util.serial.PODType:
            ) -> str:
        return self.text

    @classmethod
    def parse_text(cls, text: str, base_dir: typing.Union[str, None] = None) -> 'ParsedDocument':
        """ Parse some text into a document. """

        if (base_dir is None):
            base_dir = '.'

        text, tokens = quizcomp.parser.render._parse_text(text, base_dir)
        return quizcomp.parser.document.ParsedDocument(text, tokens, base_dir = base_dir)

    @classmethod
    def parse_file(cls, raw_path: str, base_dir: typing.Union[str, None] = None) -> 'ParsedDocument':
        """ Parse a text file into a document. """

        if (base_dir is None):
            base_dir = '.'

        # Prepend the base dir if the path is not absolute.
        if (not os.path.isabs(raw_path)):
            raw_path = os.path.join(base_dir, raw_path)

        path = os.path.abspath(raw_path)

        if (not os.path.isfile(path)):
            raise ValueError(f"Path to parse ('{raw_path}') does not exist or is not a file.")

        text = edq.util.dirent.read_file(path)
        base_dir = os.path.dirname(path)

        return cls.parse_text(text, base_dir = base_dir)
