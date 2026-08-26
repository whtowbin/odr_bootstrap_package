#!/bin/bash
# Publish odr-bootstrap using uv's build and publish pipeline.
#
# Usage:
#   ./scripts/publish.sh             # Publish to PyPI (requires UV_PUBLISH_TOKEN or trusted publishing)
#   TESTPYPI=1 ./scripts/publish.sh  # Publish to TestPyPI

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== ODR Bootstrap Publisher ===${NC}"

if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed.${NC}"
    echo "Install it from: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Run the same validation used in the release workflow.
echo -e "${YELLOW}Running pre-release checks...${NC}"
uv sync --all-extras
uv run pytest
uv run ruff check .
uv run mypy odr_bootstrap
uv run --extra docs sphinx-build -b html docs/source docs/build/html

# Build distribution
echo -e "${YELLOW}Building release artifacts...${NC}"
uv build

# Check that artifacts were created
shopt -s nullglob
WHEELS=(dist/*.whl)
SDISTS=(dist/*.tar.gz)
if [ "${#WHEELS[@]}" -eq 0 ] || [ "${#SDISTS[@]}" -eq 0 ]; then
    echo -e "${RED}Error: build failed; no distribution artifacts were produced.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build successful${NC}"
echo "  Wheel: ${WHEELS[0]}"
echo "  Source distribution: ${SDISTS[0]}"

if [ "${TESTPYPI:-0}" = "1" ]; then
    echo -e "${YELLOW}Publishing to TestPyPI...${NC}"
    uv publish --publish-url https://test.pypi.org/legacy/
    echo -e "${GREEN}✓ Published to TestPyPI${NC}"
else
    echo -e "${YELLOW}Publishing to PyPI...${NC}"
    uv publish
    echo -e "${GREEN}✓ Published to PyPI${NC}"
fi
