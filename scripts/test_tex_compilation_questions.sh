#!/bin/bash

# Compile TeX/PDF output for good question and quiz test cases.
# This is intentionally independent from Python's unittest flow because
# compilation is comparatively slow and should be opt-in.

set -euo pipefail

readonly THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
readonly ROOT_DIR="${THIS_DIR}/.."
readonly GOOD_QUESTIONS_DIR="${ROOT_DIR}/tests/questions/good"
readonly GOOD_QUIZZES_DIR="${ROOT_DIR}/tests/quizzes/good"
readonly OUTPUT_DIR="${TMPDIR:-/tmp}/quizcomp-tex-compilation"
readonly LOG_TAIL_LINES=20

QUESTION_PATHS=()
QUIZ_PATHS=()
RUN_STATUS=0

function fail() {
    echo "ERROR: $1" >&2
    exit 1
}

function run_command() {
    local log_path="$1"
    shift

    set +e
    "$@" >> "${log_path}" 2>&1
    RUN_STATUS=$?
    set -e

    return 0
}

function check_requirements() {
    if ! command -v python3 >/dev/null 2>&1 ; then
        fail "Could not find python3."
    fi

    if ! command -v pdflatex >/dev/null 2>&1 ; then
        fail "Could not find pdflatex."
    fi
}

function discover_cases() {
    mapfile -t question_paths < <(find "${GOOD_QUESTIONS_DIR}" -type f -name "question.json" | sort)
    mapfile -t quiz_paths < <(find "${GOOD_QUIZZES_DIR}" -type f -name "quiz.json" | sort)

    if (( ${#question_paths[@]} == 0 )) ; then
        fail "No good question test cases found."
    fi

    if (( ${#quiz_paths[@]} == 0 )) ; then
        fail "No good quiz test cases found."
    fi

    QUESTION_PATHS=("${question_paths[@]}")
    QUIZ_PATHS=("${quiz_paths[@]}")
}

function run_question_tests() {
    local num_pass=0
    local num_fail=0
    local question_count=0

    for question_path in "${QUESTION_PATHS[@]}" ; do
        question_count=$((question_count + 1))

        local rel_path="${question_path#${ROOT_DIR}/}"
        local case_dir="${OUTPUT_DIR}/question-$(printf "%03d" "${question_count}")"
        local log_path="${case_dir}/compile.log"
        local pdf_count=0
        local status=0

        rm -rf "${case_dir}"
        mkdir -p "${case_dir}"

        echo "[question ${question_count}/${#QUESTION_PATHS[@]}] ${rel_path}"

        run_command "${log_path}" python3 -m quizcomp.cli.pdf.create_question "${question_path}" --outdir "${case_dir}"
        status="${RUN_STATUS}"
        if (( status != 0 )) ; then
            echo "    FAIL: question PDF creation failed." >&2
            tail -n "${LOG_TAIL_LINES}" "${log_path}" || true
            num_fail=$((num_fail + 1))
            continue
        fi

        pdf_count="$(find "${case_dir}" -type f -name "*.pdf" | wc -l)"
        if (( pdf_count == 0 )) ; then
            echo "    FAIL: missing PDF output." >&2
            num_fail=$((num_fail + 1))
            continue
        fi

        num_pass=$((num_pass + 1))
    done

    QUESTION_PASS="${num_pass}"
    QUESTION_FAIL="${num_fail}"
}

function run_quiz_tests() {
    local num_pass=0
    local num_fail=0
    local quiz_count=0

    for quiz_path in "${QUIZ_PATHS[@]}" ; do
        quiz_count=$((quiz_count + 1))

        local rel_path="${quiz_path#${ROOT_DIR}/}"
        local case_dir="${OUTPUT_DIR}/quiz-$(printf "%03d" "${quiz_count}")"
        local log_path="${case_dir}/compile.log"
        local pdf_count=0
        local status=0

        rm -rf "${case_dir}"
        mkdir -p "${case_dir}"

        echo "[quiz ${quiz_count}/${#QUIZ_PATHS[@]}] ${rel_path}"

        run_command "${log_path}" python3 -m quizcomp.cli.pdf.create "${quiz_path}" --outdir "${case_dir}"
        status="${RUN_STATUS}"
        if (( status != 0 )) ; then
            echo "    FAIL: quiz PDF creation failed." >&2
            tail -n "${LOG_TAIL_LINES}" "${log_path}" || true
            num_fail=$((num_fail + 1))
            continue
        fi

        pdf_count="$(find "${case_dir}" -type f -name "*.pdf" | wc -l)"
        if (( pdf_count == 0 )) ; then
            echo "    FAIL: no PDF output found." >&2
            num_fail=$((num_fail + 1))
            continue
        fi

        num_pass=$((num_pass + 1))
    done

    QUIZ_PASS="${num_pass}"
    QUIZ_FAIL="${num_fail}"
}

function main() {
    cd "${ROOT_DIR}"

    check_requirements
    discover_cases

    mkdir -p "${OUTPUT_DIR}"

    run_question_tests
    run_quiz_tests

    local num_pass=$((QUESTION_PASS + QUIZ_PASS))
    local num_fail=$((QUESTION_FAIL + QUIZ_FAIL))
    local total_count=$((num_pass + num_fail))

    echo ''
    echo "TeX compilation test summary: pass=${num_pass}, fail=${num_fail}, total=${total_count}"
    echo "Output directory: ${OUTPUT_DIR}"

    if (( num_fail > 0 )) ; then
        return 1
    fi
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
