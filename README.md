# ODR Bootstrap

[![Tests](https://github.com/whtowbin/odr_bootstrap_package/actions/workflows/tests.yml/badge.svg)](https://github.com/whtowbin/odr_bootstrap_package/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/static/v1?label=PyPI&message=odr-bootstrap&color=blue)](https://pypi.org/project/odr-bootstrap/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ODR Bootstrap** fits linear calibration curves with rigorous uncertainty in both x and y — no ordinary least-squares assumptions needed.

When measurement errors exist in both the independent variable (x, e.g. concentration) and the dependent variable (y, e.g. signal intensity), ordinary least squares gives biased results. **Orthogonal Distance Regression (ODR)** handles errors in both directions, and **bootstrap resampling** turns those fits into honest confidence intervals without relying on analytical approximations.

In situations when potential outliers cannot be easily excluded—for example, when there is no independent evidence that they are bad measurements—it can be useful to retain them in the regression. Comparing results with and without these points helps quantify their influence on the fitted line and its uncertainty.

The package is used for SIMS (Secondary Ion Mass Spectrometry) calibration but applies to any field where both variables carry measurement uncertainty.

## Installation

```bash
pip install odr-bootstrap
```

```bash
uv add odr-bootstrap
```

### From source

```bash
git clone https://github.com/whtowbin/odr_bootstrap_package.git
cd odr_bootstrap_package
uv sync
```

## Documentation

Full documentation at [Read the Docs](https://odr-bootstrap-package.readthedocs.io/en/latest/index.html) — including a [Tutorial](https://odr-bootstrap-package.readthedocs.io/en/latest/tutorial.html) and [API Reference](https://odr-bootstrap-package.readthedocs.io/en/latest/api.html).

## Quick Start

```python
import numpy as np
import matplotlib.pyplot as plt
from odr_bootstrap import odr_bootstrap, fit_defaults, plot_regression

# Your calibration data
x_standards = np.array([0.1, 0.5, 1.0, 2.0, 5.0])      # known concentrations
y_intensity  = np.array([45, 200, 350, 700, 1450])       # measured signal
x_uncertainty = np.array([0.01, 0.05, 0.1, 0.2, 0.5])   # uncertainty in x
y_uncertainty = np.array([5, 20, 35, 60, 120])           # uncertainty in y

# Derive starting parameters automatically
defaults = fit_defaults(x_standards, y_intensity)

# Fit with 2000 bootstrap resamples
confidence_data, best_fit_params, points, all_params, _ = odr_bootstrap(
    x=x_standards,
    y=y_intensity,
    x_err=x_uncertainty,
    y_err=y_uncertainty,
    resample_draws=2000,
    initial_guess=defaults["initial_guess"],
    line_max=defaults["line_max"],
    line_interval=defaults["line_interval"],
)

slope, intercept = best_fit_params
print(f"y = {slope:.2f}x + {intercept:.2f}")

# Plot the fit with a 95% confidence band
fig, ax = plt.subplots(figsize=(8, 5))
plot_regression(confidence_data, datapoints=points, ax=ax,
                ecolor="lightblue", line_color="darkblue", linewidth=2)
ax.set_xlabel("Concentration (ppm)")
ax.set_ylabel("Signal Intensity (counts)")
plt.tight_layout()
plt.savefig("calibration_curve.png", dpi=150)
plt.show()
```

### Applying the calibration to new measurements

Once the calibration is fitted, you can use the bootstrap-derived uncertainty to estimate unknown values from fresh data in the same way as a standard analytical calibration:

```python
from odr_bootstrap import apply_calibration

# Unknown x values to convert into measured y values
unknown_x = np.array([0.25, 0.75, 3.0])
calibration_results = apply_calibration(
    unknown_x,
    all_params,
    fit_intercept=True,
    variable="x",
    confidence_levels=(0.68, 0.95),
)

print(calibration_results[["input_value", "best_fit", "median", "neg_ci_68", "pos_ci_68", "neg_ci_95", "pos_ci_95"]])
```

If you already know the measured signal and want to back-calculate the corresponding concentration, use the inverse mode:

```python
from odr_bootstrap import apply_calibration_y

unknown_signal = np.array([120.0, 450.0, 900.0])
concentration_estimates = apply_calibration_y(
    unknown_signal,
    all_params,
    fit_intercept=True,
    confidence_levels=(68, 95),
)
print(concentration_estimates)
```

The helper accepts scalar or array-like inputs, defaults to x-input calibration, and returns a DataFrame containing the best-fit value, median estimate, and one or more confidence intervals.

A common analytical-calibration workflow is to convert an unknown ion intensity into a concentration in ppm. The example below uses the fitted bootstrap calibration and renders the result as a Great Tables summary.

The generated HTML table is produced by the example script and saved to [docs/source/_static/unknown_concentrations.html](docs/source/_static/unknown_concentrations.html). Because markdown does not execute Python, the table is not rendered inline in the README itself; it is generated as an HTML artifact from the example script.

```python
import numpy as np
from great_tables import GT, md
from odr_bootstrap import apply_calibration_y

unknown_counts = np.array([150.0, 420.0, 910.0, 1600.0])
unknown_conc = apply_calibration_y(
    unknown_counts,
    all_params,
    fit_intercept=True,
    confidence_levels=(0.68, 0.95),
)

unknown_conc = unknown_conc.rename(
    columns={
        "input_value": "Ion intensity (counts)",
        "best_fit": "Estimated concentration (ppm)",
        "median": "Median concentration (ppm)",
        "neg_ci_68": "Lower 68% CI (ppm)",
        "pos_ci_68": "Upper 68% CI (ppm)",
        "neg_ci_95": "Lower 95% CI (ppm)",
        "pos_ci_95": "Upper 95% CI (ppm)",
    }
)
unknown_conc.insert(0, "Sample ID", [f"Unknown {i + 1}" for i in range(len(unknown_conc))])

summary_table = (
    GT(unknown_conc, rowname_col="Sample ID")
    .tab_header(
        title="Unknown sample concentrations",
        subtitle="Ion intensity to concentration estimates using the bootstrap calibration",
    )
    .fmt_number(
        columns=[
            "Ion intensity (counts)",
            "Estimated concentration (ppm)",
            "Median concentration (ppm)",
            "Lower 68% CI (ppm)",
            "Upper 68% CI (ppm)",
            "Lower 95% CI (ppm)",
            "Upper 95% CI (ppm)",
        ],
        decimals=2,
    )
    .tab_source_note(
        source_note=md("Calibration generated with ODR Bootstrap and propagated uncertainty.")
    )
)

print(summary_table.as_raw_html())
```

To regenerate the table from source, run:

```bash
uv run --extra examples python examples/example.py
```

This produces a compact publication-ready table showing each unknown ion intensity, the best-fit concentration estimate, and both the 68% and 95% confidence intervals.

### Visualising parameter uncertainty

```python
from odr_bootstrap import gaussian_aggregate, plot_density

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
plt.savefig("calibration_estimates.png", dpi=150)
plt.show()
```

## Example Output

Running `python examples/example.py` produces four figures. The first two show the clean calibration fit; the second two repeat the analysis with synthetic outliers so you can see how they affect the result.

### Clean calibration fit

![Calibration curve with 68% and 95% bootstrap confidence intervals](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_curve.png)

The shaded bands are the 68% (inner) and 95% (outer) bootstrap confidence intervals. Narrower bands indicate a more precisely constrained calibration.

### Bootstrap parameter distributions

![Bootstrap slope and intercept distributions](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_estimates.png)

Each histogram shows how the fitted slope and intercept vary across bootstrap resamples, giving you a direct view of parameter uncertainty.

### Fit with synthetic outliers

![Calibration fit with synthetic outliers and dual confidence bands](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_curve_outlier.png)

Including potential outliers in the regression widens the confidence bands and may shift the best-fit line. This illustrates why points that cannot be excluded objectively should be retained: the bootstrap distributions quantify their effect on the fitted parameters and prediction uncertainty.

### Outlier-affected parameter distributions

![Outlier-affected slope and intercept distributions](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_estimates_outlier.png)

The potential outliers broaden and shift both distributions. Comparing these to the clean-data distributions makes their influence easy to quantify.

## Module Functions

### Defaults helper

- **`fit_defaults(x, y, fit_intercept=True)`**  
  Computes sensible starting parameters from your data using a least-squares pre-fit.  
  Returns `{"initial_guess": [...], "line_max": float, "line_interval": float}`.

### Core fitting

- **`fit_odr_linear(x, y, x_err, y_err, fit_intercept=True, initial_guess=None)`**  
  Single ODR fit. Returns `(params, param_errors)`.

- **`bootstrap_odr_fit(x, y, x_err, y_err, resample_draws, ...)`**  
  Fits the ODR model to N random resamples of your data.  
  Returns `(all_fit_params, resampled_data)`.

### Confidence intervals

- **`evaluate_confidence(fit_params, line_max, line_interval, confidence_level=0.95)`**  
  Computes confidence bounds from bootstrap parameter distributions.  
  Returns a DataFrame indexed by x-values.

- **`odr_bootstrap(...)`**  
  Convenience wrapper: runs `bootstrap_odr_fit` + `evaluate_confidence` in one call.  
  `line_max`, `line_interval`, and `initial_guess` are derived automatically when omitted.

### Statistics

- **`gaussian_aggregate(concentrations, errors)`**  
  Aggregates bootstrap distributions into a smooth KDE estimate.  
  Returns `(distribution_dict, statistics_dict)`.

### Plotting

- **`plot_regression(confidence_df, datapoints=None, ax=None, ...)`**  
  Plots the best-fit line with shaded confidence band(s).

- **`plot_density(data, bounds, ax=None, ...)`**  
  Plots a probability density curve from `gaussian_aggregate` output.

- **`plot_calibration_estimates(fit_params, fit_error, title=...)`**  
  Side-by-side slope and intercept distribution plots.

## Requirements

- Python >= 3.11
- numpy >= 2.2.4
- scipy >= 1.15.2
- odrpack >= 0.6.1
- pandas >= 2.2.3
- matplotlib >= 3.10.1

## License

MIT — see [LICENSE](LICENSE).

## Citation

```bibtex
@software{towbin2025odr,
  title  = {ODR Bootstrap: Orthogonal Distance Regression with Bootstrap Resampling},
  author = {Towbin, Henry},
  year   = {2025},
  url    = {https://github.com/whtowbin/odr_bootstrap_package}
}
```
