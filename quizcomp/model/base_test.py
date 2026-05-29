import typing

import edq.testing.unittest

import quizcomp.model.base

class TestCoreType(edq.testing.unittest.BaseTest):
    """ Test basic operations of the core type. """

    def test_get_hierarchical_value(self) -> None:
        """ Test getting hierarchical values. """

        # [(case name, grandparent init kwargs, parent init kwargs, child init kwargs, value type, key, expected, error substring), ...]
        test_cases: typing.List[typing.Tuple[
                str,
                typing.Dict[str, typing.Any],
                typing.Dict[str, typing.Any],
                typing.Dict[str, typing.Any],
                str,
                str,
                typing.Any,
                typing.Union[str, None]
        ]] = [
            (
                'Missing - Empty',
                {},
                {},
                {},
                'attributes',
                'key',
                None,
                None,
            ),

            (
                'Self - Base',
                {},
                {},
                {'attributes': {'key': 'a'}},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'Parent - Base',
                {},
                {'attributes': {'key': 'a'}},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'GParent - Base',
                {'attributes': {'key': 'a'}},
                {},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'Child - Override Ancestors',
                {'attributes': {'key': 'z'}},
                {'attributes': {'key': 'b'}},
                {'attributes': {'key': 'a'}},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'Parent - Override GParent',
                {'attributes': {'key': 'z'}},
                {'attributes': {'key': 'a'}},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'First - Parent Base',
                {},
                {'attributes_first': {'key': 'a'}},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'Last - Parent Base',
                {},
                {'attributes_last': {'key': 'a'}},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'First - GParent Base',
                {'attributes_first': {'key': 'a'}},
                {},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'Last - GParent Base',
                {'attributes_last': {'key': 'a'}},
                {},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'First - Override Base',
                {},
                {'attributes': {'key': 'z'}, 'attributes_first': {'key': 'a'}},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'Last - Override Base',
                {},
                {'attributes': {'key': 'z'}, 'attributes_last': {'key': 'a'}},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'Last - Override First',
                {},
                {'attributes_first': {'key': 'z'}, 'attributes_last': {'key': 'a'}},
                {},
                'attributes',
                'key',
                'a',
                None,
            ),

            (
                'Error - Unknown Value Type',
                {},
                {},
                {},
                'zzz',
                'key',
                None,
                'Unknown value type',
            ),
        ]

        for (i, test_case) in enumerate(test_cases):
            (case_name, gparent_kwargs, parent_kwargs, child_kwargs, value_type, key, expected, error_substring) = test_case

            with self.subTest(msg = f"Case {i} ({case_name}):"):
                gparent = quizcomp.model.base.CoreType(**gparent_kwargs)
                parent = quizcomp.model.base.CoreType(**parent_kwargs)
                child = quizcomp.model.base.CoreType(**child_kwargs)

                parent.children.append(child)
                child.parent = parent

                gparent.children.append(parent)
                parent.parent = gparent

                try:
                    actual = child._get_hierarchical_value(value_type, key)
                except Exception as ex:
                    error_string = self.format_error_string(ex)
                    if (error_substring is None):
                        self.fail(f"Unexpected error: '{error_string}'.")

                    self.assertIn(error_substring, error_string, 'Error is not as expected.')

                    continue

                if (error_substring is not None):
                    self.fail(f"Did not get expected error: '{error_substring}'.")

                self.assertEqual(expected, actual)
