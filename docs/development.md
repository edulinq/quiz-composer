# Development

This document contains some notes for any developers.

## CI

To run mostly the same checks run in CI, use the [scripts/check_all.sh](../scripts/check_all.sh) script:
```sh
./scripts/check_all.sh
```

## Testing

Because test project involves different forms of parsing and compilation
(two things which historically have a lot of tests),
we break out our tests into several different places.

### "Normal" Tests

Tests that don't fall into the other categories are all grouped together.
These tests will be written in Python and have the `_test.py` suffix.

You can run all these tests with the [scripts/run_tests.sh](../scripts/run_tests.sh) script:
```sh
./scripts/run_tests.sh
```

This script also accepts an argument that is a Python regular expression.
Only tests that match the regular expression will be run.
For example, to only run CLI tests, you can use:
```sh
./scripts/run_tests.sh quiz
```

### Parsing Tests

Tests for the core parsing engine are also written in Python and have the `_parsertest.py` suffix.

You can run all these tests with the [scripts/run_parser_tests.sh](../scripts/run_parser_tests.sh) script:
```sh
./scripts/run_parser_tests.sh
```

Like the normal tests, this script takes an optional regex pattern:
```sh
./scripts/run_parser_tests.sh commonmark
```

### TeX Compilation Tests

TeX compilation tests generally take longer and require `pdflatex` to be installed an accessible.
These tests will compile all valid test quizzes and questions.

You can run these tests with the [scripts/run_compilation_tests.sh](../scripts/run_compilation_tests.sh) script:
```sh
./scripts/run_compilation_tests.sh
```

These tests can also take an optional pattern (but uses Bash matching with the `=~` operator):
```sh
./scripts/run_compilation_tests.sh image
```
