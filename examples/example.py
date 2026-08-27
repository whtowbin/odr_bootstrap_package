#%%
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
    evaluate_confidence,
    fit_defaults,
    gaussian_aggregate,
    odr_bootstrap,
    plot_density,
    plot_regression,
)

OUTPUT_DIR = Path(__file__).resolve().parent
DOCS_STATIC_DIR = REPO_ROOT / "docs" / "source" / "_static"


def main() -> None:
    """Run the complete example workflow and save figures next to the script."""

    DOCS_STATIC_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("ODR Bootstrap Calibration Example")
    print("=" * 70)

    # =========================================================================
    # 1. Create Synthetic Calibration Data
    # =========================================================================
    print("\n[1/6] Creating synthetic calibration data...")

    x_standards = np.array([0.1, 0.5, 1.0, 2.0, 5.0, 10.0])
    y_measured = 125 * x_standards + 15 + np.random.normal(0, 40, len(x_standards))
    x_uncertainty = np.array([0.01, 0.05, 0.1, 0.2, 0.5, 1.0])
    y_uncertainty = np.array([20, 30, 50, 60, 100, 150])

    # Derive sensible initial parameters from the data
    defaults = fit_defaults(x_standards, y_measured, fit_intercept=True)
    initial_guess = defaults["initial_guess"]
    line_max = defaults["line_max"] * 1.2
    line_interval = defaults["line_interval"]

    print(f"   Standards: {x_standards}")
    print(f"   Measurements: {y_measured}")
    print(f"   X uncertainties: {x_uncertainty}")
    print(f"   Y uncertainties: {y_uncertainty}")
    print(
        f"   Least-squares initial guess: "
        f"slope={initial_guess[0]:.3f}, intercept={initial_guess[1]:.3f}"
    )

    x_outlier = np.concatenate([x_standards, [8.5, 12]])
    y_outlier = np.concatenate([
        y_measured,
        [125 * 8.5 + 15 + 400],
        [125 * 12 + 15 - 1200],
    ])
    x_outlier_err = np.concatenate([x_uncertainty, [0.3, 0.5]])
    y_outlier_err = np.concatenate([y_uncertainty, [100, 250]])

    # =========================================================================
    # 2. Run ODR Bootstrap Fitting
    # =========================================================================
    print("\n[2/6] Running ODR Bootstrap (N=2000 resamples)...")

    confidence_data, best_fit_params, points, all_params, _ = odr_bootstrap(
        x=x_standards,
        y=y_measured,
        x_err=x_uncertainty,
        y_err=y_uncertainty,
        resample_draws=2000,
        fit_intercept=True,
        initial_guess=initial_guess,
        confidence_level=0.95,
        line_max=line_max,
        line_interval=line_interval,
    )

    conf_68 = evaluate_confidence(
        all_params, line_max=line_max, line_interval=line_interval,
        confidence_level=0.68,
    )
    conf_95 = evaluate_confidence(
        all_params, line_max=line_max, line_interval=line_interval,
        confidence_level=0.95,
    )

    outlier_defaults = fit_defaults(x_outlier, y_outlier, fit_intercept=True)
    outlier_confidence_data, outlier_best_fit, outlier_points, outlier_params, _ = odr_bootstrap(
        x=x_outlier,
        y=y_outlier,
        x_err=x_outlier_err,
        y_err=y_outlier_err,
        resample_draws=2000,
        fit_intercept=True,
        initial_guess=outlier_defaults["initial_guess"],
        confidence_level=0.95,
        line_max=outlier_defaults["line_max"] * 1.2,
        line_interval=outlier_defaults["line_interval"],
    )
    outlier_line_max = outlier_defaults["line_max"] * 1.2
    outlier_line_interval = outlier_defaults["line_interval"]
    outlier_conf_68 = evaluate_confidence(
        outlier_params,
        line_max=outlier_line_max,
        line_interval=outlier_line_interval,
        confidence_level=0.68,
    )
    outlier_conf_95 = evaluate_confidence(
        outlier_params,
        line_max=outlier_line_max,
        line_interval=outlier_line_interval,
        confidence_level=0.95,
    )

    print(f"   Best fit slope: {best_fit_params[0]:.2f}")
    print(f"   Best fit intercept: {best_fit_params[1]:.2f}")
    print(f"   Bootstrap resamples computed: {len(all_params) - 1}")
    print(f"   Data points after NaN removal: {len(points)}")

    # =========================================================================
    # 3. Plot Regression with 68% and 95% confidence intervals
    # =========================================================================
    print("\n[3/6] Plotting regression with 68% and 95% confidence intervals...")

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
    fig.savefig(DOCS_STATIC_DIR / "calibration_curve.png", dpi=150, bbox_inches="tight")
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_curve.png'}")
    plt.close(fig)

    # =========================================================================
    # 4. Plot Calibration Estimate Distributions
    # =========================================================================
    print("\n[4/6] Plotting calibration estimate distributions...")

    all_params_array = np.asarray(all_params, dtype=float)
    all_slopes = all_params_array[:, 0]
    all_intercepts = all_params_array[:, 1]
    slope_mean = all_slopes.mean()
    slope_std = all_slopes.std()
    intercept_mean = all_intercepts.mean()
    intercept_std = all_intercepts.std()

    slope_dist, slope_stats = gaussian_aggregate(
        all_slopes,
        np.full_like(all_slopes, slope_std),
    )
    intercept_dist, intercept_stats = gaussian_aggregate(
        all_intercepts,
        np.full_like(all_intercepts, intercept_std),
    )

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))
    plot_density(slope_dist, slope_stats, ax=axes[0])
    plot_density(intercept_dist, intercept_stats, ax=axes[1])
    axes[0].set_xlabel("Calibration Slope", fontsize=12)
    axes[0].set_ylabel("Probability", fontsize=12)
    axes[1].set_xlabel("Calibration Y-Intercept", fontsize=12)
    axes[1].set_ylabel("Probability", fontsize=12)
    fig.suptitle("Calibration Slope and Intercept Bootstrap Distributions", fontsize=16)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "calibration_estimates.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPO_ROOT / "calibration_estimates.png", dpi=150, bbox_inches="tight")
    fig.savefig(DOCS_STATIC_DIR / "calibration_estimates.png", dpi=150, bbox_inches="tight")
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_estimates.png'}")
    plt.close(fig)

    # =========================================================================
    # 5. Plot Sensitivity to Retained Potential Outliers
    # =========================================================================
    print("\n[5/6] Plotting sensitivity to retained potential outliers...")

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
    fig.savefig(DOCS_STATIC_DIR / "calibration_curve_outlier.png", dpi=150, bbox_inches="tight")
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_curve_outlier.png'}")
    plt.close(fig)

    # =========================================================================
    # 6. Plot Parameter Uncertainty with Retained Potential Outliers
    # =========================================================================
    print("\n[6/6] Plotting parameter uncertainty with retained potential outliers...")

    outlier_params_array = np.asarray(outlier_params, dtype=float)
    outlier_slopes = outlier_params_array[:, 0]
    outlier_intercepts = outlier_params_array[:, 1]
    outlier_slope_std = outlier_slopes.std()
    outlier_intercept_std = outlier_intercepts.std()

    outlier_slope_dist, outlier_slope_stats = gaussian_aggregate(
        outlier_slopes,
        np.full_like(outlier_slopes, outlier_slope_std),
    )
    outlier_intercept_dist, outlier_intercept_stats = gaussian_aggregate(
        outlier_intercepts,
        np.full_like(outlier_intercepts, outlier_intercept_std),
    )

    outlier_fig, outlier_axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))
    plot_density(outlier_slope_dist, outlier_slope_stats, ax=outlier_axes[0])
    plot_density(outlier_intercept_dist, outlier_intercept_stats, ax=outlier_axes[1])
    outlier_axes[0].set_xlabel("Slope with Potential Outliers", fontsize=12)
    outlier_axes[0].set_ylabel("Probability", fontsize=12)
    outlier_axes[1].set_xlabel("Y-Intercept with Potential Outliers", fontsize=12)
    outlier_axes[1].set_ylabel("Probability", fontsize=12)
    outlier_fig.suptitle(
        "Parameter Distributions with Retained Potential Outliers",
        fontsize=16,
    )
    outlier_fig.tight_layout()
    outlier_fig.savefig(OUTPUT_DIR / "calibration_estimates_outlier.png", dpi=150, bbox_inches="tight")
    outlier_fig.savefig(REPO_ROOT / "calibration_estimates_outlier.png", dpi=150, bbox_inches="tight")
    outlier_fig.savefig(DOCS_STATIC_DIR / "calibration_estimates_outlier.png", dpi=150, bbox_inches="tight")
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_estimates_outlier.png'}")
    plt.close(outlier_fig)

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

# %%
