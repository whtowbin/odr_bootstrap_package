#!/bin/bash
# Publish odr-bootstrap to PyPI using uv build
# 
# This script builds the package and publishes it to PyPI.
# It should typically be run by GitHub Actions on release creation.
#
# Usage:
#   ./scripts/publish.sh             # Publish to PyPI (requires PyPI token)
#   TESTPYPI=1 ./scripts/publish.sh  # Publish to TestPyPI (test environment)

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ODR Bootstrap Publisher ===${NC}"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed${NC}"
    echo "Install from: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Check if twine is installed
if ! command -v twine &> /dev/null; then
    echo -e "${YELLOW}Warning: twine is not installed${NC}"
    echo "Installing twine..."
    pip install twine
fi

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info

# Build distribution
echo -e "${YELLOW}Building distribution with uv...${NC}"
uv build

# Check build artifacts
if [ ! -f "dist"/*.whl ] || [ ! -f "dist"/*.tar.gz ]; then
    echo -e "${RED}Error: Build failed - no artifacts found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build successful${NC}"
echo "  Wheel: $(ls dist/*.whl)"
echo "  Sdist: $(ls dist/*.tar.gz)"

# Publish
if [ "$TESTPYPI" = "1" ]; then
    REPO="testpypi"
    REPO_URL="https://test.pypi.org"
    echo -e "${YELLOW}Publishing to TestPyPI...${NC}"
else
    REPO="pypi"
    REPO_URL="https://pypi.org"
    echo -e "${YELLOW}Publishing to PyPI...${NC}"
fi

twine upload --repository "$REPO" dist/*

echo -e "${GREEN}✓ Publication successful!${NC}"
echo "  View at: $REPO_URL/project/odr-bootstrap/"
