"""Parity tests between scipy.odr and odrpack.

scipy is deprecating its ``scipy.odr`` module (see
https://docs.scipy.org/doc/scipy/reference/odr.html and the discussion at
https://discuss.scientific-python.org/t/rfc-deprecating-scipy-odr/2166/20)
and recommends migrating to `odrpack <https://pypi.org/project/odrpack/>`_,
which wraps the same underlying ODRPACK95 Fortran solver used by
``scipy.odr``.

These tests fit the README/tutorial example datasets with both
``scipy.odr`` and ``odrpack`` directly (independent of anything in
``odr_bootstrap.core``) and assert that the fitted parameters, parameter
standard errors, and residual variance agree within 2%. This documents
that the migration performed in ``odr_bootstrap/core.py`` (see
``fit_odr_linear``) does not change the statistics users get out of the
package.

These tests require ``scipy`` (for ``scipy.odr``, still a project
dependency) and ``odrpack``.
"""

from __future__ import annotations

import numpy as np
import pytest

odr = pytest.importorskip("scipy.odr", reason="scipy.odr not available")
odrpack = pytest.importorskip("odrpack", reason="odrpack not installed")

RTOL = 0.02  # 2% relative tolerance


def _linear_with_intercept_scipy(beta: np.ndarray, x: np.ndarray) -> np.ndarray:
    return beta[0] * x + beta[1]


def _linear_with_intercept_odrpack(x: np.ndarray, beta: np.ndarray) -> np.ndarray:
    return beta[0] * x + beta[1]


def _linear_through_origin_scipy(beta: np.ndarray, x: np.ndarray) -> np.ndarray:
    return beta[0] * x


def _linear_through_origin_odrpack(x: np.ndarray, beta: np.ndarray) -> np.ndarray:
    return beta[0] * x


def _fit_scipy(
    x: np.ndarray,
    y: np.ndarray,
    x_err: np.ndarray,
    y_err: np.ndarray,
    beta0: list[float],
    fit_intercept: bool,
) -> tuple[np.ndarray, np.ndarray, float]:
    model = odr.Model(
        _linear_with_intercept_scipy if fit_intercept else _linear_through_origin_scipy
    )
    data = odr.RealData(x, y, sx=x_err, sy=y_err)
    myodr = odr.ODR(data, model, beta0=beta0)
    myodr.set_job(fit_type=0)
    out = myodr.run()
    return (
        np.asarray(out.beta, dtype=float),
        np.asarray(out.sd_beta, dtype=float),
        float(out.res_var),
    )


def _fit_odrpack(
    x: np.ndarray,
    y: np.ndarray,
    x_err: np.ndarray,
    y_err: np.ndarray,
    beta0: list[float],
    fit_intercept: bool,
) -> tuple[np.ndarray, np.ndarray, float]:
    f = _linear_with_intercept_odrpack if fit_intercept else _linear_through_origin_odrpack
    sol = odrpack.odr_fit(
        f,
        x,
        y,
        beta0,
        weight_x=1.0 / np.square(x_err),
        weight_y=1.0 / np.square(y_err),
    )
    return (
        np.asarray(sol.beta, dtype=float),
        np.asarray(sol.sd_beta, dtype=float),
        float(sol.res_var),
    )


# Example datasets pulled directly from README.md ("Quick Start") and
# docs/source/tutorial.rst.
README_DATA = dict(
    x=np.array([0.1, 0.5, 1.0, 2.0, 5.0]),
    y=np.array([45.0, 200.0, 350.0, 700.0, 1450.0]),
    x_err=np.array([0.01, 0.05, 0.1, 0.2, 0.5]),
    y_err=np.array([5.0, 20.0, 35.0, 60.0, 120.0]),
)

TUTORIAL_DATA = dict(
    x=np.array([0.1, 0.5, 1.0, 2.0, 5.0, 10.0]),
    y=np.array([28.0, 78.0, 143.0, 265.0, 637.0, 1282.0]),
    x_err=np.array([0.01, 0.05, 0.1, 0.2, 0.5, 1.0]),
    y_err=np.array([20.0, 30.0, 50.0, 60.0, 100.0, 150.0]),
)


@pytest.mark.parametrize(
    "dataset,fit_intercept,beta0",
    [
        pytest.param(README_DATA, True, [1.0, 0.0], id="readme-intercept"),
        pytest.param(README_DATA, False, [300.0], id="readme-no-intercept"),
        pytest.param(TUTORIAL_DATA, True, [1.0, 0.0], id="tutorial-intercept"),
        pytest.param(TUTORIAL_DATA, False, [125.0], id="tutorial-no-intercept"),
    ],
)
def test_odrpack_matches_scipy_odr(
    dataset: dict[str, np.ndarray], fit_intercept: bool, beta0: list[float]
) -> None:
    scipy_beta, scipy_sd, scipy_res_var = _fit_scipy(
        dataset["x"], dataset["y"], dataset["x_err"], dataset["y_err"],
        beta0, fit_intercept,
    )
    odrpack_beta, odrpack_sd, odrpack_res_var = _fit_odrpack(
        dataset["x"], dataset["y"], dataset["x_err"], dataset["y_err"],
        beta0, fit_intercept,
    )

    np.testing.assert_allclose(odrpack_beta, scipy_beta, rtol=RTOL)
    np.testing.assert_allclose(odrpack_sd, scipy_sd, rtol=RTOL)
    assert odrpack_res_var == pytest.approx(scipy_res_var, rel=RTOL)
