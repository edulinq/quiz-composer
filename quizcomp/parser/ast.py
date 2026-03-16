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

class ASTNode(dict):
    """ A simple representation for an AST node. """

    def type(self) -> str:
        """ Get the type of this node. """

        return self['type']

    def children(self) -> typing.List['ASTNode']:
        """ Get the ordered children of this node. """

        return self.get('children', [])

    def text(self) -> str:
        """ Get any text represented by this node (but not its children). """

        return self.get('text', '')

def build(tokens: typing.Sequence[markdown_it.token.Token]) -> ASTNode:
    """ Build an AST from a stream of tokens. """

    tree = markdown_it.tree.SyntaxTreeNode(tokens)
    return _walk_ast(tree)

def _walk_ast(node: markdown_it.tree.SyntaxTreeNode) -> ASTNode:
    result: typing.Dict[str, typing.Any] = {
        'type': node.type,
    }

    if (node.type in quizcomp.parser.common.CONTENT_NODES):
        result['text'] = node.content

    for name in AST_NODE_ATTRIBUTES.get(node.type, []):
        value = getattr(node, name)
        if ((value is not None) and (value != '')):
            result[name] = value

    for name in AST_TOKEN_ATTRS.get(node.type, []):
        value = node.attrGet(name)
        if (value is not None):
            result[name] = value

    for name in AST_TOKEN_METAS.get(node.type, []):
        value = node.meta.get(name, None)
        if (value is not None):
            result[name] = value

    if (len(node.children) > 0):
        result['children'] = [_walk_ast(child) for child in node.children]

    return ASTNode(result)
