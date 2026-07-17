#!/bin/bash

# Create a full website including all documentation ready to be deployed.
# This script should only be done from a clean repo on the main branch.
# Documentation will be generated from the main branch (latest) as well as each version tag.

readonly THIS_DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd | xargs realpath)"
readonly ROOT_DIR="${THIS_DIR}/.."
readonly TEMPLATE_HTML_DIR="${THIS_DIR}/template/html"
readonly BUILD_DIR="${ROOT_DIR}/build"
readonly DOCS_BUILD_DIR="${BUILD_DIR}/html"
readonly SITE_BUILD_DIR="${BUILD_DIR}/site"
readonly DOCS_DIRNAME='docs'
readonly DOCS_OUT_DIR="${SITE_BUILD_DIR}/${DOCS_DIRNAME}"
readonly GEN_DOCS_SCRIPT="${THIS_DIR}/gen_docs.sh"

readonly MAIN_BRANCH="main"

readonly REPO='edulinq/quiz-composer'
readonly REPO_DISPLAY_NAME='EduLinq Quiz Composer'
readonly REPO_MAIN_PACKAGE_NAME='quizcomp'

readonly INDEX_TITLE_LOCATION='<header class="pdoc">'
readonly MODULE_TITLE_LOCATION='<section class="module-info">'

readonly API_DOC_MARKER='<!-- API-DOC-MARKER -->'

# Don't generate any docs for this version or earlier.
# Because of this specific tag, we can just do a lexicographic comparison.
readonly ONLY_AFTER_TAG='v1.0.0'

function check_git() {
    if [ ! -z "$(git status --porcelain)" ] ; then
        echo "ERROR: Repository is not clean."
        exit 1
    fi

    if [ $(git branch --show-current) != "${MAIN_BRANCH}" ] ; then
        echo "ERROR: Repository is not on the main branch."
        exit 2
    fi

    return 0
}

function gen_docs() {
    local label=$1
    local reference=$2
    local dirname=$3

    echo "Generating docs for '${label}'."

    rm -rf "${DOCS_BUILD_DIR}"
    ${GEN_DOCS_SCRIPT} "${DOCS_BUILD_DIR}"

    # Add in the label to the landing pages.
    local git_link="https://github.com/${REPO}/tree/${reference}"

    local index_title="<h1 style='flex-grow: 1'>${REPO_DISPLAY_NAME} API Reference: <a href='${git_link}'>${label}</a></h1>"
    sed -i "s#${INDEX_TITLE_LOCATION}#${INDEX_TITLE_LOCATION}${index_title}#" "${DOCS_BUILD_DIR}/index.html"

    local module_title="<h1>${REPO_DISPLAY_NAME} API Reference: <a href='${git_link}'>${label}</a></h1>"
    sed -i "s#${MODULE_TITLE_LOCATION}#${MODULE_TITLE_LOCATION}${module_title}#" "${DOCS_BUILD_DIR}/${REPO_MAIN_PACKAGE_NAME}.html"

    # Moved the compiled documentation to the main site.
    mkdir -p "${DOCS_OUT_DIR}"
    mv "${DOCS_BUILD_DIR}" "${DOCS_OUT_DIR}/${dirname}"

    # Add this documentation to the main index page.
    local index_li="<li><a href='${DOCS_DIRNAME}/${dirname}/index.html'>${label}</a></li>"
    sed -i "s#${API_DOC_MARKER}#${index_li}${API_DOC_MARKER}#" "${SITE_BUILD_DIR}/index.html"
}

function main() {
    if [[ $# -ne 0 ]]; then
        echo "USAGE: $0"
        exit 1
    fi

    set -e
    trap exit SIGINT

    cd "${ROOT_DIR}"

    # Remove any existing output.
    rm -rf "${SITE_BUILD_DIR}"
    mkdir -p "${SITE_BUILD_DIR}"
    cp -r "${TEMPLATE_HTML_DIR}"/* "${SITE_BUILD_DIR}"/

    # Ensure that the repo looks good.
    check_git

    # Generate the latest documentation.
    local git_hash=$(git rev-parse --short HEAD)
    gen_docs "latest (${git_hash})" "${git_hash}" 'latest'

    # Generate docs for each tagged version.
    for tag in $(git tag -l | grep -P '^v\d+\.\d+\.\d+' | sort -r --version-sort ) ; do
        if [[ ! "${tag}" > "${ONLY_AFTER_TAG}" ]] ; then
            continue
        fi

        git checkout --quiet "${tag}"
        gen_docs "${tag}" "${tag}" "${tag}"
    done

    # Move back to main.
    git checkout --quiet "${MAIN_BRANCH}"

    return 0
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
