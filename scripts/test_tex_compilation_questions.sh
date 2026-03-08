#!/bin/bash

# Compile TeX/PDF output for question and quiz test cases.
# This is intentionally independent from Python's unittest flow because
# compilation is comparatively slow and should be opt-in.

set -uo pipefail

readonly THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
readonly ROOT_DIR="${THIS_DIR}/.."
readonly GOOD_QUESTIONS_DIR="${ROOT_DIR}/tests/questions/good"
readonly GOOD_QUIZZES_DIR="${ROOT_DIR}/tests/quizzes/good"
readonly OUTPUT_DIR="${TMPDIR:-/tmp}/quizcomp-tex-compilation"
readonly LOG_TAIL_LINES=20

num_pass=0
num_fail=0

function check_requirements() {
    if ! command -v python3 >/dev/null 2>&1 ; then
        echo "ERROR: Could not find python3." >&2
        exit 10
    fi

    if ! command -v pdflatex >/dev/null 2>&1 ; then
        echo "ERROR: Could not find pdflatex." >&2
        exit 11
    fi
}

function run_tests() {
    local case_type="$1"
    local base_dir="$2"
    local case_filename="$3"
    local cli_module="$4"

    local -a case_paths=()
    mapfile -t case_paths < <(find "${base_dir}" -type f -name "${case_filename}" | sort)

    if (( ${#case_paths[@]} == 0 )) ; then
        echo "ERROR: No ${case_type} test cases found." >&2
        return 20
    fi

    local case_count=0

    for case_path in "${case_paths[@]}" ; do
        case_count=$((case_count + 1))

        local rel_path="${case_path#${ROOT_DIR}/}"
        local case_dir="${OUTPUT_DIR}/${case_type}-$(printf "%03d" "${case_count}")"
        local log_path="${case_dir}/compile.log"

        rm -rf "${case_dir}"
        mkdir -p "${case_dir}"

        echo "[${case_type}] ${rel_path}"

        python3 -m "${cli_module}" "${case_path}" --outdir "${case_dir}" > "${log_path}" 2>&1
        local status=$?
        if (( status != 0 )) ; then
            echo "    FAIL: PDF creation failed." >&2
            tail -n "${LOG_TAIL_LINES}" "${log_path}" || true
            num_fail=$((num_fail + 1))
            continue
        fi

        local pdf_count="$(find "${case_dir}" -type f -name "*.pdf" | wc -l)"
        if (( pdf_count == 0 )) ; then
            echo "    FAIL: PDF creation failed." >&2
            num_fail=$((num_fail + 1))
            continue
        fi

        num_pass=$((num_pass + 1))
    done
}

function main() {
    cd "${ROOT_DIR}"

    check_requirements

    mkdir -p "${OUTPUT_DIR}"
    echo "Running TeX compilation tests."
    echo "Output directory: ${OUTPUT_DIR}"
    echo ''

    run_tests "question" "${GOOD_QUESTIONS_DIR}" "question.json" "quizcomp.cli.pdf.create_question"
    run_tests "quiz" "${GOOD_QUIZZES_DIR}" "quiz.json" "quizcomp.cli.pdf.create"

    local total_count=$((num_pass + num_fail))

    echo ''
    echo "TeX compilation test summary: pass=${num_pass}, fail=${num_fail}, total=${total_count}"

    if (( num_fail > 0 )) ; then
        return 1
    fi
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
