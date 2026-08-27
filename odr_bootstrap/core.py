"""
ODR bootstrapping utilities for SIMS calibration analysis.

This module provides orthogonal distance regression (ODR) with uncertainties
in both x and y, bootstrap resampling of fit parameters, confidence interval
evaluation for predicted fit lines, and calibration estimate plotting.

Dependencies
------------
matplotlib
numpy
pandas
scipy

Changelog
---------
August 2025:
  - API refactor: all public names now follow PEP 8 snake_case.
  - Added fit_defaults() helper to derive initial_guess, line_max, and
    line_interval automatically from data via a least-squares pre-fit.
  - Removed dead parameters: sigma (plot_regression), plot (odr_bootstrap),
    cut_off (gaussian_aggregate), and **kwargs aliases in evaluate_confidence.
  - Removed duplicate nested function definitions inside fitting functions.
  - fit_intercept default unified to True across all functions.
  - line_max / line_interval are now required in evaluate_confidence;
    odr_bootstrap auto-derives them when None.

April 2025:
  - Fixed zero-intercept ODR initialization: properly wrap slope-only
    initial guess in list for scipy.odr compatibility.
  - Updated deprecated np.trapz to np.trapezoid for scipy 1.15+ compatibility.
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from scipy import odr


def _as_float_array(values: np.ndarray | list[float]) -> np.ndarray:
    """Convert array-like inputs into a float ndarray for downstream math."""
    return np.asarray(values, dtype=float)


def linear_with_intercept(
    p: np.ndarray | list[float], x: np.ndarray | list[float]
) -> np.ndarray:
    """
    Evaluate a line with slope and intercept: y = p[0]*x + p[1].

    Parameters
    ----------
    p : array-like
        Parameter vector [slope, intercept].
    x : array-like
        Independent variable values.

    Returns
    -------
    ndarray
        Evaluated y values.
    """
    params = _as_float_array(p)
    x_arr = _as_float_array(x)
    return np.asarray(float(params[0]) * x_arr + float(params[1]), dtype=float)


def linear_through_origin(
    p: np.ndarray | list[float], x: np.ndarray | list[float]
) -> np.ndarray:
    """
    Evaluate a line through the origin: y = p[0]*x.

    Parameters
    ----------
    p : array-like
        Parameter vector [slope].
    x : array-like
        Independent variable values.

    Returns
    -------
    ndarray
        Evaluated y values.
    """
    params = _as_float_array(p)
    x_arr = _as_float_array(x)
    return np.asarray(float(params[0]) * x_arr, dtype=float)


def fit_defaults(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    fit_intercept: bool = True,
) -> dict[str, Any]:
    """
    Compute sensible default fitting parameters from data.

    Uses a least-squares pre-fit (``numpy.polyfit``) to derive a starting
    parameter guess and an x-grid range appropriate for the data.

    Parameters
    ----------
    x : array-like
        Independent variable values.
    y : array-like
        Dependent variable values.
    fit_intercept : bool, optional
        If True, include an intercept in the initial guess. Default is True.

    Returns
    -------
    dict
        initial_guess : list of float
            ``[slope, intercept]`` (or ``[slope]`` when fit_intercept is False)
            derived from a least-squares fit.
        line_max : float
            Upper x-value for the evaluation grid: ``max(x) * 1.1``.
        line_interval : float
            Grid step: ``line_max / 1000``.

    Raises
    ------
    ValueError
        If fewer than 2 finite data points are available.
    """
    x_arr = _as_float_array(x)
    y_arr = _as_float_array(y)

    valid = np.isfinite(x_arr) & np.isfinite(y_arr)
    x_clean = x_arr[valid]
    y_clean = y_arr[valid]

    if len(x_clean) < 2:
        raise ValueError(
            "At least 2 finite data points are required to compute fit defaults."
        )

    slope, intercept = np.polyfit(x_clean, y_clean, 1)
    initial_guess = (
        [float(slope), float(intercept)] if fit_intercept else [float(slope)]
    )

    line_max = float(np.max(x_clean)) * 1.1
    line_interval = max(line_max / 1000.0, 1e-10)

    return {
        "initial_guess": initial_guess,
        "line_max": line_max,
        "line_interval": line_interval,
    }


def fit_odr_linear(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    x_err: np.ndarray | list[float],
    y_err: np.ndarray | list[float],
    fit_intercept: bool = True,
    initial_guess: list[float] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Fit a linear model using orthogonal distance regression (ODR).

    Parameters
    ----------
    x : array-like
        Independent variable values.
    y : array-like
        Dependent variable values.
    x_err : array-like
        Uncertainties in x.
    y_err : array-like
        Uncertainties in y.
    fit_intercept : bool, optional
        If True, fit ``y = a*x + b``. If False, fit ``y = a*x`` through the
        origin. Default is True.
    initial_guess : list of float, optional
        Starting parameters. For intercept fits supply ``[slope, intercept]``;
        for zero-intercept fits supply ``[slope]``. Default is None, in which
        case a least-squares estimate is computed automatically via
        ``fit_defaults``.

    Returns
    -------
    tuple
        params : ndarray
            Fitted parameter array.
        param_errors : ndarray
            1-sigma uncertainty array.
    """
    if initial_guess is None:
        initial_guess = fit_defaults(x, y, fit_intercept=fit_intercept)["initial_guess"]

    beta0 = list(initial_guess)
    if fit_intercept:
        beta0 = beta0[:2]
        model = odr.Model(linear_with_intercept)
    else:
        beta0 = [beta0[0]]
        model = odr.Model(linear_through_origin)

    data = odr.RealData(x, y, sx=x_err, sy=y_err)
    myodr = odr.ODR(data, model, beta0=beta0)
    myodr.set_job(fit_type=0)
    out = myodr.run()

    params = np.asarray(out.beta, dtype=float)
    param_errors = np.asarray(out.sd_beta, dtype=float)
    return params, param_errors


