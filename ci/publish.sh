#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"

ARTIFACT_SERVER_URL="${ARTIFACT_SERVER_URL:-}"
ARTIFACT_SERVER_TOKEN="${ARTIFACT_SERVER_TOKEN:-}"
BUILD_NUMBER="${BUILD_NUMBER:-local}"
BRANCH_NAME="${BRANCH_NAME:-unknown}"

echo "=== Publish Script ==="
echo "Build number: ${BUILD_NUMBER}"
echo "Branch: ${BRANCH_NAME}"

if [[ -z "${ARTIFACT_SERVER_URL}" ]]; then
    echo "WARNING: ARTIFACT_SERVER_URL not set. Skipping external publish."
    echo "Archiving locally only."
    exit 0
fi

if [[ -z "${ARTIFACT_SERVER_TOKEN}" ]]; then
    echo "ERROR: ARTIFACT_SERVER_TOKEN not set."
    exit 1
fi

if [[ ! -d "${BUILD_DIR}" ]]; then
    echo "ERROR: Build directory not found."
    exit 1
fi

ARTIFACTS=()
if [[ -f "${BUILD_DIR}/calculator_app" ]]; then
    ARTIFACTS+=("${BUILD_DIR}/calculator_app")
fi

for xml in "${BUILD_DIR}"/*.xml; do
    if [[ -f "${xml}" ]]; then
        ARTIFACTS+=("${xml}")
    fi
done

if [[ ${#ARTIFACTS[@]} -eq 0 ]]; then
    echo "ERROR: No artifacts found to publish."
    exit 1
fi

echo "Found ${#ARTIFACTS[@]} artifact(s) to publish:"
for artifact in "${ARTIFACTS[@]}"; do
    echo "  - ${artifact}"
done

cd "${BUILD_DIR}"

for artifact in "${ARTIFACTS[@]}"; do
    filename=$(basename "${artifact}")
    echo "Uploading ${filename}..."

    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer ${ARTIFACT_SERVER_TOKEN}" \
        -F "project=CppBuildLab" \
        -F "build_number=${BUILD_NUMBER}" \
        -F "branch=${BRANCH_NAME}" \
        -F "file=@${artifact}" \
        "${ARTIFACT_SERVER_URL}/upload")

    http_code=$(echo "${response}" | tail -n1)
    body=$(echo "${response}" | head -n -1)

    if [[ "${http_code}" -eq 200 ]] || [[ "${http_code}" -eq 201 ]]; then
        echo "  Success: ${body}"
    else
        echo "  Failed (HTTP ${http_code}): ${body}"
        exit 1
    fi
done

echo "All artifacts published successfully!"