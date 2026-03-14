#!/bin/bash

# Create HTML documentation for the current code.

readonly THIS_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd | xargs realpath)"
readonly ROOT_DIR="${THIS_DIR}/.."

readonly BASE_PACKAGE="quizcomp"
readonly PACKAGE_DIR="${ROOT_DIR}/${BASE_PACKAGE}"
readonly DEFAULT_OUT_DIR="${ROOT_DIR}/build/html"

readonly FILE_PATTERNS='!.*_test !.*_backendtest'

function main() {
    if [[ $# -gt 1 ]]; then
        echo "USAGE: $0 [out dir]"
        exit 1
    fi

    set -e
    trap exit SIGINT

    local outputDir=$DEFAULT_OUT_DIR
    if [[ $# -gt 0 ]]; then
        outputDir=$1
    fi

    cd "${ROOT_DIR}"

    mkdir -p "${outputDir}"

    # Build the base docs.
    pdoc --output-directory "${outputDir}" "${PACKAGE_DIR}" ${FILE_PATTERNS}
    if [[ $? -ne 0 ]] ; then
        echo "Failed to generate docs."
        return 2
    fi

    # Update the docs with CLI information.
    NO_COLOR=1 python3 -m edq.cli.doc.update-pdoc-cli "${PACKAGE_DIR}" "${BASE_PACKAGE}" "${outputDir}"
    if [[ $? -ne 0 ]] ; then
        echo "Failed to update docs with CLI information."
        return 3
    fi

    return 0
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
