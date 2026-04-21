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
from scipy import odr


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
        a, b = p
        return a * x + b

    def slope_func(p: np.ndarray | list[float], x: np.ndarray | list[float]) -> np.ndarray:
        a = p
        return a * x

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

    Popt = out.beta
    Perr = out.sd_beta
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
    def yint_func(p, x):
        a, b = p
        return a * x + b

    def slope_func(p, x):
        a = p
        return a * x

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

    Popt = out.beta
    Perr = out.sd_beta
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
    def resample(count):
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
    a, b = p
    return a * x + b


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
    a = p
    return a * x


def Eval_Conf(
    Fit_Param: list[np.ndarray],
    Confidence_Bound: float = 0.95,
    LineMax: int = 200,
    LineInt: int = 1,
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
    LineMax : int, optional
        Maximum x-value for the evaluation grid. Default is 200.
    LineInt : int, optional
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
    if len(Fit_Param[0]) > 2:
        raise ValueError(
            "Fit_Param has too many inputs per row. Line inputs must be 1 or 2 parameters."
        )

    FitFunc = yint_func
    if len(Fit_Param[0]) == 1:
        FitFunc = slope_func

    evaluated = []
    x = np.arange(0, LineMax, LineInt)
    for row in Fit_Param:
        evaluated.append(FitFunc(row, x))

    BootStp_Samples = pd.DataFrame(evaluated)
    confidence_ints = []
    for _, col in BootStp_Samples.items():
        histrange = (np.nanmin(col), np.nanmax(col))
        hist = np.histogram(col, bins=200, range=histrange)
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
    confidence_df: pd.DataFrame,
    datapoints: pd.DataFrame | None = None,
    LineMax: int = 200,
    LineInt: int = 1,
    ax: plt.Axes | None = None,
    ecolor: str = "r",
    line_color: str = "b",
    sigma: int = 2,
    e_alpha: float = 0.5,
    **kwargs: Any,
) -> plt.Axes:
    """
    Plot a best-fit regression line and its bootstrap confidence band.

    Parameters
    ----------
    confidence_df : pandas.DataFrame
        Output from `Eval_Conf` with columns `best_fit`, `neg_error_bound`, and
        `pos_error_bound`.
    datapoints : pandas.DataFrame, optional
        DataFrame containing columns `x`, `y`, `xerr`, and `yerr`.
    LineMax : int, optional
        Accepted for compatibility but not used in this function.
    LineInt : int, optional
        Accepted for compatibility but not used in this function.
    ax : matplotlib.axes.Axes, optional
        Axis object to draw on. If None, the current axis is used.
    ecolor : str, optional
        Confidence band color. Default is 'r'.
    line_color : str, optional
        Best-fit line color. Default is 'b'.
    sigma : int, optional
        Ignored in the current implementation.
    e_alpha : float, optional
        Alpha transparency for the confidence band. Default is 0.5.

    Returns
    -------
    matplotlib.axes.Axes
        Axis containing the regression plot.
    """
    BestFitLine = confidence_df["best_fit"]
    NegBound = confidence_df["neg_error_bound"]
    PosBound = confidence_df["pos_error_bound"]

    x = NegBound.index
    if ax is None:
        ax = plt.gca()

    ax.fill_between(x, NegBound, PosBound, color=ecolor, alpha=e_alpha)
    ax.plot(x, BestFitLine, color=line_color, **kwargs)

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
    ax: plt.Axes | None = None,
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

    return confidence_data, param[0], points, param, subs


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
    def gaussian(x, sigma, avg):
        return (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(
            -0.5 * ((x - avg) / sigma) ** 2
        )

    def CI_bound(xi, data, bound_fraction):
        for n, val in enumerate(np.cumsum(data)):
            if val > bound_fraction:
                return round(xi[n], 2)

    def find_range(avgs, sigmas):
        max_val = np.max(avgs) + 3 * np.max(sigmas)
        min_val = np.min(avgs) - 3 * np.max(sigmas)
        return min_val, max_val

    min_val, max_val = find_range(concentrations, errors)
    xi = np.arange(min_val, max_val, 0.01)
    x = np.tile(xi, (len(concentrations), 1))
    unnormed_data = np.sum(gaussian(x.T, errors, concentrations), axis=1)
    # Use np.trapezoid (scipy >= 1.15) instead of deprecated np.trapz
    data = unnormed_data / np.trapezoid(unnormed_data)

    average = np.dot(xi, data) / np.sum(data)
    most_frequent = xi[np.argmax(data)]
    best_fit = concentrations[0]

    center_of_mass = CI_bound(xi, data, 0.50)
    one_sigma_bounds = CI_bound(xi, data, 0.16), CI_bound(xi, data, 0.84)
    two_sigma_bounds = CI_bound(xi, data, 0.05), CI_bound(xi, data, 0.95)
    CI_one_sigma = (
        round(center_of_mass - one_sigma_bounds[0], 2),
        round(one_sigma_bounds[1] - center_of_mass, 2),
    )
    CI_two_sigma = (
        round(center_of_mass - two_sigma_bounds[0], 2),
        round(two_sigma_bounds[1] - center_of_mass, 2),
    )

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
    ax: plt.Axes | None = None,
    sample_name: str | None = None,
) -> plt.Axes:
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
) -> plt.Figure:
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
