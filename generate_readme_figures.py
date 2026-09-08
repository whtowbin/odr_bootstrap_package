#%%
"""One-off generator for the README's own figures.

Runs the exact code shown in README.md's "Quick Start" and "Visualising
parameter uncertainty" sections (copied verbatim) so the two saved images
actually match the code printed above them, then saves the result under
distinct filenames (readme_calibration_curve.png / readme_calibration_estimates.png)
so a future `make regen-examples` run (which regenerates
calibration_curve.png / calibration_estimates.png from examples/example.py's
different dataset) can't silently overwrite them again.

Not part of the package or its build/regen pipeline — run manually whenever
the README's own code samples change:

    uv run --extra examples python generate_readme_figures.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from odr_bootstrap import (  # noqa: E402
    fit_defaults,
    gaussian_aggregate,
    odr_bootstrap,
    plot_density,
    plot_regression,
)

REPO_ROOT = Path(__file__).resolve().parent

# ── README "Quick Start" block, verbatim ────────────────────────────────────
# Calibration standards: x = measured count rate, y = known concentration
x_counts      = np.array([   117,  223,   528, 640,  1014,  2071])   # count rate
y_conc        = np.array([  46.0,  54.5,   73.8, 84.8, 169.9,  216.1])   # ppm
x_uncertainty = np.array([   22,   35,    77,  48,   109,    241])     # counting sigma
y_uncertainty = y_conc * 0.15  + 5                                       # 2 % of concentration

# Derive starting parameters automatically
defaults = fit_defaults(x_counts, y_conc)

# Fit with 2000 bootstrap resamples
confidence_data, best_fit_params, points, all_params, _ = odr_bootstrap(
    x=x_counts,
    y=y_conc,
    x_err=x_uncertainty,
    y_err=y_uncertainty,
    resample_draws=2000,
    initial_guess=defaults["initial_guess"],
    line_max=defaults["line_max"],
    line_interval=defaults["line_interval"],
)

slope, intercept = best_fit_params
print(f"concentration = {slope:.5f} x count_rate + {intercept:.4f}")

# Plot the fit with a 95% confidence band
fig, ax = plt.subplots(figsize=(8, 5))
plot_regression(confidence_data, datapoints=points, ax=ax,
                ecolor="lightblue", line_color="darkblue", linewidth=2)
ax.set_xlabel("Count rate (counts)")
ax.set_ylabel("Concentration (ppm)")
plt.tight_layout()
plt.savefig(REPO_ROOT / "readme_calibration_curve.png", dpi=150)
plt.close(fig)
print(f"Saved: {REPO_ROOT / 'readme_calibration_curve.png'}")

# ── README "Visualising parameter uncertainty" block, verbatim ─────────────
all_params_array = np.asarray(all_params, dtype=float)
slopes     = all_params_array[:, 0]
intercepts = all_params_array[:, 1]

slope_dist,     slope_stats     = gaussian_aggregate(slopes,     np.full_like(slopes,     slopes.std()))
intercept_dist, intercept_stats = gaussian_aggregate(intercepts, np.full_like(intercepts, intercepts.std()))

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
plot_density(slope_dist,     slope_stats,     ax=axes[0])
plot_density(intercept_dist, intercept_stats, ax=axes[1])
axes[0].set_title("Slope Distribution")
axes[1].set_title("Intercept Distribution")
plt.tight_layout()
plt.savefig(REPO_ROOT / "readme_calibration_estimates.png", dpi=150)
plt.close(fig)
print(f"Saved: {REPO_ROOT / 'readme_calibration_estimates.png'}")

# %%
