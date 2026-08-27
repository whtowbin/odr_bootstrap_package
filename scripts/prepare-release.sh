#!/usr/bin/env bash
# Rebuild everything that should be fresh before pushing/publishing:
#   1. Sync dependencies with uv
#   2. Lint + type-check
#   3. Run the unit test suite (with coverage) and the uv-installation tests
#   4. Regenerate the example figures (updates calibration_*.png in the repo
#      root, examples/, and docs/source/_static/ in one pass)
#   5. Rebuild the Sphinx documentation
#   6. Bump the package version (pyproject.toml + odr_bootstrap/__init__.py)
#      and refresh uv.lock, if --bump/--set-version was given
#   7. Clear out old dist/ artifacts and build a fresh sdist/wheel with
#      `uv build`
#   8. Print a git status summary of anything that changed (e.g. regenerated
#      images/docs/version) so you can review before committing
#
# Usage:
#   ./scripts/prepare-release.sh                       # full pipeline, no version bump
#   ./scripts/prepare-release.sh --skip-tests           # skip pytest steps (faster iterate)
#   ./scripts/prepare-release.sh --skip-docs             # skip Sphinx build
#   ./scripts/prepare-release.sh --bump patch            # bump X.Y.Z -> X.Y.(Z+1)
#   ./scripts/prepare-release.sh --bump minor            # bump X.Y.Z -> X.(Y+1).0
#   ./scripts/prepare-release.sh --bump major            # bump X.Y.Z -> (X+1).0.0
#   ./scripts/prepare-release.sh --set-version 2.1.0     # set an explicit version
#   SKIP_INSTALL_TESTS=1 ./scripts/prepare-release.sh    # skip the slow uv-install tests
#
# Requires: uv (https://docs.astral.sh/uv/)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SKIP_TESTS=0
SKIP_DOCS=0
SKIP_EXAMPLES=0
SKIP_BUILD=0
SKIP_INSTALL_TESTS="${SKIP_INSTALL_TESTS:-0}"
BUMP=""
SET_VERSION=""

while [ $# -gt 0 ]; do
    case "$1" in
        --skip-tests) SKIP_TESTS=1 ;;
        --skip-docs) SKIP_DOCS=1 ;;
        --skip-examples) SKIP_EXAMPLES=1 ;;
        --skip-build) SKIP_BUILD=1 ;;
        --skip-install-tests) SKIP_INSTALL_TESTS=1 ;;
        --bump)
            shift
            BUMP="${1:-}"
            if [[ "$BUMP" != "patch" && "$BUMP" != "minor" && "$BUMP" != "major" ]]; then
                echo "error: --bump requires patch|minor|major" >&2
                exit 1
            fi
            ;;
        --set-version)
            shift
            SET_VERSION="${1:-}"
            if [[ ! "$SET_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                echo "error: --set-version requires a X.Y.Z version string" >&2
                exit 1
            fi
            ;;
        -h|--help)
            grep -E '^#( |$)' "$0" | sed -E 's/^# ?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
    shift
done

if [ -n "$BUMP" ] && [ -n "$SET_VERSION" ]; then
    echo "error: use either --bump or --set-version, not both" >&2
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "error: uv is not installed. See https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
fi

step() {
    echo ""
    echo "==================================================================="
    echo "  $1"
    echo "==================================================================="
}

step "Syncing dependencies (uv sync --all-extras)"
uv sync --all-extras

step "Linting (ruff check)"
uv run ruff check .

step "Type checking (mypy)"
uv run mypy odr_bootstrap

if [ "$SKIP_TESTS" -eq 0 ]; then
    step "Running unit tests with coverage (pytest)"
    uv run pytest

    if [ "$SKIP_INSTALL_TESTS" -eq 0 ]; then
        step "Running uv installation tests (pytest -m install)"
        uv run pytest -m install tests/test_installation.py --no-cov
    else
        echo "Skipping install tests (SKIP_INSTALL_TESTS=1)"
    fi
else
    echo "Skipping tests (--skip-tests)"
fi

if [ "$SKIP_EXAMPLES" -eq 0 ]; then
    step "Regenerating example figures (examples/example.py)"
    # Writes calibration_*.png into the repo root, examples/, and
    # docs/source/_static/ (see OUTPUT_DIR / DOCS_STATIC_DIR in the script),
    # keeping README.md and the Sphinx docs in sync with the current code.
    uv run python examples/example.py
else
    echo "Skipping example regeneration (--skip-examples)"
fi

if [ "$SKIP_DOCS" -eq 0 ]; then
    step "Rebuilding Sphinx documentation"
    uv run --extra docs sphinx-build -b html docs/source docs/build/html
    echo "Documentation built: docs/build/html/index.html"
else
    echo "Skipping docs build (--skip-docs)"
fi

if [ -n "$BUMP" ] || [ -n "$SET_VERSION" ]; then
    step "Bumping version"
    # pyproject.toml's [project] version is the authoritative version (used
    # by uv/hatchling for the build); odr_bootstrap/__init__.py's
    # __version__ is kept in sync for runtime introspection.
    CURRENT_VERSION="$(grep -m1 '^version = ' pyproject.toml | sed -E 's/version = "([^"]+)"/\1/')"

    if [ -n "$SET_VERSION" ]; then
        NEW_VERSION="$SET_VERSION"
    else
        IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"
        case "$BUMP" in
            major) NEW_VERSION="$((MAJOR + 1)).0.0" ;;
            minor) NEW_VERSION="${MAJOR}.$((MINOR + 1)).0" ;;
            patch) NEW_VERSION="${MAJOR}.${MINOR}.$((PATCH + 1))" ;;
        esac
    fi

    echo "Bumping version: $CURRENT_VERSION -> $NEW_VERSION"
    sed -i.bak -E "s/^version = \"[^\"]+\"/version = \"${NEW_VERSION}\"/" pyproject.toml
    sed -i.bak -E "s/^__version__ = \"[^\"]+\"/__version__ = \"${NEW_VERSION}\"/" odr_bootstrap/__init__.py
    rm -f odr_bootstrap/__init__.py.bak pyproject.toml.bak

    step "Refreshing uv.lock for new version"
    uv lock
else
    echo "Skipping version bump (pass --bump patch|minor|major or --set-version X.Y.Z)"
fi

if [ "$SKIP_BUILD" -eq 0 ]; then
    step "Clearing old release artifacts and building distribution (uv build)"
    rm -rf dist build ./*.egg-info
    uv build
    ls -la dist
else
    echo "Skipping package build (--skip-build)"
fi

step "Summary of changed files (git status)"
git status --short

echo ""
echo "==================================================================="
echo "  Done. Review the changes above (images/docs/dist), then commit"
echo "  and push, e.g.:"
echo ""
echo "    git add -A"
echo "    git commit -m \"Rebuild examples, docs, and dist artifacts\""
echo "    git push"
echo "==================================================================="
