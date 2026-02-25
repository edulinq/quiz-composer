#!/bin/bash

# Compile TeX generated from each good question test case.
# This is intentionally independent from Python's unittest flow because
# compilation is comparatively slow and should be opt-in.

set -euo pipefail

readonly THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
readonly ROOT_DIR="${THIS_DIR}/.."
readonly GOOD_QUESTIONS_DIR="${ROOT_DIR}/tests/questions/good"
readonly MIN_PDF_SIZE_BYTES=1000
readonly DOCKER_IMAGE="ghcr.io/edulinq/pdflatex-docker:1.0.0"

if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    DEFAULT_PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
else
    DEFAULT_PYTHON_BIN="python3"
fi

PYTHON_BIN="${PYTHON_BIN:-${DEFAULT_PYTHON_BIN}}"
PDFLATEX_BIN="${PDFLATEX_BIN:-pdflatex}"
USE_DOCKER=false
KEEP_TEMP=false
TEMP_DIR=""

function usage() {
    cat <<EOF
Usage: $(basename "$0") [--use-docker] [--pdflatex-bin PATH] [--python-bin PATH] [--keep-temp]

Options:
  --use-docker        Compile TeX with Docker image ${DOCKER_IMAGE}.
  --pdflatex-bin      Path to local pdflatex binary (default: ${PDFLATEX_BIN}).
  --python-bin        Python executable to use (default: ${PYTHON_BIN}).
  --keep-temp         Do not delete temporary output directory.
  -h, --help          Show this help text.
EOF
}

