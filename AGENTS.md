# Agent Instructions

## Before every release

Run `scripts/prepare-release.sh` (or `make prepare-release`) before pushing a
release / publishing to PyPI. This script should be kept up to date as the
project changes (new build steps, new docs targets, new test suites, etc.) —
if you add a step to the release process, add it here too.

```bash
./scripts/prepare-release.sh
# or
make prepare-release
```

The script (using `uv` throughout):

1. Syncs dependencies (`uv sync --all-extras`)
2. Lints and type-checks (`ruff check`, `mypy`)
3. Runs the unit test suite with coverage, plus the `uv`-installation tests
4. Regenerates the example figures (`examples/example.py`), which updates the
   calibration PNGs in the repo root, `examples/`, and `docs/source/_static/`
   so images linked from README.md and the Sphinx docs stay current
5. Rebuilds the Sphinx documentation (`docs/build/html`)
6. Bumps the package version and refreshes `uv.lock`, if `--bump
   patch|minor|major` or `--set-version X.Y.Z` was passed (skipped by
   default — pass one of these flags to actually cut a new version)
7. Clears out old `dist/` artifacts and builds a fresh sdist/wheel
   (`uv build`)
8. Prints a `git status --short` summary to review before committing

Useful invocations:

```bash
./scripts/prepare-release.sh --bump patch          # bump X.Y.Z -> X.Y.(Z+1), refresh uv.lock, full pipeline
make prepare-release BUMP=patch                    # same, via Makefile
./scripts/prepare-release.sh --set-version 2.1.0    # set an explicit version
./scripts/prepare-release.sh --skip-install-tests   # skip the slow uv-venv install tests
./scripts/prepare-release.sh --skip-tests           # only rebuild examples/docs/dist
```

Review the `git status` output (regenerated PNGs, version bump, docs, dist)
before committing, tagging, and pushing/publishing.

**Keep this file and `scripts/prepare-release.sh` in sync** — if the release
process changes (new checks, new artifacts to regenerate, a different
versioning scheme, etc.), update the script and this note together.