def fit_odr_linear_debug(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    x_err: np.ndarray | list[float],
    y_err: np.ndarray | list[float],
    fit_intercept: bool = True,
    initial_guess: list[float] | None = None,
) -> tuple[np.ndarray, np.ndarray, Any]:
    """
    Fit a linear model using ODR and return the full scipy ODR output.

    Identical to ``fit_odr_linear`` but also returns the raw
    ``scipy.odr.Output`` object for inspection and diagnostics.

    Parameters
    ----------
    x : array-like
        Independent variable values.
    y : array-like
        Dependent variable values.
    x_err : array-like
        Uncertainties in x.
    y_err : array-like
        Uncertainties in y.
    fit_intercept : bool, optional
        If True, fit ``y = a*x + b``. If False, fit through the origin.
        Default is True.
    initial_guess : list of float, optional
        Starting parameters. Default is None; auto-derived from a
        least-squares fit.

    Returns
    -------
    tuple
        params : ndarray
        param_errors : ndarray
        odr_output : scipy.odr.Output
            Full ODR result object for diagnostics.
    """
    if initial_guess is None:
        initial_guess = fit_defaults(x, y, fit_intercept=fit_intercept)["initial_guess"]

    beta0 = list(initial_guess)
    if fit_intercept:
        beta0 = beta0[:2]
        model = odr.Model(linear_with_intercept)
    else:
        beta0 = [beta0[0]]
        model = odr.Model(linear_through_origin)

    data = odr.RealData(x, y, sx=x_err, sy=y_err)
    myodr = odr.ODR(data, model, beta0=beta0)
    myodr.set_job(fit_type=0)
    out = myodr.run()

    params = np.asarray(out.beta, dtype=float)
    param_errors = np.asarray(out.sd_beta, dtype=float)
    return params, param_errors, out


