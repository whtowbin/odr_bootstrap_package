"""Example workflow for ODR bootstrapping and calibration analysis."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from odr_bootstrap import (  # noqa: E402
    Eval_Conf,
    ODR_Bootstrap,
    plot_Calibration_Estimates,
    plot_regression,
)

OUTPUT_DIR = Path(__file__).resolve().parent


def main() -> None:
    """Run the complete example workflow and save figures next to the script."""

    print("=" * 70)
    print("ODR Bootstrap Calibration Example")
    print("=" * 70)

    # =========================================================================
    # 1. Create Synthetic Calibration Data
    # =========================================================================
    print("\n[1/5] Creating synthetic calibration data...")

    x_standards = np.array([0.1, 0.5, 1.0, 2.0, 5.0, 10.0])
    y_measured = 125 * x_standards + 15 + np.random.normal(0, 40, len(x_standards))
    x_uncertainty = np.array([0.01, 0.05, 0.1, 0.2, 0.5, 1.0])
    y_uncertainty = np.array([20, 30, 50, 60, 100, 150])

    print(f"   Standards: {x_standards}")
    print(f"   Measurements: {y_measured}")
    print(f"   X uncertainties: {x_uncertainty}")
    print(f"   Y uncertainties: {y_uncertainty}")

    x_outlier = np.concatenate([x_standards, [8.5, 6.3]])
    y_outlier = np.concatenate([
        y_measured,
        [125 * 8.5 + 15 + 400],
        [125 * 12.0 + 15 + 1200],
    ])
    x_outlier_err = np.concatenate([x_uncertainty, [0.3, 0.5]])
    y_outlier_err = np.concatenate([y_uncertainty, [100, 250]])

    # =========================================================================
    # 2. Run ODR Bootstrap Fitting
    # =========================================================================
    print("\n[2/5] Running ODR Bootstrap (N=2000 resamples)...")

    confidence_data, best_fit_params, points, all_params, _ = ODR_Bootstrap(
        x=x_standards,
        y=y_measured,
        x_err=x_uncertainty,
        y_err=y_uncertainty,
        resample_draws=2000,
        InterceptFit=True,
        InitialGuess=[100, 10],
        Confidence_Bound=0.95,
        LineMax=11,
        LineInterval=0.5,
    )

    conf_68 = Eval_Conf(all_params, Confidence_Bound=0.68, LineMax=11, LineInt=0.5)
    conf_95 = Eval_Conf(all_params, Confidence_Bound=0.95, LineMax=11, LineInt=0.5)

    outlier_confidence_data, outlier_best_fit, outlier_points, outlier_params, _ = ODR_Bootstrap(
        x=x_outlier,
        y=y_outlier,
        x_err=x_outlier_err,
        y_err=y_outlier_err,
        resample_draws=2000,
        InterceptFit=True,
        InitialGuess=[100, 10],
        Confidence_Bound=0.95,
        LineMax=11,
        LineInterval=0.5,
    )
    outlier_conf_68 = Eval_Conf(outlier_params, Confidence_Bound=0.68, LineMax=11, LineInt=0.5)
    outlier_conf_95 = Eval_Conf(outlier_params, Confidence_Bound=0.95, LineMax=11, LineInt=0.5)

    print(f"   Best fit slope: {best_fit_params[0]:.2f}")
    print(f"   Best fit intercept: {best_fit_params[1]:.2f}")
    print(f"   Bootstrap resamples computed: {len(all_params) - 1}")
    print(f"   Data points after NaN removal: {len(points)}")

    # =========================================================================
    # 3. Plot Regression with 68% and 95% confidence intervals
    # =========================================================================
    print("\n[3/5] Plotting regression with 68% and 95% confidence intervals...")

    fig, ax = plt.subplots(figsize=(10, 6))
    plot_regression(
        [conf_95, conf_68],
        datapoints=points,
        ax=ax,
        ecolor=["#bfdbfe", "#1d4ed8"],
        line_color="#0f766e",
        e_alpha=[0.35, 0.7],
        linewidth=2.5,
    )
    ax.set_xlabel("Concentration (ppm)", fontsize=12)
    ax.set_ylabel("Ion Intensity (counts)", fontsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "calibration_curve.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPO_ROOT / "calibration_curve.png", dpi=150, bbox_inches="tight")
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_curve.png'}")
    plt.close(fig)

    # =========================================================================
    # 4. Plot Outlier Sensitivity Example
    # =========================================================================
    print("\n[4/5] Plotting outlier sensitivity example...")

    fig, ax = plt.subplots(figsize=(10, 6))
    plot_regression(
        [outlier_conf_95, outlier_conf_68],
        datapoints=outlier_points,
        ax=ax,
        ecolor=["#fde68a", "#d97706"],
        line_color="#7c2d12",
        e_alpha=[0.4, 0.8],
        linewidth=2.5,
    )
    ax.set_xlabel("Concentration (ppm)", fontsize=12)
    ax.set_ylabel("Ion Intensity (counts)", fontsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "calibration_curve_outlier.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPO_ROOT / "calibration_curve_outlier.png", dpi=150, bbox_inches="tight")
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_curve_outlier.png'}")
    plt.close(fig)

    # =========================================================================
    # 5. Plot Calibration Estimate Distributions
    # =========================================================================
    print("\n[5/5] Plotting calibration estimate distributions...")

    all_slopes = np.array([p[0] for p in all_params])
    all_intercepts = np.array([p[1] for p in all_params])
    slope_mean = all_slopes.mean()
    slope_std = all_slopes.std()
    intercept_mean = all_intercepts.mean()
    intercept_std = all_intercepts.std()

    fit_params = np.array([
        [slope_mean, intercept_mean]
        for _ in range(5)
    ])
    fit_params += np.random.normal(0, [slope_std, intercept_std], (5, 2))

    fit_error = np.array([
        [slope_std, intercept_std]
        for _ in range(5)
    ])

    fig = plot_Calibration_Estimates(
        fit_params,
        fit_error,
        Title="Calibration Slope and Intercept Bootstrap Distributions",
    )
    fig.savefig(OUTPUT_DIR / "calibration_estimates.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPO_ROOT / "calibration_estimates.png", dpi=150, bbox_inches="tight")
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_estimates.png'}")
    plt.close(fig)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\nFit Parameters (from full dataset):")
    print(f"  Slope:     {best_fit_params[0]:8.2f}")
    print(f"  Intercept: {best_fit_params[1]:8.2f}")

    print(f"\nBootstrap Statistics (N={len(all_params)-1}):")
    print(f"  Slope mean:     {slope_mean:.2f} ± {slope_std:.2f}")
    print(f"  Intercept mean: {intercept_mean:.2f} ± {intercept_std:.2f}")


if __name__ == "__main__":
    main()
