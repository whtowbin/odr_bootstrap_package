#%%
"""Complete ODR Bootstrap calibration workflow.

This script is the single source of truth for the code shown in the Sphinx
docs (``docs/source/examples.rst`` pulls sections of this file directly via
``literalinclude``), so keep the section banner comments below intact when
editing — they mark the ``:start-after:``/``:end-before:`` anchors used there.

Calibration axis convention
----------------------------
x = measured ion count rate (counts)   ← independent variable with counting noise
y = known concentration (ppm)          ← dependent variable

The workflow:
  1. Fits a linear calibration to fixed, reproducible SIMS-style standards.
  2. Repeats the fit with two additional off-trend standards retained to
     show how potential outliers affect the fit and its bootstrap
     uncertainty (see "Handling Potential Outliers" in the docs).
  3. Applies the *outlier-affected* calibration to unknown **concentration**
     values, evaluating the Y variable (``apply_calibration_y``) to estimate
     the corresponding count rate with bootstrap confidence intervals.
  4. Renders the results with Great Tables and saves all figures/HTML to
     examples/ and docs/source/_static/.

Run:
    uv run --extra examples python examples/example.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

try:
    from great_tables import GT, md
except ModuleNotFoundError:  # pragma: no cover - optional example dependency
    GT = None
    md = None

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from odr_bootstrap import (  # noqa: E402
    apply_calibration_y,
    evaluate_confidence,
    fit_defaults,
    gaussian_aggregate,
    odr_bootstrap,
    plot_density,
    plot_regression,
)

OUTPUT_DIR = Path(__file__).resolve().parent
DOCS_STATIC_DIR = REPO_ROOT / "docs" / "source" / "_static"

# ──────────────────────────────────────────────────────────────────────────────
# Fixed calibration standards
# x = ion count rate from reference standards (counts)
# y = known concentration of those standards (ppm)
# ──────────────────────────────────────────────────────────────────────────────
# section:standards
X_COUNTS = np.array([62, 117, 223, 528, 1014, 2001])  # count rate
Y_CONC = np.array([0.5, 1.0, 2.0, 5.0, 10.0, 20.0])  # ppm
X_UNCERTAINTY = np.array([15, 20, 25, 40, 60, 80])  # counting sigma
Y_UNCERTAINTY = Y_CONC * 0.02  # 2 % of concentration
# end-section:standards

# Unknown samples: known/measured concentrations whose count rate we want to
# back-estimate (evaluating the Y variable of the calibration).
UNKNOWN_CONC = np.array([0.8, 3.5, 7.0, 15.0])  # ppm


def main() -> None:
    """Run the complete calibration workflow and save figures/tables."""

    DOCS_STATIC_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("ODR Bootstrap Calibration Example")
    print("=" * 70)

    # =========================================================================
    # 1. Fit the clean calibration
    # =========================================================================
    print("\n[1/6] Fitting calibration to the fixed standards...")

    # section:clean-fit
    defaults = fit_defaults(X_COUNTS, Y_CONC, fit_intercept=True)
    initial_guess = defaults["initial_guess"]
    line_max = defaults["line_max"] * 1.2
    line_interval = defaults["line_interval"]

    confidence_data, best_fit_params, points, all_params, _ = odr_bootstrap(
        x=X_COUNTS,
        y=Y_CONC,
        x_err=X_UNCERTAINTY,
        y_err=Y_UNCERTAINTY,
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
    # end-section:clean-fit

    print(f"   Best-fit slope:     {best_fit_params[0]:.6f}  ppm / count")
    print(f"   Best-fit intercept: {best_fit_params[1]:.6f}  ppm")
    print(f"   Bootstrap resamples: {len(all_params) - 1}")
    print(f"   Data points after NaN removal: {len(points)}")

    # =========================================================================
    # 2. Fit the outlier-affected calibration
    # =========================================================================
    print("\n[2/6] Fitting calibration with two retained potential outliers...")

    # section:outlier-fit
    # Two additional standards that fall well off the fitted trend. They are
    # intentionally retained (not discarded) because there is no independent
    # evidence they are bad measurements — see "Handling Potential Outliers".
    x_outlier = np.concatenate([X_COUNTS, [750.0, 1500.0]])
    y_outlier = np.concatenate([Y_CONC, [10.3, 10.8]])
    x_outlier_err = np.concatenate([X_UNCERTAINTY, [70, 130]])
    y_outlier_err = np.concatenate([Y_UNCERTAINTY, [0.3, 0.3]])

    outlier_defaults = fit_defaults(x_outlier, y_outlier, fit_intercept=True)
    outlier_line_max = outlier_defaults["line_max"] * 1.2
    outlier_line_interval = outlier_defaults["line_interval"]

    outlier_confidence_data, outlier_best_fit, outlier_points, outlier_params, _ = odr_bootstrap(
        x=x_outlier,
        y=y_outlier,
        x_err=x_outlier_err,
        y_err=y_outlier_err,
        resample_draws=2000,
        fit_intercept=True,
        initial_guess=outlier_defaults["initial_guess"],
        confidence_level=0.95,
        line_max=outlier_line_max,
        line_interval=outlier_line_interval,
    )

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
    # end-section:outlier-fit

    print(f"   Best-fit slope:     {outlier_best_fit[0]:.6f}  ppm / count")
    print(f"   Best-fit intercept: {outlier_best_fit[1]:.6f}  ppm")
    print(f"   Bootstrap resamples: {len(outlier_params) - 1}")
    print(f"   Data points after NaN removal: {len(outlier_points)}")

    # =========================================================================
    # 3. Plot regression with 68% and 95% confidence intervals
    # =========================================================================
    print("\n[3/6] Plotting regression with 68% and 95% confidence intervals...")

    # section:plot-clean
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
    ax.set_xlabel("Count Rate (counts)", fontsize=12)
    ax.set_ylabel("Concentration (ppm)", fontsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "calibration_curve.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPO_ROOT / "calibration_curve.png", dpi=150, bbox_inches="tight")
    fig.savefig(DOCS_STATIC_DIR / "calibration_curve.png", dpi=150, bbox_inches="tight")
    # end-section:plot-clean
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_curve.png'}")
    plt.close(fig)

    # =========================================================================
    # 4. Plot calibration estimate distributions
    # =========================================================================
    print("\n[4/6] Plotting calibration estimate distributions...")

    # section:plot-clean-estimates
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
    # end-section:plot-clean-estimates
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_estimates.png'}")
    plt.close(fig)

    # =========================================================================
    # 5. Plot sensitivity to retained potential outliers
    # =========================================================================
    print("\n[5/6] Plotting sensitivity to retained potential outliers...")

    # section:plot-outlier
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
    ax.set_xlabel("Count Rate (counts)", fontsize=12)
    ax.set_ylabel("Concentration (ppm)", fontsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "calibration_curve_outlier.png", dpi=150, bbox_inches="tight")
    fig.savefig(REPO_ROOT / "calibration_curve_outlier.png", dpi=150, bbox_inches="tight")
    fig.savefig(DOCS_STATIC_DIR / "calibration_curve_outlier.png", dpi=150, bbox_inches="tight")
    # end-section:plot-outlier
    print(f"   ✓ Saved: {OUTPUT_DIR / 'calibration_curve_outlier.png'}")
    plt.close(fig)

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

    # =========================================================================
    # 6. Apply the outlier-affected calibration, evaluating the Y variable
    # =========================================================================
    print("\n[6/6] Applying the outlier-affected calibration to unknown concentrations...")

    # section:apply-calibration
    # `outlier_params` (not the clean-fit `all_params`) is used deliberately:
    # since the potential outliers cannot be excluded on independent grounds,
    # the applied calibration should reflect the wider, outlier-affected
    # uncertainty. `apply_calibration_y` evaluates the Y variable — the
    # inputs are known/measured concentrations (ppm) and the output is the
    # corresponding estimated count rate with bootstrap confidence intervals.
    # `line_max`/`line_interval` must span the count-rate (x) axis, not the
    # concentration (y) values being supplied, so they are carried over from
    # the outlier fit rather than left to be inferred from `UNKNOWN_CONC`.
    results = apply_calibration_y(
        UNKNOWN_CONC,
        outlier_params,
        fit_intercept=True,
        confidence_levels=(0.68, 0.95),
        line_max=outlier_line_max,
        line_interval=outlier_line_interval,
    )
    # end-section:apply-calibration
    print(results.to_string(float_format="{:.3f}".format, index=False))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\nClean fit parameters:")
    print(f"  Slope:     {best_fit_params[0]:8.6f}")
    print(f"  Intercept: {best_fit_params[1]:8.6f}")
    print(f"\nClean bootstrap statistics (N={len(all_params) - 1}):")
    print(f"  Slope mean:     {slope_mean:.6f} ± {slope_std:.6f}")
    print(f"  Intercept mean: {intercept_mean:.6f} ± {intercept_std:.6f}")
    print("\nOutlier-affected fit parameters:")
    print(f"  Slope:     {outlier_best_fit[0]:8.6f}")
    print(f"  Intercept: {outlier_best_fit[1]:8.6f}")

    # =========================================================================
    # Render the results table with Great Tables
    # =========================================================================
    if GT is None or md is None:
        print("\n   great_tables not installed — skipping HTML table output.")
        print("   Install with:  uv sync --extra examples")
        return

    _save_results_table(results)


def _save_results_table(df) -> None:  # type: ignore[no-untyped-def]
    """Build and save the concentration → count-rate results table."""
    # section:render-table
    display = df.copy()
    display.insert(0, "Sample ID", [f"Unknown {i + 1}" for i in range(len(display))])
    display = display.rename(columns={
        "input_value": "Known concentration (ppm)",
        "best_fit": "Estimated count rate (counts)",
        "median": "Median count rate (counts)",
        "neg_ci_68": "Lower 68 % CI (counts)",
        "pos_ci_68": "Upper 68 % CI (counts)",
        "neg_ci_95": "Lower 95 % CI (counts)",
        "pos_ci_95": "Upper 95 % CI (counts)",
    })

    tbl = (
        GT(display, rowname_col="Sample ID")
        .tab_header(
            title="Unknown sample count rates",
            subtitle="Concentration converted to count rate using the outlier-affected bootstrap calibration",
        )
        .fmt_number(
            columns=["Known concentration (ppm)"],
            decimals=2,
        )
        .fmt_number(
            columns=[
                "Estimated count rate (counts)", "Median count rate (counts)",
                "Lower 68 % CI (counts)", "Upper 68 % CI (counts)",
                "Lower 95 % CI (counts)", "Upper 95 % CI (counts)",
            ],
            decimals=1,
        )
        .tab_spanner(
            label="68 % CI (counts)",
            columns=["Lower 68 % CI (counts)", "Upper 68 % CI (counts)"],
        )
        .tab_spanner(
            label="95 % CI (counts)",
            columns=["Lower 95 % CI (counts)", "Upper 95 % CI (counts)"],
        )
        .tab_source_note(source_note=md(
            "Calibration fit: **concentration (ppm) = slope × count rate + intercept**, fit with two "
            "retained potential outliers. Confidence intervals propagated from 2000 bootstrap resamples "
            "of the outlier-affected ODR fit."
        ))
    )
    # end-section:render-table

    html = tbl.as_raw_html()
    (OUTPUT_DIR / "calibration_results.html").write_text(html, encoding="utf-8")
    (DOCS_STATIC_DIR / "calibration_results.html").write_text(html, encoding="utf-8")
    print("\n   ✓ Saved: calibration_results.html")


if __name__ == "__main__":
    main()

# %%