def bootstrap_odr_fit(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    x_err: np.ndarray | list[float],
    y_err: np.ndarray | list[float],
    resample_draws: int,
    fit_intercept: bool = True,
    initial_guess: list[float] | None = None,
) -> tuple[list[np.ndarray], list[pd.DataFrame]]:
    """
    Perform bootstrap resampling of ODR linear fits.

    Parameters
    ----------
    x : array-like
        Independent variable values.
    y : array-like
        Dependent variable values.
    x_err : array-like
        Uncertainties in x.
    y_err : array-like
        Uncertainties in y.
    resample_draws : int
        Number of bootstrap resamples to perform.
    fit_intercept : bool, optional
        If True, fit slope and intercept. If False, fit through the origin.
        Default is True.
    initial_guess : list of float, optional
        Starting parameters. Default is None; auto-derived from the cleaned
        data via ``fit_defaults``.

    Returns
    -------
    tuple
        fit_params : list of ndarray
            First element is the fit from the full dataset, followed by all
            bootstrap fits.
        subsamples : list of DataFrame
            Resampled DataFrames used for each bootstrap iteration.
    """
    def resample(count: int) -> np.ndarray:
        return np.random.randint(0, count, count)

    data = np.array([x, x_err, y, y_err]).T
    df = pd.DataFrame(data, columns=["x", "x_err", "y", "y_err"])
    df.dropna(inplace=True)

    if initial_guess is None:
        initial_guess = fit_defaults(
            df["x"], df["y"], fit_intercept=fit_intercept
        )["initial_guess"]

    guess = list(initial_guess)
    if not fit_intercept:
        guess = [guess[0]]

    length = len(df)
    opt, _ = fit_odr_linear(
        x=df["x"],
        y=df["y"],
        x_err=df["x_err"],
        y_err=df["y_err"],
        fit_intercept=fit_intercept,
        initial_guess=guess,
    )
    fit_params = [opt]
    subsamples = []

    for _ in range(resample_draws):
        sub = df.take(resample(length))
        opt, _ = fit_odr_linear(
            x=sub["x"],
            y=sub["y"],
            x_err=sub["x_err"],
            y_err=sub["y_err"],
            fit_intercept=fit_intercept,
            initial_guess=guess,
        )
        fit_params.append(opt)
        subsamples.append(sub)

    return fit_params, subsamples


def evaluate_confidence(
    fit_params: list[np.ndarray],
    line_max: int | float,
    line_interval: int | float,
    confidence_level: float = 0.95,
) -> pd.DataFrame:
    """
    Evaluate bootstrap confidence intervals for linear predictions.

    Parameters
    ----------
    fit_params : list of array-like
        Bootstrapped fit parameter vectors. Each element must contain either
        one value (slope only) or two values (slope and intercept).
    line_max : int or float
        Maximum x-value for the evaluation grid. Pass the ``line_max`` value
        returned by ``fit_defaults`` or supply a value appropriate for your
        data range.
    line_interval : int or float
        Step size for the evaluation grid. Pass the ``line_interval`` value
        returned by ``fit_defaults``, or use ``line_max / 1000`` as a
        starting point.
    confidence_level : float, optional
        Confidence level expressed as a fraction between 0 and 1.
        Default is 0.95.

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by x values with columns:
        ``neg_error_bound``, ``pos_error_bound``, ``best_fit``,
        ``percent_error_neg``, ``percent_error_pos``.

    Raises
    ------
    ValueError
        If ``line_interval`` is not positive, ``line_max`` is negative, or
        any parameter vector has more than two elements.
    """
    if line_interval <= 0:
        raise ValueError("line_interval must be positive.")
    if line_max < 0:
        raise ValueError("line_max must be non-negative.")

    first_param = np.asarray(fit_params[0], dtype=float)
    if len(first_param) > 2:
        raise ValueError(
            "fit_params has too many values per row. "
            "Each parameter vector must have 1 (slope) or 2 (slope, intercept) elements."
        )

    fit_func = (
        linear_with_intercept if len(first_param) == 2 else linear_through_origin
    )

    num_steps = max(0, int(round(float(line_max) / float(line_interval))))
    x = np.linspace(0.0, float(line_max), num_steps + 1)
    if len(x) == 0:
        x = np.array([0.0])

    evaluated = [fit_func(row, x) for row in fit_params]
    bootstrap_samples = pd.DataFrame(evaluated)

    confidence_ints = []
    for _, col in bootstrap_samples.items():
        histrange = (np.nanmin(col), np.nanmax(col))
        hist = np.histogram(col, bins=400, range=histrange)
        conf_int = stats.rv_histogram(hist).interval(confidence_level)
        confidence_ints.append(conf_int)

    results = pd.DataFrame(
        confidence_ints, columns=("neg_error_bound", "pos_error_bound")
    )
    results.index = x
    results["best_fit"] = evaluated[0]
    results["percent_error_neg"] = (
        results["best_fit"] - results["neg_error_bound"]
    ) / np.abs(results["best_fit"])
    results["percent_error_pos"] = (
        results["pos_error_bound"] - results["best_fit"]
    ) / np.abs(results["best_fit"])

    return results


