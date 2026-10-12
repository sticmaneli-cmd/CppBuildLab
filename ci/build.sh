#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BUILD_DIR="${PROJECT_ROOT}/build"
CONFIG_FILE="${PROJECT_ROOT}/ci-config.yaml"

echo "=== Build Script ==="
echo "Project root: ${PROJECT_ROOT}"
echo "Build directory: ${BUILD_DIR}"

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

echo "Configuring with CMake..."
cmake -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TESTS=ON \
    "${PROJECT_ROOT}"

echo "Building..."
ninja

echo "Build completed successfully"
echo "Artifacts in: ${BUILD_DIR}"
ls -la "${BUILD_DIR}/"