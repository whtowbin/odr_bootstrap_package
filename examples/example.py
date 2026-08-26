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
    print("\n[1/4] Creating synthetic calibration data...")

    # Define standard materials with known concentrations
    x_standards = np.array([0.1, 0.5, 1.0, 2.0, 5.0, 10.0])

    # Simulated ion intensity measurements (counts)
    # True relationship: y = 125*x + 15 (slope = 125, intercept = 15)
    y_measured = 125 * x_standards + 15 + np.random.normal(0, 40, len(x_standards))

    # Measurement uncertainties
    x_uncertainty = np.array([0.01, 0.05, 0.1, 0.2, 0.5, 1.0])
    y_uncertainty = np.array([20, 30, 50, 60, 100, 150])

    print(f"   Standards: {x_standards}")
    print(f"   Measurements: {y_measured}")
    print(f"   X uncertainties: {x_uncertainty}")
    print(f"   Y uncertainties: {y_uncertainty}")

    # =========================================================================
    # 2. Run ODR Bootstrap Fitting
    # =========================================================================
    print("\n[2/4] Running ODR Bootstrap (N=2000 resamples)...")

    confidence_data, best_fit_params, points, all_params, subsamples = ODR_Bootstrap(
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

    print(f"   Best fit slope: {best_fit_params[0]:.2f}")
    print(f"   Best fit intercept: {best_fit_params[1]:.2f}")
    print(f"   Bootstrap resamples computed: {len(all_params) - 1}")
    print(f"   Data points after NaN removal: {len(points)}")

    # =========================================================================
    # 3. Plot Confidence Intervals
    # =========================================================================
    print("\n[3/4] Plotting regression with confidence intervals...")

    fig, ax = plt.subplots(figsize=(10, 6))
    plot_regression(
        confidence_data,
        datapoints=points,
        ax=ax,
        ecolor="lightblue",
        line_color="darkblue",
        e_alpha=0.4,
        linewidth=2.5,
    )
    ax.set_xlabel("Concentration (ppm)", fontsize=12)
    ax.set_ylabel("Ion Intensity (counts)", fontsize=12)
    ax.set_title("SIMS Calibration Curve with 95% Bootstrap CI", fontsize=14)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "calibration_curve.png", dpi=150, bbox_inches="tight")
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_curve.png'}")
    plt.close(fig)

    # =========================================================================
    # 4. Plot Calibration Estimate Distributions
    # =========================================================================
    print("\n[4/4] Plotting calibration estimate distributions...")

    # Extract slope and intercept from all bootstrap results
    all_slopes = np.array([p[0] for p in all_params])
    all_intercepts = np.array([p[1] for p in all_params])

    # Compute uncertainties (standard deviation of bootstrap samples)
    slope_mean = all_slopes.mean()
    slope_std = all_slopes.std()
    intercept_mean = all_intercepts.mean()
    intercept_std = all_intercepts.std()

    # For plotting, we'll use the bootstrap results as "measurements"
    # with their standard deviations as "errors"
    fit_params = np.array([
        [slope_mean, intercept_mean]
        for _ in range(5)  # Create 5 "measurements"
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
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_estimates.png'}")
    plt.close(fig)

    # =========================================================================
    # Summary Statistics
    # =========================================================================
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