def plot_regression(
    confidence_df: pd.DataFrame | list[pd.DataFrame],
    datapoints: pd.DataFrame | None = None,
    ax: Axes | None = None,
    ecolor: str | list[str] = "r",
    line_color: str | list[str] = "b",
    e_alpha: float | list[float] = 0.5,
    **kwargs: Any,
) -> Axes:
    """
    Plot a best-fit regression line with one or more shaded confidence bands.

    Parameters
    ----------
    confidence_df : pandas.DataFrame or list of pandas.DataFrame
        Output from ``evaluate_confidence`` with columns ``best_fit``,
        ``neg_error_bound``, and ``pos_error_bound``. A list overlays
        multiple confidence intervals on the same regression line.
    datapoints : pandas.DataFrame, optional
        DataFrame containing columns ``x``, ``y``, ``xerr``, and ``yerr``.
    ax : matplotlib.axes.Axes, optional
        Axis object to draw on. If None, the current axis is used.
    ecolor : str or list of str, optional
        Confidence-band color(s).
    line_color : str or list of str, optional
        Best-fit line color(s).
    e_alpha : float or list of float, optional
        Transparency for the confidence bands.
    **kwargs
        Additional keyword arguments forwarded to ``ax.plot`` (fit line) and
        ``ax.errorbar`` (data points).

    Returns
    -------
    matplotlib.axes.Axes
        Axis containing the regression plot.
    """
    if isinstance(confidence_df, list):
        if not confidence_df:
            raise ValueError("confidence_df must contain at least one DataFrame.")

        ax = ax if ax is not None else plt.gca()
        band_colors = (
            [ecolor] * len(confidence_df)
            if isinstance(ecolor, str)
            else list(ecolor)
        )
        band_alphas = (
            [e_alpha] * len(confidence_df)
            if isinstance(e_alpha, float)
            else list(e_alpha)
        )
        line_colors = (
            [line_color] * len(confidence_df)
            if isinstance(line_color, str)
            else list(line_color)
        )

        x_values = confidence_df[0]["best_fit"].index
        if datapoints is not None:
            x_values = np.asarray(datapoints["x"], dtype=float)

        if len(confidence_df) >= 2:
            conf_95 = confidence_df[0]
            conf_68 = confidence_df[1]
            x = conf_95["neg_error_bound"].index
            ax.fill_between(
                x,
                conf_95["neg_error_bound"],
                conf_95["pos_error_bound"],
                color=band_colors[0],
                alpha=band_alphas[0],
                linewidth=0,
                label="95% CI",
            )
            ax.fill_between(
                x,
                conf_68["neg_error_bound"],
                conf_68["pos_error_bound"],
                color=band_colors[1 % len(band_colors)],
                alpha=band_alphas[1 % len(band_alphas)],
                linewidth=0,
                label="68% CI",
            )
            best_fit_color = line_colors[0] if line_colors else "#0f766e"
            line_kwargs = dict(kwargs)
            line_kwargs.setdefault("linewidth", 2.0)
            ax.plot(
                x,
                conf_95["best_fit"],
                color=best_fit_color,
                label="Best fit",
                **line_kwargs,
            )
        else:
            conf = confidence_df[0]
            x = conf["neg_error_bound"].index
            ax.fill_between(
                x,
                conf["neg_error_bound"],
                conf["pos_error_bound"],
                color=band_colors[0],
                alpha=band_alphas[0],
                linewidth=0,
                label="95% CI",
            )
            best_fit_color = line_colors[0] if line_colors else "#0f766e"
            line_kwargs = dict(kwargs)
            line_kwargs.setdefault("linewidth", 2.0)
            ax.plot(
                x,
                conf["best_fit"],
                color=best_fit_color,
                label="Best fit",
                **line_kwargs,
            )

        if datapoints is not None:
            ax.errorbar(
                x=datapoints["x"],
                y=datapoints["y"],
                yerr=datapoints["yerr"],
                xerr=datapoints["xerr"],
                marker=".",
                fmt="g",
                linestyle="none",
                capsize=5,
                markeredgewidth=1,
                markersize=10,
                label=None,
                **kwargs,
            )

        x_values_arr = np.asarray(list(x_values), dtype=float)
        x_max = float(np.nanmax(x_values_arr)) if len(x_values_arr) else 0.0
        x_min = float(np.nanmin(x_values_arr)) if len(x_values_arr) else 0.0
        ax.set_xlim(left=min(x_min, 0.0), right=x_max * 1.05 + 1e-9)
        ax.legend(loc="best", frameon=True)
        return ax

    best_fit = confidence_df["best_fit"]
    neg_bound = confidence_df["neg_error_bound"]
    pos_bound = confidence_df["pos_error_bound"]

    x = neg_bound.index
    if ax is None:
        ax = plt.gca()

    ax.fill_between(x, neg_bound, pos_bound, color=ecolor, alpha=e_alpha)
    ax.plot(x, best_fit, color=line_color, **kwargs)

    x_max = (
        float(np.nanmax(np.asarray(list(x), dtype=float))) if len(x) else 0.0
    )
    if datapoints is not None:
        data_x = np.asarray(datapoints["x"], dtype=float)
        if len(data_x):
            x_max = max(x_max, float(np.nanmax(data_x)))
        ax.errorbar(
            x=datapoints["x"],
            y=datapoints["y"],
            yerr=datapoints["yerr"],
            xerr=datapoints["xerr"],
            marker=".",
            fmt="g",
            linestyle="none",
            capsize=5,
            markeredgewidth=1,
            markersize=10,
            label=None,
            **kwargs,
        )

    ax.set_xlim(
        left=min(float(np.nanmin(np.asarray(list(x), dtype=float))), 0.0),
        right=x_max * 1.05 + 1e-9,
    )
    return ax


