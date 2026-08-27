#!/usr/bin/env bash
# Test the package (lint, type-check, unit tests, and installation tests)
# across every Python version declared as supported in pyproject.toml,
# using uv to provision each interpreter and a fresh environment.
#
# Usage:
#   ./scripts/test-all-python-versions.sh                # full suite, all versions
#   ./scripts/test-all-python-versions.sh 3.12            # only Python 3.12
#   INSTALL_TESTS=1 ./scripts/test-all-python-versions.sh # also run `pytest -m install`
#
# Requires: uv (https://docs.astral.sh/uv/)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Supported versions, kept in sync with pyproject.toml's classifiers /
# requires-python and the CI matrix in .github/workflows/tests.yml.
DEFAULT_VERSIONS=("3.11" "3.12" "3.13")

if [ "$#" -gt 0 ]; then
    VERSIONS=("$@")
else
    VERSIONS=("${DEFAULT_VERSIONS[@]}")
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "error: uv is not installed. See https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

INSTALL_TESTS="${INSTALL_TESTS:-0}"

FAILED_VERSIONS=()

for version in "${VERSIONS[@]}"; do
    echo ""
    echo "==================================================================="
    echo "  Testing with Python ${version}"
    echo "==================================================================="

    if ! uv python find "${version}" >/dev/null 2>&1; then
        echo "-- Python ${version} not found locally; asking uv to install it"
        uv python install "${version}"
    fi

    set +e
    (
        set -e
        uv sync --all-extras --python "${version}"
        echo "-- Lint (ruff)"
        uv run --python "${version}" ruff check .
        echo "-- Type check (mypy)"
        uv run --python "${version}" mypy odr_bootstrap
        echo "-- Unit tests (pytest)"
        uv run --python "${version}" pytest

        if [ "${INSTALL_TESTS}" = "1" ]; then
            echo "-- Installation tests (pytest -m install)"
            uv run --python "${version}" pytest -m install tests/test_installation.py --no-cov
        fi
    )
    status=$?
    set -e

    if [ "${status}" -ne 0 ]; then
        echo "!! Python ${version}: FAILED"
        FAILED_VERSIONS+=("${version}")
    else
        echo "++ Python ${version}: PASSED"
    fi
done

echo ""
echo "==================================================================="
if [ "${#FAILED_VERSIONS[@]}" -eq 0 ]; then
    echo "All Python versions passed: ${VERSIONS[*]}"
    exit 0
else
    echo "Failures on: ${FAILED_VERSIONS[*]}"
    exit 1
fi
