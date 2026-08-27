"""End-to-end installation tests.

These tests verify that the package can actually be installed with ``uv``
using the exact commands documented in :mod:`README.md` and
``docs/source/installation.rst``. Unlike the rest of the test suite, these
tests do not import ``odr_bootstrap`` directly from the working tree -
instead they build a real sdist/wheel, create an isolated environment with
``uv``, install the package into it (mirroring the README/docs), and then
run a small script inside that environment to confirm the package is
importable and usable.

They are slower than the rest of the suite (they build the package and
create virtual environments), so they are marked with the ``install``
marker and are skipped by default in the coverage-focused ``pytest``
invocation used elsewhere in this project. Run them explicitly with::

    uv run pytest -m install
    # or
    make test-install
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.install

REPO_ROOT = Path(__file__).resolve().parent.parent

# A minimal script that mirrors the "Verify Installation" section of
# docs/source/installation.rst and the Quick Start section of README.md.
_VERIFY_SCRIPT = """
import odr_bootstrap
import numpy as np
from odr_bootstrap import (
    fit_defaults,
    fit_odr_linear,
    bootstrap_odr_fit,
    evaluate_confidence,
    odr_bootstrap as odr_bootstrap_fn,
    gaussian_aggregate,
    plot_regression,
    plot_density,
    plot_calibration_estimates,
)

assert isinstance(odr_bootstrap.__version__, str) and odr_bootstrap.__version__

x = np.array([0.1, 0.5, 1.0, 2.0, 5.0])
y = np.array([45.0, 200.0, 350.0, 700.0, 1450.0])
x_err = np.array([0.01, 0.05, 0.1, 0.2, 0.5])
y_err = np.array([5.0, 20.0, 35.0, 60.0, 120.0])

defaults = fit_defaults(x, y)
params, param_errors = fit_odr_linear(x, y, x_err, y_err)
assert len(params) == 2

confidence_data, best_fit_params, points, all_params, _ = odr_bootstrap_fn(
    x=x,
    y=y,
    x_err=x_err,
    y_err=y_err,
    resample_draws=25,
    initial_guess=defaults["initial_guess"],
    line_max=defaults["line_max"],
    line_interval=defaults["line_interval"],
)
assert best_fit_params is not None