def odr_bootstrap(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    x_err: np.ndarray | list[float],
    y_err: np.ndarray | list[float],
    resample_draws: int = 5000,
    line_max: int | float | None = None,
    line_interval: int | float | None = None,
    fit_intercept: bool = True,
    initial_guess: list[float] | None = None,
    confidence_level: float = 0.95,
    **kwargs: Any,
) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame, list[np.ndarray], list[pd.DataFrame]]:
    """
    Run bootstrap resampling for ODR linear fitting and compute confidence data.

    This is the top-level convenience function. It calls ``bootstrap_odr_fit``
    then ``evaluate_confidence`` and returns everything needed for plotting and
    further analysis. ``fit_defaults`` is used to derive any parameters left
    as ``None``.

    Parameters
    ----------
    x : array-like
        Independent variable values.
    y : array-like
        Dependent variable values.
    x_err : array-like
        Uncertainties in x.
    y_err : array-like
        Uncertainties in y.
    resample_draws : int, optional
        Number of bootstrap resamples. Default is 5000.
    line_max : int, float, or None, optional
        Maximum x-value used in ``evaluate_confidence``. When None,
        auto-derived as ``max(x) * 1.1`` via ``fit_defaults``.
    line_interval : int, float, or None, optional
        Step size used in ``evaluate_confidence``. When None,
        auto-derived as ``line_max / 1000`` via ``fit_defaults``.
    fit_intercept : bool, optional
        If True, fit slope and intercept. If False, fit through the origin.
        Default is True.
    initial_guess : list of float, optional
        Starting parameters. When None, auto-derived via ``fit_defaults``.
    confidence_level : float, optional
        Confidence level for interval estimation. Default is 0.95.

    Returns
    -------
    tuple
        confidence_data : pandas.DataFrame
            Confidence interval results from ``evaluate_confidence``.
        best_fit_params : ndarray
            Fit parameters from the full dataset.
        points : pandas.DataFrame
            Cleaned input data with columns ``x``, ``y``, ``xerr``, ``yerr``.
        all_params : list of ndarray
            All fit parameter vectors including bootstrap resamples.
        subsamples : list of pandas.DataFrame
            Bootstrap resampled subsets.
    """
    defaults = fit_defaults(x, y, fit_intercept=fit_intercept)
    if initial_guess is None:
        initial_guess = defaults["initial_guess"]
    if line_max is None:
        line_max = defaults["line_max"]
    if line_interval is None:
        line_interval = defaults["line_interval"]

    all_params, subsamples = bootstrap_odr_fit(
        x, y, x_err, y_err, resample_draws, fit_intercept, initial_guess
    )
    confidence_data = evaluate_confidence(
        fit_params=all_params,
        line_max=line_max,
        line_interval=line_interval,
        confidence_level=confidence_level,
    )

    points = pd.DataFrame({"x": x, "y": y, "xerr": x_err, "yerr": y_err})
    points.dropna(inplace=True)

    return (
        confidence_data,
        np.asarray(all_params[0], dtype=float),
        points,
        all_params,
        subsamples,
    )


