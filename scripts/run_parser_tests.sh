#!/bin/bash

# Run tests specifically about parsing.

readonly THIS_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd | xargs realpath)"
readonly ROOT_DIR="${THIS_DIR}/.."

function main() {
    set -e
    trap exit SIGINT

    cd "${ROOT_DIR}"

    python3 -m edq.testing.run --filename-pattern '*_parsertest.py' $@
    return $?
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
