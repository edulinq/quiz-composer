#!/bin/bash

# Profile run_tests.py.
# Any arguments passed to this script will be forwarded to run_tests.py.

readonly THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
readonly ROOT_DIR="${THIS_DIR}/.."

readonly RUN_TESTS_RELPATH="run_tests.py"

readonly TEMP_STATS_PATH="/tmp/quizcomp_profile_stats.cprofile"

readonly ROW_COUNT=50

function main() {
    set -e
    trap exit SIGINT

    cd "${ROOT_DIR}"

    echo "Profiling ..."
    python -m cProfile -o "${TEMP_STATS_PATH}" "${RUN_TESTS_RELPATH}" "$@" > "${TEMP_STATS_PATH}.out" 2> "${TEMP_STATS_PATH}.err"
    echo "Profiling Complete"
    echo ""

    echo "--- BEGIN: All Functions, Sorted by Cumulative Time, Top ${ROW_COUNT} ---"
    python -c "import pstats ; stats = pstats.Stats('${TEMP_STATS_PATH}') ; stats.sort_stats('cumtime').print_stats(${ROW_COUNT})"
    echo "--- END: All Functions, Sorted by Cumulative Time, Top ${ROW_COUNT} ---"

    echo "--- BEGIN: All Functions, Sorted by Total Time, Top ${ROW_COUNT} ---"
    python -c "import pstats ; stats = pstats.Stats('${TEMP_STATS_PATH}') ; stats.sort_stats('tottime').print_stats(${ROW_COUNT})"
    echo "--- END: All Functions, Sorted by Total Time, Top ${ROW_COUNT} ---"

    echo "--- BEGIN: Quiz Composer Functions, Sorted by Cumulative Time, Top ${ROW_COUNT} ---"
    python -c "import pstats ; stats = pstats.Stats('${TEMP_STATS_PATH}') ; stats.sort_stats('cumtime').print_stats('quizcomp', ${ROW_COUNT})"
    echo "--- END: Quiz Composer Functions, Sorted by Cumulative Time, Top ${ROW_COUNT} ---"

    echo "--- BEGIN: Quiz Composer Functions, Sorted by Total Time, Top ${ROW_COUNT} ---"
    python -c "import pstats ; stats = pstats.Stats('${TEMP_STATS_PATH}') ; stats.sort_stats('tottime').print_stats('quizcomp', ${ROW_COUNT})"
    echo "--- END: Quiz Composer Functions, Sorted by Total Time, Top ${ROW_COUNT} ---"
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
