#!/bin/bash

# Compile TeX/PDF output for good question and quiz test cases.
# This is intentionally independent from Python's unittest flow because
# compilation is comparatively slow and should be opt-in.

set -euo pipefail

readonly THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
readonly ROOT_DIR="${THIS_DIR}/.."
readonly GOOD_QUESTIONS_DIR="${ROOT_DIR}/tests/questions/good"
readonly GOOD_QUIZZES_DIR="${ROOT_DIR}/tests/quizzes/good"

function main() {
    set -e
    trap exit SIGINT

    cd "${ROOT_DIR}"

    if ! command -v python3 >/dev/null 2>&1; then
        echo "Could not find python3." >&2
        exit 1
    fi

    if ! command -v pdflatex >/dev/null 2>&1; then
        echo "Could not find pdflatex." >&2
        exit 1
    fi

    temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/quizcomp-tex-compilation.XXXXXX")"
    trap "rm -rf \"${temp_dir}\"" EXIT

    mapfile -t question_paths < <(find "${GOOD_QUESTIONS_DIR}" -type f -name "question.json" | sort)
    mapfile -t quiz_paths < <(find "${GOOD_QUIZZES_DIR}" -type f -name "quiz.json" | sort)

    if (( ${#question_paths[@]} == 0 && ${#quiz_paths[@]} == 0 )); then
        echo "No good question/quiz test cases found." >&2
        exit 1
    fi

    local num_pass=0
    local num_fail=0

    local question_count=0
    for question_path in "${question_paths[@]}"; do
        question_count=$((question_count + 1))

        local rel_path
        local case_dir
        local tex_path
        local log_path

        rel_path="${question_path#${ROOT_DIR}/}"
        case_dir="${temp_dir}/question-$(printf "%03d" "${question_count}")"
        tex_path="${case_dir}/question.tex"
        log_path="${case_dir}/compile.log"

        mkdir -p "${case_dir}"

        echo "[question ${question_count}/${#question_paths[@]}] ${rel_path}"

        if ! python3 -m quizcomp.cli.parse.question "${question_path}" --format tex > "${tex_path}" 2> "${log_path}"; then
            echo "  FAIL: could not generate TeX." >&2
            tail -n 20 "${log_path}" || true
            num_fail=$((num_fail + 1))
            continue
        fi

        if ! python3 -c "import sys; import quizcomp.latex; quizcomp.latex.compile(sys.argv[1])" "${tex_path}" >> "${log_path}" 2>&1; then
            echo "  FAIL: could not compile TeX with quizcomp.latex.compile()." >&2
            tail -n 20 "${log_path}" || true
            num_fail=$((num_fail + 1))
            continue
        fi

        if [[ ! -f "${case_dir}/question.pdf" ]]; then
            echo "  FAIL: missing PDF output." >&2
            num_fail=$((num_fail + 1))
            continue
        fi

        num_pass=$((num_pass + 1))
    done

    local quiz_count=0
    for quiz_path in "${quiz_paths[@]}"; do
        quiz_count=$((quiz_count + 1))

        local rel_path
        local case_dir
        local log_path
        local pdf_count

        rel_path="${quiz_path#${ROOT_DIR}/}"
        case_dir="${temp_dir}/quiz-$(printf "%03d" "${quiz_count}")"
        log_path="${case_dir}/compile.log"

        mkdir -p "${case_dir}"

        echo "[quiz ${quiz_count}/${#quiz_paths[@]}] ${rel_path}"

        if ! python3 -m quizcomp.cli.pdf.create "${quiz_path}" --outdir "${case_dir}" >> "${log_path}" 2>&1; then
            echo "  FAIL: quizcomp.cli.pdf.create failed." >&2
            tail -n 20 "${log_path}" || true
            num_fail=$((num_fail + 1))
            continue
        fi

        pdf_count="$(find "${case_dir}" -type f -name "*.pdf" | wc -l)"
        if ((pdf_count == 0)); then
            echo "  FAIL: no PDF output found." >&2
            num_fail=$((num_fail + 1))
            continue
        fi

        num_pass=$((num_pass + 1))
    done

    local total_count
    total_count=$(( ${#question_paths[@]} + ${#quiz_paths[@]} ))

    echo ''
    echo "TeX compilation test summary: pass=${num_pass}, fail=${num_fail}, total=${total_count}"

    if ((num_fail > 0)); then
        exit 1
    fi
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
