"""
ODR Bootstrap: Orthogonal Distance Regression with Bootstrap Resampling

A Python package for SIMS calibration analysis with proper uncertainty
quantification in both x and y measurements.
"""

from .core import (
    ODR_Linear,
    ODR_Linear_Test,
    Bootstrap_fit,
    Eval_Conf,
    plot_regression,
    ODR_Bootstrap,
    gauss_agv_err,
    plot_datapoints,
    plot_Calibration_Estimates,
    yint_func,
    slope_func,
)

__version__ = "0.1.0"
__author__ = "Henry Towbin"
__all__ = [
    "ODR_Linear",
    "ODR_Linear_Test",
    "Bootstrap_fit",
    "Eval_Conf",
    "plot_regression",
    "ODR_Bootstrap",
    "gauss_agv_err",
    "plot_datapoints",
    "plot_Calibration_Estimates",
    "yint_func",
    "slope_func",
]
