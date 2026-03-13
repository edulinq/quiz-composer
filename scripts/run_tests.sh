#!/bin/bash

# Run unit tests with the standard testing main.

readonly THIS_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd | xargs realpath)"
readonly ROOT_DIR="${THIS_DIR}/.."

function main() {
    set -e
    trap exit SIGINT

    cd "${ROOT_DIR}"

    python3 -m edq.testing.run $@
    return $?
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