def gaussian_aggregate(
    concentrations: np.ndarray | list[float],
    errors: np.ndarray | list[float],
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """
    Compute an aggregate distribution from values with Gaussian uncertainties.

    Combines multiple normal distributions into a single kernel density
    estimate using trapezoidal integration to normalize the result.

    Parameters
    ----------
    concentrations : array-like
        Central values for each Gaussian component.
    errors : array-like
        Standard deviations for each Gaussian component.

    Returns
    -------
    tuple
        distribution : dict
            Dictionary containing ``x`` and ``y`` arrays for the normalized
            density.
        statistics : dict
            Summary information including mean, mode, midpoint, and bounds.
    """
    def gaussian(
        x_values: np.ndarray,
        sigma: np.ndarray | float,
        avg: np.ndarray | float,
    ) -> np.ndarray:
        sigma_arr = np.asarray(sigma, dtype=float)
        avg_arr = np.asarray(avg, dtype=float)
        result = (1 / (sigma_arr * np.sqrt(2 * np.pi))) * np.exp(
            -0.5 * ((x_values - avg_arr) / sigma_arr) ** 2
        )
        return np.asarray(result, dtype=float)

    def ci_bound(xi: np.ndarray, data: np.ndarray, bound_fraction: float) -> float:
        cumulative = np.cumsum(data)
        index = np.searchsorted(cumulative, bound_fraction, side="left")
        if index >= len(xi):
            raise ValueError("Could not locate the requested confidence bound.")
        return float(round(xi[index], 2))

    def find_range(
        avgs: np.ndarray | list[float], sigmas: np.ndarray | list[float]
    ) -> tuple[float, float]:
        avg_arr = np.asarray(avgs, dtype=float)
        sigma_arr = np.asarray(sigmas, dtype=float)
        valid = np.isfinite(avg_arr) & np.isfinite(sigma_arr) & (sigma_arr > 0)
        if not np.any(valid):
            raise ValueError(
                "Input concentrations and errors must contain finite positive values."
            )

        avg_arr = avg_arr[valid]
        sigma_arr = sigma_arr[valid]

        lower_bound = float(
            np.percentile(avg_arr, 0.5) - 6 * np.percentile(sigma_arr, 99.0)
        )
        upper_bound = float(
            np.percentile(avg_arr, 99.5) + 6 * np.percentile(sigma_arr, 99.0)
        )
        return lower_bound, upper_bound

    concentrations_arr = np.asarray(concentrations, dtype=float)
    errors_arr = np.asarray(errors, dtype=float)

    min_val, max_val = find_range(concentrations_arr, errors_arr)
    spread = max_val - min_val
    step = max(0.01, spread / 20000.0)
    xi = np.arange(min_val, max_val + step, step)
    if len(xi) > 50000:
        step = spread / 50000.0
        xi = np.arange(min_val, max_val + step, step)

    x = np.tile(xi, (len(concentrations_arr), 1))
    unnormed_data = np.sum(gaussian(x.T, errors_arr, concentrations_arr), axis=1)
    data = unnormed_data / np.trapezoid(unnormed_data)

    average = float(np.dot(xi, data) / np.sum(data))
    most_frequent = float(xi[np.argmax(data)])
    best_fit = float(concentrations_arr[0])

    center_of_mass = ci_bound(xi, data, 0.50)
    lower_16, upper_84 = ci_bound(xi, data, 0.16), ci_bound(xi, data, 0.84)
    lower_05, upper_95 = ci_bound(xi, data, 0.05), ci_bound(xi, data, 0.95)
    CI_one_sigma = (
        round(center_of_mass - lower_16, 2),
        round(upper_84 - center_of_mass, 2),
    )
    CI_two_sigma = (
        round(center_of_mass - lower_05, 2),
        round(upper_95 - center_of_mass, 2),
    )
    one_sigma_bounds = (lower_16, upper_84)
    two_sigma_bounds = (lower_05, upper_95)

    return (
        {"x": xi, "y": data},
        {
            "simple_best_fit": best_fit,
            "mean": average,
            "mode": most_frequent,
            "mid_point": center_of_mass,
            "one_sigma_bounds": one_sigma_bounds,
            "two_sigma_bounds": two_sigma_bounds,
            "CI_one_sigma": CI_one_sigma,
            "CI_two_sigma": CI_two_sigma,
            "n": len(concentrations),
        },
    )


def plot_density(
    data: dict[str, np.ndarray],
    bounds: dict[str, Any],
    ax: Axes | None = None,
    sample_name: str | None = None,
) -> Axes:
    """
    Plot a probability density curve and annotate summary statistics.

    Parameters
    ----------
    data : dict
        Dictionary containing ``x`` and ``y`` density arrays, as returned by
        ``gaussian_aggregate``.
    bounds : dict
        Summary statistics dictionary, as returned by ``gaussian_aggregate``.
    ax : matplotlib.axes.Axes, optional
        Axis to draw on. If None, the current axis is used.
    sample_name : str, optional
        Optional label or title text.

    Returns
    -------
    matplotlib.axes.Axes
        Axis containing the plotted density curve.
    """
    ax = ax or plt.gca()
    x = data["x"]
    y = data["y"]
    ax.plot(x, y, linewidth=3)
    ax.set_xlabel("Concentration ppm")
    ax.set_ylabel("Probability")

    ax.axvline(
        x=bounds["mean"],
        ymin=0,
        color="b",
        linestyle="dashed",
        linewidth=3,
        label="Mean",
    )
    ax.axvline(
        x=bounds["mid_point"],
        ymin=0,
        color="g",
        linestyle="dashed",
        linewidth=3,
        label="Mid-point & 65% CI",
    )

    CI_one_sigma = bounds["CI_one_sigma"]
    CI_two_sigma = bounds["CI_two_sigma"]

    ax.annotate(
        f"""
    Simple Best Fit: {float(bounds['simple_best_fit']):.2f}
    Mean: {float(bounds['mean']):.2f}
    Mode: {float(bounds['mode']):.2f}
    Mid-point: {float(bounds['mid_point']):.2f}
    Confidence Intervals
    68%: - {CI_one_sigma[0]:.2f} / +{CI_one_sigma[1]:.2f}
    95%: - {CI_two_sigma[0]:.2f} / +{CI_two_sigma[1]:.2f}
    n: {bounds['n']}
    """,
        xy=(0.02, 0.68),
        xycoords="axes fraction",
        bbox=dict(boxstyle="square", fc="w", alpha=0.85),
    )
    eb = ax.errorbar(
        x=bounds["mid_point"],
        y=np.max(y) / 2,
        xerr=np.array([[CI_one_sigma[0]], [CI_one_sigma[1]]]),
        capsize=10,
        elinewidth=3,
        capthick=3,
        ecolor="g",
        linestyle="dashed",
    )
    eb[-1][0].set_linestyle("dashed")

    ax.set_ylim(bottom=0)
    ax.legend(loc="upper right", framealpha=0.85)
    return ax


def plot_calibration_estimates(
    fit_params: np.ndarray | list[list[float]],
    fit_error: np.ndarray | list[list[float]],
    title: str = "Calibration Line Fits",
) -> Figure:
    """
    Plot calibration slope and intercept estimate distributions.

    Parameters
    ----------
    fit_params : array-like
        Fit parameters for slope and intercept, shape (n, 2).
    fit_error : array-like
        Fit uncertainties for slope and intercept, shape (n, 2).
    title : str, optional
        Figure title. Default is "Calibration Line Fits".

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the slope and intercept estimate plots.
    """
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

    slope_dist, slope_stats = gaussian_aggregate(
        np.array(fit_params)[:, 0], np.array(fit_error)[:, 0]
    )
    plot_density(slope_dist, slope_stats, ax=ax1)
    ax1.set_xlabel("Calibration Slope", fontsize=20)
    ax1.set_ylabel("Probability", fontsize=20)

    intercept_dist, intercept_stats = gaussian_aggregate(
        np.array(fit_params)[:, 1], np.array(fit_error)[:, 1]
    )
    plot_density(intercept_dist, intercept_stats, ax=ax2)
    ax2.set_xlabel("Calibration Y-Intercept ppm", fontsize=20)
    ax2.set_ylabel("Probability", fontsize=20)

    plt.suptitle(title, fontsize=20)
    fig.tight_layout()
    return fig
