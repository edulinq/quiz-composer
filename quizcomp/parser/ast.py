import typing

import markdown_it.token
import markdown_it.tree

import quizcomp.parser.common

# Pull specific attributes from nodes of these specified types.
AST_NODE_ATTRIBUTES: typing.Dict[str, typing.List[str]] = {
    'code_block': [
        'info',
    ],
    'fence': [
        'info',
    ],
    'heading': [
        'tag',
    ],
}

# Pull these attributes out of these specific token types when building the AST.
AST_TOKEN_ATTRS: typing.Dict[str, typing.List[str]] = {
    'image': [
        'src',
    ],
    'link': [
        'href',
    ],
    'td': [
        'style',
    ],
    'th': [
        'style',
    ],
}

# Like AST_TOKEN_ATTRS, but for the `meta` property.
AST_TOKEN_METAS: typing.Dict[str, typing.List[str]] = {
    'container_block': [
        quizcomp.parser.common.TOKEN_META_KEY_ROOT,
        quizcomp.parser.common.TOKEN_META_KEY_STYLE,
    ]
}

class ASTNode:
    """ A simple representation for an AST node. """

    def __init__(self,
            type: typing.Union[str, None] = None,
            children: typing.Union[typing.List['ASTNode'], None] = None,
            text: str = '',
            **kwargs: typing.Any,
            ) -> None:
        if (type is None):
            raise ValueError("AST nodes cannot have a missing type.")

        self.type: str = type
        """ The type of AST node. """

        if (children is None):
            children = []

        self.children: typing.List['ASTNode'] = children
        """ The children of this node. """

        self.text: str = text
        """
        The text represented by this node (but not its children).
        If these is not text, this will be an empty string.
        """

        self.attributes: typing.Dict[str, typing.Any] = kwargs
        """ Additional attributes attached to this node. """

    def get(self, key: str, default_value: typing.Any) -> typing.Any:
        """ Get an attribute of this node. """

        return self.attributes.get(key, default_value)

    # TEST - old usage of to_pod (from quizcomp, not edq).
    def to_pod(self, omit_empty: bool = True) -> typing.Dict[str, typing.Any]:
        """ Represent this AST as a dictionary, potentially leaving out any empty elements. """

        data: typing.Dict[str, typing.Any] = {
            'type': self.type,
        }

        if (len(self.children) > 0):
            data['children'] = [child.to_pod() for child in self.children]

        if (len(self.text) > 0):
            data['text'] = self.text

        if (len(self.attributes) > 0):
            data['attributes'] = self.attributes

        return data

def build(tokens: typing.Sequence[markdown_it.token.Token]) -> ASTNode:
    """ Build an AST from a stream of tokens. """

    tree = markdown_it.tree.SyntaxTreeNode(tokens)
    return _walk_ast(tree)

def _walk_ast(node: markdown_it.tree.SyntaxTreeNode) -> ASTNode:
    data: typing.Dict[str, typing.Any] = {
        'type': node.type,
    }

    if (node.type in quizcomp.parser.common.CONTENT_NODES):
        data['text'] = node.content

    for name in AST_NODE_ATTRIBUTES.get(node.type, []):
        value = getattr(node, name)
        if ((value is not None) and (value != '')):
            data[name] = value

    for name in AST_TOKEN_ATTRS.get(node.type, []):
        value = node.attrGet(name)
        if (value is not None):
            data[name] = value

    for name in AST_TOKEN_METAS.get(node.type, []):
        value = node.meta.get(name, None)
        if (value is not None):
            data[name] = value

    if (len(node.children) > 0):
        data['children'] = [_walk_ast(child) for child in node.children]

    return ASTNode(**data)
