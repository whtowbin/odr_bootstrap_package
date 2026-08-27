.PHONY: help install sync test test-cov test-install test-all-versions lint type-check format clean build release-check prepare-release release publish publish-test docs regen-examples

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
	@echo "  make test-install   Run end-to-end uv installation tests (builds package, installs into fresh venvs)"
	@echo "  make test-all-versions  Run lint/type-check/tests/install-tests across all supported Python versions (3.11-3.13)"
	@echo "  make lint           Check code style with ruff"
	@echo "  make type-check     Check types with mypy"
	@echo "  make format         Format code with ruff (in-place)"
	@echo ""
	@echo "Building & Releases:"
	@echo "  make build          Build distribution (wheel + sdist)"
	@echo "  make docs           Build Sphinx docs (regenerates example assets first)"
	@echo "  make regen-examples Regenerate calibration plots and HTML tables"
	@echo "  make release-check  Run full validation before a release"
	@echo "  make prepare-release  Rebuild examples/docs/images, run tests, and build dist before pushing"
	@echo "  make prepare-release BUMP=patch   Same, plus bump version (patch|minor|major) and uv.lock"
	@echo "  make publish-test   Publish to TestPyPI"
	@echo "  make publish        Publish to PyPI (uses uv publish)"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Remove build artifacts"

sync:
	uv sync --all-extras

install:
	uv sync --all-extras

test:
	uv run pytest

test-cov:
	uv run pytest --cov=odr_bootstrap --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated: htmlcov/index.html"

test-install:
	uv run pytest -m install tests/test_installation.py --no-cov

test-all-versions:
	./scripts/test-all-python-versions.sh

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

regen-examples:
	uv run --extra examples python examples/example.py
	@echo "Example artifacts regenerated: calibration plots and unknown_concentrations.html"

docs: regen-examples
	uv run --extra docs sphinx-build -b html docs/source docs/build/html
	@echo "Documentation built: docs/build/html/index.html"

release-check: clean
	uv sync --all-extras
	uv run pytest
	uv run pytest -m install tests/test_installation.py --no-cov
	uv run ruff check .
	uv run mypy odr_bootstrap
	$(MAKE) regen-examples
	uv run --extra docs sphinx-build -b html docs/source docs/build/html
	uv build
	@echo "Release validation complete."

prepare-release:
	./scripts/prepare-release.sh $(if $(BUMP),--bump $(BUMP),)$(if $(SET_VERSION), --set-version $(SET_VERSION),)

publish-test: release-check
	@echo "Publishing to TestPyPI..."
	uv publish --publish-url https://test.pypi.org/legacy/

publish: release-check
	@echo "Publishing to PyPI..."
	uv publish

.DEFAULT_GOAL := help
