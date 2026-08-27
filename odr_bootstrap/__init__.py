"""
ODR Bootstrap: Orthogonal Distance Regression with Bootstrap Resampling

A Python package for SIMS calibration analysis with proper uncertainty
quantification in both x and y measurements.
"""

from .core import (
    bootstrap_odr_fit,
    evaluate_confidence,
    fit_defaults,
    fit_odr_linear,
    fit_odr_linear_debug,
    gaussian_aggregate,
    linear_through_origin,
    linear_with_intercept,
    odr_bootstrap,
    plot_calibration_estimates,
    plot_density,
    plot_regression,
)

__version__ = "2.0.0"
__author__ = "Henry Towbin"
__all__ = [
    "fit_defaults",
    "fit_odr_linear",
    "fit_odr_linear_debug",
    "bootstrap_odr_fit",
    "evaluate_confidence",
    "plot_regression",
    "odr_bootstrap",
    "gaussian_aggregate",
    "plot_density",
    "plot_calibration_estimates",
    "linear_with_intercept",
    "linear_through_origin",
]
