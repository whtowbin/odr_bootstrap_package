"""
Calibration Application Example
================================
Demonstrates how to apply a fitted ODR Bootstrap calibration to new (unknown)
measurements, converting measured ion count rates into concentration estimates.
Uses fixed calibration standards so the output is fully reproducible.

Calibration axis convention
---------------------------
x = measured ion count rate (counts)   ← independent variable with counting noise
y = known concentration (ppm)          ← dependent variable

Fitting this way means ``apply_calibration(variable="x")`` converts a measured
count rate directly into a concentration with bootstrap confidence intervals —
the standard analytical-calibration workflow for SIMS data.

The script:
  1. Fits a linear calibration to SIMS-style standards.
  2. Applies the calibration to unknown count-rate measurements.
  3. Renders the results with Great Tables and saves HTML artifacts to
     examples/ and docs/source/_static/.

Run:
    uv run --extra examples python examples/calibration_application_example.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

try:
    from great_tables import GT, md
except ModuleNotFoundError:
    GT = None  # type: ignore[assignment]
    md = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from odr_bootstrap import (  # noqa: E402
    apply_calibration,
    fit_defaults,
    odr_bootstrap,
)

OUTPUT_DIR = Path(__file__).resolve().parent
DOCS_STATIC_DIR = REPO_ROOT / "docs" / "source" / "_static"
DOCS_STATIC_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Fixed calibration standards
# x = ion count rate from reference standards (counts)
# y = known concentration of those standards (ppm)
# ──────────────────────────────────────────────────────────────────────────────
X_COUNTS      = np.array([62,   117,  223,   528,   1014,  2001])   # count rate
Y_CONC        = np.array([0.5,  1.0,  2.0,   5.0,   10.0,  20.0])   # ppm
X_UNCERTAINTY = np.array([15,   20,   25,    40,     60,    80])     # counting σ
Y_UNCERTAINTY = Y_CONC * 0.02                                         # 2 % of concentration

# Unknown samples: measured count rates whose concentration we want to estimate
UNKNOWN_COUNTS = np.array([150.0, 430.0, 850.0, 1600.0])


def main() -> None:
    print("=" * 70)
    print("ODR Bootstrap — Calibration Application Example")
    print("Count rate → Concentration (ppm)")
    print("=" * 70)

    # ── 1.  Fit the calibration ────────────────────────────────────────────
    print("\n[1/3] Fitting calibration (count rate → concentration)…")
    defaults = fit_defaults(X_COUNTS, Y_CONC, fit_intercept=True)

    confidence_data, best_fit_params, points, all_params, _ = odr_bootstrap(
        x=X_COUNTS,
        y=Y_CONC,
        x_err=X_UNCERTAINTY,
        y_err=Y_UNCERTAINTY,
        resample_draws=2000,
        fit_intercept=True,
        initial_guess=defaults["initial_guess"],
        confidence_level=0.95,
        line_max=defaults["line_max"],
        line_interval=defaults["line_interval"],
    )

    slope, intercept = best_fit_params
    print(f"   Best-fit slope:     {slope:.6f}  ppm / count")
    print(f"   Best-fit intercept: {intercept:.6f}  ppm")
    print(f"   Bootstrap resamples: {len(all_params) - 1}")

    # ── 2.  Apply calibration: count rate → concentration ─────────────────
    print("\n[2/3] Applying calibration to unknown samples (count rate → ppm)…")
    results = apply_calibration(
        UNKNOWN_COUNTS,
        all_params,
        variable="x",
        fit_intercept=True,
        confidence_levels=(0.68, 0.95),
    )
    print(results.to_string(float_format="{:.3f}".format, index=False))

    # ── 3.  Render Great Tables HTML ───────────────────────────────────────
    print("\n[3/3] Rendering Great Tables HTML…")
    if GT is None or md is None:
        print("   great_tables not installed — skipping HTML output.")
        print("   Install with:  uv sync --extra examples")
        return

    _save_results_table(results)

    print("\n" + "=" * 70)
    print("Done.  HTML table saved to:")
    print(f"   {OUTPUT_DIR / 'calibration_results.html'}")
    print(f"   {DOCS_STATIC_DIR / 'calibration_results.html'}")
    print("=" * 70)


def _save_results_table(df) -> None:  # type: ignore[no-untyped-def]
    """Build and save the count-rate → concentration results table."""
    display = df.copy()
    display.insert(0, "Sample ID", [f"Unknown {i + 1}" for i in range(len(display))])
    display = display.rename(columns={
        "input_value": "Count rate (counts)",
        "best_fit":    "Best-fit conc. (ppm)",
        "median":      "Median conc. (ppm)",
        "neg_ci_68":   "Lower 68 % CI (ppm)",
        "pos_ci_68":   "Upper 68 % CI (ppm)",
        "neg_ci_95":   "Lower 95 % CI (ppm)",
        "pos_ci_95":   "Upper 95 % CI (ppm)",
    })

    tbl = (
        GT(display, rowname_col="Sample ID")
        .tab_header(
            title="Unknown sample concentrations",
            subtitle="Count rate converted to concentration (ppm) using the bootstrap calibration",
        )
        .fmt_number(
            columns=["Count rate (counts)"],
            decimals=0,
        )
        .fmt_number(
            columns=[
                "Best-fit conc. (ppm)", "Median conc. (ppm)",
                "Lower 68 % CI (ppm)", "Upper 68 % CI (ppm)",
                "Lower 95 % CI (ppm)", "Upper 95 % CI (ppm)",
            ],
            decimals=2,
        )
        .tab_spanner(
            label="68 % CI (ppm)",
            columns=["Lower 68 % CI (ppm)", "Upper 68 % CI (ppm)"],
        )
        .tab_spanner(
            label="95 % CI (ppm)",
            columns=["Lower 95 % CI (ppm)", "Upper 95 % CI (ppm)"],
        )
        .tab_source_note(source_note=md(
            "Calibration fit: **concentration (ppm) = slope × count rate + intercept**. "
            "Confidence intervals propagated from 2000 bootstrap resamples of the ODR fit."
        ))
    )

    html = tbl.as_raw_html()
    (OUTPUT_DIR / "calibration_results.html").write_text(html, encoding="utf-8")
    (DOCS_STATIC_DIR / "calibration_results.html").write_text(html, encoding="utf-8")
    print("   ✓ Saved: calibration_results.html")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