print("INSTALL_CHECK_OK", odr_bootstrap.__version__)
"""


def _require_uv() -> str:
    uv_path = shutil.which("uv")
    if uv_path is None:
        pytest.skip("uv is not installed; cannot run installation tests")
    return uv_path


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=600,
    )


@pytest.fixture(scope="module")
def uv_exe() -> str:
    return _require_uv()


@pytest.fixture(scope="module")
def built_distributions(uv_exe: str, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Build the sdist and wheel exactly as ``uv build`` / ``make build`` would."""
    build_dir = tmp_path_factory.mktemp("dist")
    result = _run([uv_exe, "build", "--out-dir", str(build_dir)], cwd=REPO_ROOT)
    assert result.returncode == 0, (
        f"uv build failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    wheels = list(build_dir.glob("*.whl"))
    sdists = list(build_dir.glob("*.tar.gz"))
    assert wheels, f"No wheel produced in {build_dir}"
    assert sdists, f"No sdist produced in {build_dir}"
    return build_dir


def _make_venv(uv_exe: str, venv_dir: Path, python: str | None = None) -> Path:
    cmd = [uv_exe, "venv", str(venv_dir)]
    if python:
        cmd += ["--python", python]
    result = _run(cmd, cwd=REPO_ROOT)
    assert result.returncode == 0, (
        f"uv venv failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    python_bin = venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / (
        "python.exe" if sys.platform == "win32" else "python"
    )
    assert python_bin.exists(), f"Expected venv python at {python_bin}"
    return python_bin


def _verify_in_env(python_bin: Path, tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    script_path = tmp_path / "verify_install.py"
    script_path.write_text(_VERIFY_SCRIPT)
    result = subprocess.run(
        [str(python_bin), str(script_path)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        f"Verification script failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "INSTALL_CHECK_OK" in result.stdout


class TestUvInstallFromWheel:
    """Mirrors: `uv pip install odr-bootstrap` (README/docs, "With uv")."""

    def test_uv_pip_install_wheel(
        self, uv_exe: str, built_distributions: Path, tmp_path: Path
    ) -> None:
        wheel = next(built_distributions.glob("*.whl"))
        venv_dir = tmp_path / "venv"
        python_bin = _make_venv(uv_exe, venv_dir)

        install = _run(
            [uv_exe, "pip", "install", "--python", str(python_bin), str(wheel)],
        )
        assert install.returncode == 0, (
            f"uv pip install (wheel) failed:\nstdout:\n{install.stdout}"
            f"\nstderr:\n{install.stderr}"
        )
        _verify_in_env(python_bin, tmp_path)


class TestUvInstallFromSdist:
    """Mirrors installing the sdist (equivalent to installing from PyPI's
    source distribution)."""

    def test_uv_pip_install_sdist(
        self, uv_exe: str, built_distributions: Path, tmp_path: Path
    ) -> None:
        sdist = next(built_distributions.glob("*.tar.gz"))
        venv_dir = tmp_path / "venv"
        python_bin = _make_venv(uv_exe, venv_dir)

        install = _run(
            [uv_exe, "pip", "install", "--python", str(python_bin), str(sdist)],
        )
        assert install.returncode == 0, (
            f"uv pip install (sdist) failed:\nstdout:\n{install.stdout}"
            f"\nstderr:\n{install.stderr}"
        )
        _verify_in_env(python_bin, tmp_path)


class TestUvAddFromLocalPath:
    """Mirrors: `uv add odr-bootstrap` by adding the built wheel as a
    dependency to a throwaway uv project."""

    def test_uv_add_wheel_into_project(
        self, uv_exe: str, built_distributions: Path, tmp_path: Path
    ) -> None:
        wheel = next(built_distributions.glob("*.whl"))
        project_dir = tmp_path / "consumer_project"
        project_dir.mkdir()

        init = _run(
            [uv_exe, "init", "--no-workspace", "--python", "3.11", "."],
            cwd=project_dir,
        )
        assert init.returncode == 0, (
            f"uv init failed:\nstdout:\n{init.stdout}\nstderr:\n{init.stderr}"
        )

        add = _run([uv_exe, "add", str(wheel)], cwd=project_dir)
        assert add.returncode == 0, (
            f"uv add failed:\nstdout:\n{add.stdout}\nstderr:\n{add.stderr}"
        )

        run_result = _run(
            [uv_exe, "run", "python", "-c", "import odr_bootstrap; print(odr_bootstrap.__version__)"],
            cwd=project_dir,
        )
        assert run_result.returncode == 0, (
            f"uv run import check failed:\nstdout:\n{run_result.stdout}"
            f"\nstderr:\n{run_result.stderr}"
        )
        assert run_result.stdout.strip()


class TestFromSourceWithUvSync:
    """Mirrors the README/docs "From source" instructions:

        git clone ...
        cd odr_bootstrap_package
        uv sync
    """

    def test_uv_sync_from_source_checkout(self, uv_exe: str, tmp_path: Path) -> None:
        # Copy the repository (tracked files only) into a clean directory so
        # this test doesn't mutate the real working tree's lockfile/venv and
        # accurately mimics a fresh `git clone`.
        checkout_dir = tmp_path / "checkout"
        ls_files = _run(["git", "ls-files"], cwd=REPO_ROOT)
        assert ls_files.returncode == 0, "git ls-files failed"
        files = [f for f in ls_files.stdout.splitlines() if f.strip()]
        assert files, "No tracked files found via git ls-files"

        for rel_path in files:
            src = REPO_ROOT / rel_path
            if not src.is_file():
                continue
            dst = checkout_dir / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        sync = _run([uv_exe, "sync", "--all-extras"], cwd=checkout_dir)
        assert sync.returncode == 0, (
            f"uv sync --all-extras failed:\nstdout:\n{sync.stdout}"
            f"\nstderr:\n{sync.stderr}"
        )

        check = _run(
            [
                uv_exe,
                "run",
                "python",
                "-c",
                "import odr_bootstrap; print(odr_bootstrap.__version__)",
            ],
            cwd=checkout_dir,
        )
        assert check.returncode == 0, (
            f"uv run import check failed:\nstdout:\n{check.stdout}"
            f"\nstderr:\n{check.stderr}"
        )
        assert check.stdout.strip()


@pytest.mark.parametrize("python_version", ["3.11", "3.12", "3.13"])
class TestInstallAcrossSupportedPythonVersions:
    """Verify the wheel installs and imports across every Python version the
    project claims to support (see the classifiers / `requires-python` in
    pyproject.toml and the badges in README.md)."""

    def test_install_and_import(
        self,
        uv_exe: str,
        built_distributions: Path,
        tmp_path: Path,
        python_version: str,
    ) -> None:
        wheel = next(built_distributions.glob("*.whl"))
        venv_dir = tmp_path / f"venv-{python_version}"

        venv_result = _run(
            [uv_exe, "venv", str(venv_dir), "--python", python_version],
            cwd=REPO_ROOT,
        )
        if venv_result.returncode != 0:
            pytest.skip(
                f"Python {python_version} unavailable via uv: {venv_result.stderr}"
            )

        python_bin = venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / (
            "python.exe" if sys.platform == "win32" else "python"
        )

        install = _run(
            [uv_exe, "pip", "install", "--python", str(python_bin), str(wheel)],
        )
        assert install.returncode == 0, (
            f"uv pip install failed for Python {python_version}:\n"
            f"stdout:\n{install.stdout}\nstderr:\n{install.stderr}"
        )
        _verify_in_env(python_bin, tmp_path / f"verify-{python_version}")
