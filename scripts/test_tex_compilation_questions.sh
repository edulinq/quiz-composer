#!/bin/bash

# Compile TeX generated from each good question test case.
# This is intentionally independent from Python's unittest flow because
# compilation is comparatively slow and should be opt-in.

set -euo pipefail

readonly THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
readonly ROOT_DIR="${THIS_DIR}/.."
readonly GOOD_QUESTIONS_DIR="${ROOT_DIR}/tests/questions/good"

function main() {
    cd "${ROOT_DIR}"

    if ! command -v python3 >/dev/null 2>&1; then
        echo "Could not find python3." >&2
        exit 1
    fi

    if ! command -v pdflatex >/dev/null 2>&1; then
        echo "Could not find pdflatex." >&2
        exit 1
    fi

    temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/quizcomp-tex-questions.XXXXXX")"
    trap "rm -rf \"${temp_dir}\"" EXIT

    local count=0
    while read -r question_path; do
        count=$((count + 1))

        local rel_path
        local case_dir
        local tex_path

        rel_path="${question_path#${ROOT_DIR}/}"
        case_dir="${temp_dir}/$(printf "%03d" "${count}")"
        tex_path="${case_dir}/question.tex"

        mkdir -p "${case_dir}"

        echo "[${count}] ${rel_path}"

        python3 -m quizcomp.cli.parse.question "${question_path}" --format tex > "${tex_path}"

        (
            cd "${case_dir}"
            pdflatex -interaction=nonstopmode -halt-on-error question.tex > /dev/null
            pdflatex -interaction=nonstopmode -halt-on-error question.tex > /dev/null
        )

        if [[ ! -f "${case_dir}/question.pdf" ]]; then
            echo "Missing PDF output for ${rel_path}." >&2
            exit 1
        fi
    done < <(find "${GOOD_QUESTIONS_DIR}" -type f -name "question.json" | sort)

    if ((count == 0)); then
        echo "No good question test cases found under: ${GOOD_QUESTIONS_DIR}" >&2
        exit 1
    fi

    echo ''
    echo "TeX compilation test summary: pass=${count}, fail=0, total=${count}"
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
