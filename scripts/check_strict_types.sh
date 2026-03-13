#!/bin/bash

# Check types (strictly) with mypy.

readonly THIS_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd | xargs realpath)"
readonly ROOT_DIR="${THIS_DIR}/.."

function main() {
    if [[ $# -ne 0 ]]; then
        echo "USAGE: $0"
        exit 1
    fi

    set -e
    trap exit SIGINT

    cd "${ROOT_DIR}"

    mypy quizcomp --strict --cache-dir "${ROOT_DIR}/.mypy_strict_cache"
    return $?
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
