#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"

echo "=== Test Script ==="
echo "Build directory: ${BUILD_DIR}"

if [[ ! -d "${BUILD_DIR}" ]]; then
    echo "ERROR: Build directory not found. Run build.sh first."
    exit 1
fi

cd "${BUILD_DIR}"

echo "Running tests..."
ctest --output-on-failure --parallel 4

echo "All tests passed!"