function parse_args() {
    while (($# > 0)); do
        case "$1" in
            --use-docker)
                USE_DOCKER=true
                ;;
            --pdflatex-bin)
                shift
                if (($# == 0)); then
                    echo "Missing value for --pdflatex-bin." >&2
                    exit 2
                fi
                PDFLATEX_BIN="$1"
                ;;
            --python-bin)
                shift
                if (($# == 0)); then
                    echo "Missing value for --python-bin." >&2
                    exit 2
                fi
                PYTHON_BIN="$1"
                ;;
            --keep-temp)
                KEEP_TEMP=true
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown argument: $1" >&2
                usage >&2
                exit 2
                ;;
        esac

        shift
    done
}

function check_requirements() {
    if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
        echo "Could not find python executable: ${PYTHON_BIN}" >&2
        exit 1
    fi

    if [[ "${USE_DOCKER}" == "true" ]]; then
        if ! command -v docker >/dev/null 2>&1; then
            echo "Docker mode requested, but 'docker' is not installed." >&2
            exit 1
        fi

        if ! docker info >/dev/null 2>&1; then
            echo "Docker mode requested, but Docker is not available to the current user." >&2
            exit 1
        fi

        return
    fi

    if ! command -v "${PDFLATEX_BIN}" >/dev/null 2>&1; then
        echo "Could not find local pdflatex binary: ${PDFLATEX_BIN}" >&2
        echo "Install pdflatex or run with --use-docker." >&2
        exit 1
    fi
}

function compile_local() {
    local tex_path="$1"
    local log_path="$2"
    local out_dir
    local tex_filename

    out_dir="$(dirname "${tex_path}")"
    tex_filename="$(basename "${tex_path}")"

    for _ in 1 2; do
        if ! (cd "${out_dir}" && "${PDFLATEX_BIN}" -interaction=nonstopmode -halt-on-error "${tex_filename}" >> "${log_path}" 2>&1); then
            return 1
        fi
    done
}

function compile_docker() {
    local tex_path="$1"
    local log_path="$2"
    local out_dir
    local tex_filename

    out_dir="$(dirname "${tex_path}")"
    tex_filename="$(basename "${tex_path}")"

    for _ in 1 2; do
        if ! docker run --rm \
            --user "$(id -u):$(id -g)" \
            -v "${out_dir}:/work" \
            "${DOCKER_IMAGE}" \
            "${tex_filename}" >> "${log_path}" 2>&1; then
            return 1
        fi
    done
}

function main() {
    parse_args "$@"
    check_requirements

    cd "${ROOT_DIR}"

    mapfile -t question_paths < <(find "${GOOD_QUESTIONS_DIR}" -type f -name "question.json" | sort)
    if ((${#question_paths[@]} == 0)); then
        echo "No good question test cases found under: ${GOOD_QUESTIONS_DIR}" >&2
        exit 1
    fi

    TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/quizcomp-tex-questions.XXXXXX")"

    cleanup() {
        if [[ "${KEEP_TEMP}" == "true" ]]; then
            echo "Keeping temporary output directory: ${TEMP_DIR}"
        else
            rm -rf "${TEMP_DIR}"
        fi
    }
    trap cleanup EXIT

    local num_pass=0
    local num_fail=0
    local index=0

    echo "Running TeX compilation tests for ${#question_paths[@]} question fixtures."
    if [[ "${USE_DOCKER}" == "true" ]]; then
        echo "Compilation mode: Docker (${DOCKER_IMAGE})"
    else
        echo "Compilation mode: local pdflatex (${PDFLATEX_BIN})"
    fi

    for question_path in "${question_paths[@]}"; do
        index=$((index + 1))
        local case_name
        local out_dir
        local tex_path
        local pdf_path
        local log_path
        local rel_path

        rel_path="${question_path#${ROOT_DIR}/}"
        case_name="$(printf "%03d_%s" "${index}" "$(basename "$(dirname "${question_path}")")")"
        out_dir="${TEMP_DIR}/${case_name}"
        tex_path="${out_dir}/question.tex"
        pdf_path="${out_dir}/question.pdf"
        log_path="${out_dir}/compile.log"

        mkdir -p "${out_dir}"

        echo "[${index}/${#question_paths[@]}] ${rel_path}"

        if ! "${PYTHON_BIN}" - "${question_path}" "${tex_path}" "${out_dir}" > /dev/null 2>> "${log_path}" <<'PY'
import os
import sys

import quizcomp.converter.tex
import quizcomp.question.base

question_path = sys.argv[1]
tex_path = sys.argv[2]
out_dir = sys.argv[3]

question = quizcomp.question.base.Question.from_path(question_path)
converter = quizcomp.converter.tex.TexTemplateConverter(
    answer_key = False,
    image_base_dir = os.path.join(out_dir, "images"),
    image_relative_root = "images",
    cleanup_images = False,
)
content = converter.convert_question(question)

with open(tex_path, "w") as file:
    file.write(content)
PY
        then
            echo "  FAIL: Could not generate TeX."
            tail -n 20 "${log_path}" || true
            num_fail=$((num_fail + 1))
            continue
        fi

        if [[ "${USE_DOCKER}" == "true" ]]; then
            if ! compile_docker "${tex_path}" "${log_path}"; then
                echo "  FAIL: Docker compilation failed."
                tail -n 20 "${log_path}" || true
                num_fail=$((num_fail + 1))
                continue
            fi
        else
            if ! compile_local "${tex_path}" "${log_path}"; then
                echo "  FAIL: Local compilation failed."
                tail -n 20 "${log_path}" || true
                num_fail=$((num_fail + 1))
                continue
            fi
        fi

        if [[ ! -f "${pdf_path}" ]]; then
            echo "  FAIL: PDF was not generated (${pdf_path})."
            num_fail=$((num_fail + 1))
            continue
        fi

        local pdf_size
        pdf_size="$(wc -c < "${pdf_path}")"
        if ((pdf_size <= MIN_PDF_SIZE_BYTES)); then
            echo "  FAIL: PDF is too small (${pdf_size} bytes <= ${MIN_PDF_SIZE_BYTES})."
            num_fail=$((num_fail + 1))
            continue
        fi

        echo "  PASS (${pdf_size} bytes)"
        num_pass=$((num_pass + 1))
    done

    echo
    echo "TeX compilation test summary: pass=${num_pass}, fail=${num_fail}, total=${#question_paths[@]}"

    if ((num_fail > 0)); then
        exit 1
    fi
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
