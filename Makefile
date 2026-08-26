.PHONY: help install sync test test-cov lint type-check format clean build release-check release publish publish-test docs

help:
	@echo "ODR Bootstrap Package Management"
	@echo ""
	@echo "Setup:"
	@echo "  make sync           Sync dependencies with uv"
	@echo "  make install        Install package in development mode"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run tests"
	@echo "  make test-cov       Run tests with coverage report"
	@echo "  make lint           Check code style with ruff"
	@echo "  make type-check     Check types with mypy"
	@echo "  make format         Format code with ruff (in-place)"
	@echo ""
	@echo "Building & Releases:"
	@echo "  make build          Build distribution (wheel + sdist)"
	@echo "  make docs           Build Sphinx docs"
	@echo "  make release-check  Run full validation before a release"
	@echo "  make publish-test   Publish to TestPyPI"
	@echo "  make publish        Publish to PyPI (uses uv publish)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Remove build artifacts"

sync:
	uv sync --all-extras

install:
	uv sync --all-extras
	uv pip install -e ".[dev,docs,test]"

test:
	uv run pytest

test-cov:
	uv run pytest --cov=odr_bootstrap --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated: htmlcov/index.html"

lint:
	uv run ruff check .

type-check:
	uv run mypy odr_bootstrap

format:
	uv run ruff format .

clean:
	rm -rf build dist *.egg-info
	rm -rf htmlcov .coverage .mypy_cache
	rm -rf .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

build: clean
	uv build

docs:
	uv run --extra docs sphinx-build -b html docs/source docs/build/html
	@echo "Documentation built: docs/build/html/index.html"

release-check: clean
	uv sync --all-extras
	uv run pytest
	uv run ruff check .
	uv run mypy odr_bootstrap
	uv run --extra docs sphinx-build -b html docs/source docs/build/html
	uv build
	@echo "Release validation complete."

publish-test: release-check
	@echo "Publishing to TestPyPI..."
	uv publish --publish-url https://test.pypi.org/legacy/

publish: release-check
	@echo "Publishing to PyPI..."
	uv publish

.DEFAULT_GOAL := help
