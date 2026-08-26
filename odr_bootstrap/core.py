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


def ODR_Linear(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    x_err: np.ndarray | list[float],
    y_err: np.ndarray | list[float],
    intercept: bool = False,
    InitialGuess: list[float] | None = None,
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
        Uncertainties in the independent variable values.
    y_err : array-like
        Uncertainties in the dependent variable values.
    intercept : bool, optional
        If True, fit `y = a * x + b`. If False, fit `y = a * x` through the origin.
        Default is False.
    InitialGuess : list, optional
        Initial guess for the fit parameters. For intercept fits supply
        `[slope, intercept]`. For zero-intercept fits supply `[slope]`.
        Default is `[100, 1]`.

    Returns
    -------
    tuple
        `Popt`, `Perr` where `Popt` is the fitted parameter array and `Perr`
        is the 1-sigma uncertainty array.
    """
    def yint_func(p: np.ndarray | list[float], x: np.ndarray | list[float]) -> np.ndarray:
        params = _as_float_array(p)
        x_arr = _as_float_array(x)
        slope = float(params[0])
        intercept = float(params[1])
        return np.asarray(slope * x_arr + intercept, dtype=float)

    def slope_func(p: np.ndarray | list[float], x: np.ndarray | list[float]) -> np.ndarray:
        params = _as_float_array(p)
        x_arr = _as_float_array(x)
        slope = float(params[0])
        return np.asarray(slope * x_arr, dtype=float)

    if InitialGuess is None:
        InitialGuess = [100, 1]

    linear_model = odr.Model(yint_func)
    beta0 = InitialGuess
    if intercept is False:
        linear_model = odr.Model(slope_func)
        # scipy.odr.ODR requires beta0 to be array-like; wrap scalar in list
        beta0 = [InitialGuess[0]]  # Use only slope for zero-intercept fit

    data = odr.RealData(x, y, sx=x_err, sy=y_err)
    myodr = odr.ODR(data, linear_model, beta0=beta0)
    myodr.set_job(fit_type=0)
    out = myodr.run()

    Popt = np.asarray(out.beta, dtype=float)
    Perr = np.asarray(out.sd_beta, dtype=float)
    return Popt, Perr


def ODR_Linear_Test(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    x_err: np.ndarray | list[float],
    y_err: np.ndarray | list[float],
    intercept: bool = False,
    InitialGuess: list[float] = [100, 1],
) -> tuple[np.ndarray, np.ndarray, Any]:
    """
    Fit a linear model using ODR and return the raw ODR output.

    Parameters
    ----------
    x : array-like
        Independent variable values.
    y : array-like
        Dependent variable values.
    x_err : array-like
        Uncertainties in the independent variable values.
    y_err : array-like
        Uncertainties in the dependent variable values.
    intercept : bool, optional
        If True, fit `y = a * x + b`. If False, fit `y = a * x` through the origin.
        Default is False.
    InitialGuess : list, optional
        Initial guess for the fit parameters. For intercept fits supply
        `[slope, intercept]`. For zero-intercept fits supply `[slope]`.
        Default is `[100, 1]`.

    Returns
    -------
    tuple
        `Popt`, `Perr`, `odr_output` where `odr_output` is the full ODR result.
    """
    def yint_func(p: np.ndarray | list[float], x: np.ndarray | list[float]) -> np.ndarray:
        params = _as_float_array(p)
        x_arr = _as_float_array(x)
        slope = float(params[0])
        intercept = float(params[1])
        return np.asarray(slope * x_arr + intercept, dtype=float)

    def slope_func(p: np.ndarray | list[float], x: np.ndarray | list[float]) -> np.ndarray:
        params = _as_float_array(p)
        x_arr = _as_float_array(x)
        slope = float(params[0])
        return np.asarray(slope * x_arr, dtype=float)

    linear_model = odr.Model(yint_func)
    beta0 = InitialGuess
    if intercept is False:
        linear_model = odr.Model(slope_func)
        # scipy.odr.ODR requires beta0 to be array-like; wrap scalar in list
        beta0 = [InitialGuess[0]]  # Use only slope for zero-intercept fit

    data = odr.RealData(x, y, sx=x_err, sy=y_err)
    myodr = odr.ODR(data, linear_model, beta0=beta0)
    myodr.set_job(fit_type=0)
    out = myodr.run()

    Popt = np.asarray(out.beta, dtype=float)
    Perr = np.asarray(out.sd_beta, dtype=float)
    return Popt, Perr, out


def Bootstrap_fit(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    x_err: np.ndarray | list[float],
    y_err: np.ndarray | list[float],
    resample_draws: int,
    InterceptFit: bool = True,
    InitialGuess: list[float] = [100, 1],
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
        Uncertainties in the independent variable values.
    y_err : array-like
        Uncertainties in the dependent variable values.
    resample_draws : int
        Number of bootstrap resamples to compute.
    InterceptFit : bool, optional
        If True, fit slope and intercept; if False, fit through the origin.
        Default is True.
    InitialGuess : list, optional
        Initial guess for model parameters. Default is `[100, 1]`.

    Returns
    -------
    tuple
        fit_params : list of ndarray
            First element is the fit result from the full dataset, followed
            by all bootstrap fits.
        subsamples : list of pandas.DataFrame
            Resampled DataFrame objects used for each bootstrap iteration.
    """
    def resample(count: int) -> np.ndarray:
        return np.random.randint(0, count, count)

    InitialGuess = list(InitialGuess)
    if InterceptFit is False:
        InitialGuess = [InitialGuess[0]]

    data = np.array([x, x_err, y, y_err]).T
    df = pd.DataFrame(data, columns=["x", "x_err", "y", "y_err"])
    df.dropna(inplace=True)
    length = len(df)

    opt, err = ODR_Linear(
        x=df["x"],
        y=df["y"],
        x_err=df["x_err"],
        y_err=df["y_err"],
        InitialGuess=InitialGuess,
        intercept=InterceptFit,
    )
    Fit_Param = [opt]
    subs = []

    for _ in range(resample_draws):
        sub = df.take(resample(length))
        opt, err = ODR_Linear(
            x=sub["x"],
            y=sub["y"],
            x_err=sub["x_err"],
            y_err=sub["y_err"],
            InitialGuess=InitialGuess,
            intercept=InterceptFit,
        )
        Fit_Param.append(opt)
        subs.append(sub)

    return Fit_Param, subs


def yint_func(p: np.ndarray | list[float], x: np.ndarray | list[float]) -> np.ndarray:
    """
    Evaluate a line with slope and intercept.

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
    slope = float(params[0])
    intercept = float(params[1])
    return np.asarray(slope * x_arr + intercept, dtype=float)


def slope_func(p: np.ndarray | list[float], x: np.ndarray | list[float]) -> np.ndarray:
    """
    Evaluate a line through the origin.

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
    slope = float(params[0])
    return np.asarray(slope * x_arr, dtype=float)


def Eval_Conf(
    Fit_Param: list[np.ndarray],
    Confidence_Bound: float = 0.95,
    LineMax: int | float = 200,
    LineInt: int | float = 1,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Evaluate bootstrap confidence intervals for linear predictions.

    Parameters
    ----------
    Fit_Param : list of array-like
        Bootstrapped fit parameter vectors. Each row must contain either one
        parameter (slope only) or two parameters (slope and intercept).
    Confidence_Bound : float, optional
        Confidence level expressed as a fraction between 0 and 1.
        Default is 0.95.
    LineMax : int or float, optional
        Maximum x-value for the evaluation grid. Default is 200.
    LineInt : int or float, optional
        Step size for the evaluation grid. Default is 1.

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by x values containing columns:
        - neg_error_bound
        - pos_error_bound
        - best_fit
        - percent_error_neg
        - percent_error_pos
    """
    if "line_max" in kwargs:
        LineMax = kwargs["line_max"]
    if "line_interval" in kwargs:
        LineInt = kwargs["line_interval"]

    if LineInt <= 0:
        raise ValueError("LineInt must be positive.")
    if LineMax < 0:
        raise ValueError("LineMax must be non-negative.")

    first_param = np.asarray(Fit_Param[0], dtype=float)
    if len(first_param) > 2:
        raise ValueError(
            "Fit_Param has too many inputs per row. Line inputs must be 1 or 2 parameters."
        )

    FitFunc = yint_func
    if len(first_param) == 1:
        FitFunc = slope_func

    evaluated = []
    num_steps = max(0, int(round(float(LineMax) / float(LineInt))))
    x = np.linspace(0.0, float(LineMax), num_steps + 1)
    if len(x) == 0:
        x = np.array([0.0])
    for row in Fit_Param:
        evaluated.append(FitFunc(row, x))

    BootStp_Samples = pd.DataFrame(evaluated)
    confidence_ints = []
    for _, col in BootStp_Samples.items():
        histrange = (np.nanmin(col), np.nanmax(col))
        hist = np.histogram(col, bins=400, range=histrange)
        conf_int = stats.rv_histogram(hist).interval(Confidence_Bound)
        confidence_ints.append(conf_int)

    Results = pd.DataFrame(
        confidence_ints, columns=("neg_error_bound", "pos_error_bound")
    )
    Results.index = x
    Results["best_fit"] = evaluated[0]
    Results["percent_error_neg"] = (
        Results["best_fit"] - Results["neg_error_bound"]
    ) / np.abs(Results["best_fit"])
    Results["percent_error_pos"] = (
        Results["pos_error_bound"] - Results["best_fit"]
    ) / np.abs(Results["best_fit"])

    return Results


def plot_regression(
    confidence_df: pd.DataFrame | list[pd.DataFrame],
    datapoints: pd.DataFrame | None = None,
    LineMax: int | float = 200,
    LineInt: int | float = 1,
    ax: Axes | None = None,
    ecolor: str | list[str] = "r",
    line_color: str | list[str] = "b",
    sigma: int = 2,
    e_alpha: float | list[float] = 0.5,
    **kwargs: Any,
) -> Axes:
    """
    Plot a best-fit regression line with one or more shaded confidence bands.

    Parameters
    ----------
    confidence_df : pandas.DataFrame or list of pandas.DataFrame
        Output from `Eval_Conf` with columns `best_fit`, `neg_error_bound`, and
        `pos_error_bound`. A list overlays multiple confidence intervals on the
        same regression line.
    datapoints : pandas.DataFrame, optional
        DataFrame containing columns `x`, `y`, `xerr`, and `yerr`.
    ax : matplotlib.axes.Axes, optional
        Axis object to draw on. If None, the current axis is used.
    ecolor : str or list of str, optional
        Confidence-band colors. In list form, the first entry is the 68% band
        and the second is the 95% band.
    line_color : str or list of str, optional
        Best-fit line color(s). A single value colors the line uniformly.
    e_alpha : float or list of float, optional
        Transparency for the confidence bands.

    Returns
    -------
    matplotlib.axes.Axes
        Axis containing the regression plot.
    """
    if isinstance(confidence_df, list):
        if not confidence_df:
            raise ValueError("confidence_df must contain at least one DataFrame.")

        ax = ax if ax is not None else plt.gca()
        band_colors = [ecolor] * len(confidence_df) if isinstance(ecolor, str) else list(ecolor)
        band_alphas = [e_alpha] * len(confidence_df) if isinstance(e_alpha, float) else list(e_alpha)
        line_colors = [line_color] * len(confidence_df) if isinstance(line_color, str) else list(line_color)

        base_conf = confidence_df[0]
        x_values = base_conf["best_fit"].index
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
            ax.plot(x, conf_95["best_fit"], color=best_fit_color, label="Best fit", **line_kwargs)
        elif len(confidence_df) == 1:
            conf = confidence_df[0]
            x = conf["neg_error_bound"].index
            ax.fill_between(x, conf["neg_error_bound"], conf["pos_error_bound"], color=band_colors[0], alpha=band_alphas[0], linewidth=0, label="95% CI")
            best_fit_color = line_colors[0] if line_colors else "#0f766e"
            line_kwargs = dict(kwargs)
            line_kwargs.setdefault("linewidth", 2.0)
            ax.plot(x, conf["best_fit"], color=best_fit_color, label="Best fit", **line_kwargs)

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

    BestFitLine = confidence_df["best_fit"]
    NegBound = confidence_df["neg_error_bound"]
    PosBound = confidence_df["pos_error_bound"]

    x = NegBound.index
    if ax is None:
        ax = plt.gca()

    ax.fill_between(x, NegBound, PosBound, color=ecolor, alpha=e_alpha)
    ax.plot(x, BestFitLine, color=line_color, **kwargs)

    x_max = float(np.nanmax(np.asarray(list(x), dtype=float))) if len(x) else 0.0
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

    ax.set_xlim(left=min(float(np.nanmin(np.asarray(list(x), dtype=float))), 0.0), right=x_max * 1.05 + 1e-9)
    return ax


def ODR_Bootstrap(
    x: np.ndarray | list[float],
    y: np.ndarray | list[float],
    x_err: np.ndarray | list[float],
    y_err: np.ndarray | list[float],
    resample_draws: int = 5000,
    LineMax: int = 200,
    LineInterval: int = 1,
    InterceptFit: bool = True,
    InitialGuess: list[float] = [100, 1],
    Confidence_Bound: float = 0.95,
    plot: bool = False,
    ax: Axes | None = None,
    **kwargs: Any,
) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame, list[np.ndarray], list[pd.DataFrame]]:
    """
    Run bootstrap resampling for ODR linear fitting and compute confidence data.

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
    LineMax : int, optional
        Maximum x value used in `Eval_Conf`. Default is 200.
    LineInterval : int, optional
        Step size used in `Eval_Conf`. Default is 1.
    InterceptFit : bool, optional
        If True, fit slope and intercept; if False, fit through the origin.
        Default is True.
    InitialGuess : list, optional
        Initial guess for fit parameters. Default is `[100, 1]`.
    Confidence_Bound : float, optional
        Confidence level for interval estimation. Default is 0.95.
    plot : bool, optional
        Accepted for compatibility but not used in this implementation.
    ax : matplotlib.axes.Axes, optional
        Axis object for future plotting support.

    Returns
    -------
    tuple
        confidence_data : pandas.DataFrame
            Confidence interval results from `Eval_Conf`.
        best_fit_params : ndarray
            Fit parameters for the full dataset.
        points : pandas.DataFrame
            Cleaned input data containing `x`, `y`, `xerr`, and `yerr`.
        all_params : list of ndarray
            All fit parameter vectors including bootstrap resamples.
        subsamples : list of pandas.DataFrame
            Bootstrap resampled subsets.
    """
    param, subs = Bootstrap_fit(
        x, y, x_err, y_err, resample_draws, InterceptFit, InitialGuess
    )
    confidence_data = Eval_Conf(
        Fit_Param=param,
        Confidence_Bound=Confidence_Bound,
        LineMax=LineMax,
        LineInt=LineInterval,
    )

    points = pd.DataFrame({"x": x, "y": y, "xerr": x_err, "yerr": y_err})
    points.dropna(inplace=True)

    return confidence_data, np.asarray(param[0], dtype=float), points, param, subs


def gauss_agv_err(
    concentrations: np.ndarray | list[float],
    errors: np.ndarray | list[float],
    cut_off: float = 0.000001,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """
    Compute an aggregate Gaussian distribution from values and uncertainties.

    Combines multiple normal distributions into a single kernel density estimate.
    Uses trapezoidal integration (via scipy.integrate.trapezoid) to normalize.

    Parameters
    ----------
    concentrations : array-like
        Central values for each Gaussian component.
    errors : array-like
        Standard deviations for each Gaussian component.
    cut_off : float, optional
        Probability density threshold for filtering low values.
        Default is 1e-6.

    Returns
    -------
    tuple
        distribution : dict
            Dictionary containing `x` and `y` arrays for the normalized density.
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

    def CI_bound(
        xi: np.ndarray, data: np.ndarray, bound_fraction: float
    ) -> float:
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
        max_val = float(np.max(avg_arr) + 3 * np.max(sigma_arr))
        min_val = float(np.min(avg_arr) - 3 * np.max(sigma_arr))
        return min_val, max_val

    concentrations_arr = np.asarray(concentrations, dtype=float)
    errors_arr = np.asarray(errors, dtype=float)

    min_val, max_val = find_range(concentrations_arr, errors_arr)
    xi = np.arange(min_val, max_val, 0.01)
    x = np.tile(xi, (len(concentrations_arr), 1))
    unnormed_data = np.sum(gaussian(x.T, errors_arr, concentrations_arr), axis=1)
    data = unnormed_data / np.trapezoid(unnormed_data)

    average = float(np.dot(xi, data) / np.sum(data))
    most_frequent = float(xi[np.argmax(data)])
    best_fit = float(concentrations_arr[0])

    center_of_mass = CI_bound(xi, data, 0.50)
    lower_16, upper_84 = CI_bound(xi, data, 0.16), CI_bound(xi, data, 0.84)
    lower_05, upper_95 = CI_bound(xi, data, 0.05), CI_bound(xi, data, 0.95)
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


def plot_datapoints(
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
        Dictionary containing `x` and `y` density arrays.
    bounds : dict
        Summary statistics returned by `gauss_agv_err`.
    ax : matplotlib.axes.Axes, optional
        Axis object to draw on. If None, the current axis is used.
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


def plot_Calibration_Estimates(
    fit_params: np.ndarray | list[list[float]],
    fit_error: np.ndarray | list[list[float]],
    Title: str = "Calibration Line Fits",
) -> Figure:
    """
    Plot calibration slope and intercept estimate distributions.

    Parameters
    ----------
    fit_params : array-like
        Fit parameters for slope and intercept, shape (n, 2).
    fit_error : array-like
        Fit uncertainties for slope and intercept, shape (n, 2).
    Title : str, optional
        Figure title. Default is "Calibration Line Fits".

    Returns
    -------
    matplotlib.figure.Figure
        Figure containing the slope and intercept estimate plots.
    """
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

    Slope_Fit_Params = gauss_agv_err(np.array(fit_params)[:, 0], np.array(fit_error)[:, 0])
    plot_datapoints(Slope_Fit_Params[0], Slope_Fit_Params[1], ax=ax1)
    ax1.set_xlabel("Calibration Slope", fontsize=20)
    ax1.set_ylabel("Probability", fontsize=20)

    Intercept_Fit_Params = gauss_agv_err(
        np.array(fit_params)[:, 1], np.array(fit_error)[:, 1]
    )
    plot_datapoints(Intercept_Fit_Params[0], Intercept_Fit_Params[1], ax=ax2)
    ax2.set_xlabel("Calibration Y-Intercept ppm", fontsize=20)
    ax2.set_ylabel("Probability", fontsize=20)

    plt.suptitle(Title, fontsize=20)
    fig.tight_layout()
    return fig
