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

Full documentation at [Read the Docs](https://odr-bootstrap-package.readthedocs.io/en/latest/index.html) — including [Examples](https://odr-bootstrap-package.readthedocs.io/en/latest/examples.html) and [API Reference](https://odr-bootstrap-package.readthedocs.io/en/latest/api.html).

## Quick Start

```python
import numpy as np
import matplotlib.pyplot as plt
from odr_bootstrap import odr_bootstrap, fit_defaults, plot_regression

# Calibration standards: x = measured count rate, y = known concentration
x_counts      = np.array([62,   117,  223,   528,   1014,  2001])   # count rate
y_conc        = np.array([0.5,  1.0,  2.0,   5.0,   10.0,  20.0])   # ppm
x_uncertainty = np.array([15,   20,   25,    40,     60,    80])     # counting σ
y_uncertainty = y_conc * 0.02                                         # 2 % of concentration

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
print(f"concentration = {slope:.5f} × count_rate + {intercept:.4f}")

# Plot the fit with a 95% confidence band
fig, ax = plt.subplots(figsize=(8, 5))
plot_regression(confidence_data, datapoints=points, ax=ax,
                ecolor="lightblue", line_color="darkblue", linewidth=2)
ax.set_xlabel("Count rate (counts)")
ax.set_ylabel("Concentration (ppm)")
plt.tight_layout()
plt.savefig("calibration_curve.png", dpi=150)
plt.show()
```

### Applying the calibration to new measurements

Once the calibration is fitted, `apply_calibration` applies it to new data
and propagates the full bootstrap uncertainty into confidence intervals.

**Calibration axis convention:** place the measured count rate on the x-axis
and the known concentration on the y-axis. Then `apply_calibration(variable="x")`
converts an unknown count rate directly into a concentration — no inversion required.

```python
import numpy as np
from odr_bootstrap import odr_bootstrap, fit_defaults, apply_calibration

# Calibration standards: x = count rate, y = concentration (ppm)
x_counts      = np.array([62,   117,  223,   528,   1014,  2001])
y_conc        = np.array([0.5,  1.0,  2.0,   5.0,   10.0,  20.0])
x_uncertainty = np.array([15,   20,   25,    40,     60,    80])
y_uncertainty = y_conc * 0.02

defaults = fit_defaults(x_counts, y_conc, fit_intercept=True)
confidence_data, best_fit_params, points, all_params, _ = odr_bootstrap(
    x=x_counts, y=y_conc, x_err=x_uncertainty, y_err=y_uncertainty,
    resample_draws=2000, fit_intercept=True,
    initial_guess=defaults["initial_guess"],
    line_max=defaults["line_max"],
    line_interval=defaults["line_interval"],
)

# Convert unknown count rates → concentration (ppm)
unknown_counts = np.array([150.0, 430.0, 850.0, 1600.0])
results = apply_calibration(
    unknown_counts,
    all_params,
    variable="x",
    fit_intercept=True,
    confidence_levels=(0.68, 0.95),
)
print(results.to_string(float_format="{:.3f}".format, index=False))
```

```
 input_value  best_fit  median  neg_ci_68  pos_ci_68  neg_ci_95  pos_ci_95
     150.000     1.340   1.337      1.289      1.359      1.232      1.376
     430.000     4.137   4.126      4.078      4.158      3.994      4.180
     850.000     8.333   8.328      8.241      8.368      8.039      8.397
    1600.000    15.825  15.838     15.642     15.912     15.230     15.941
```

The returned DataFrame has one row per input with columns `input_value`,
`best_fit`, `median`, and `neg_ci_<pct>` / `pos_ci_<pct>` for each requested
confidence level.

Use `great_tables` (optional, `uv sync --extra examples`) to render results
as a publication-ready HTML table — see
[`examples/example.py`](examples/example.py)
for the full worked example, or the
[Examples](https://odr-bootstrap-package.readthedocs.io/en/latest/examples.html)
page for the rendered output table.

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

Running `python examples/example.py` produces four figures and a results table. The first two show the clean calibration fit; the second two repeat the analysis with two retained potential outliers so you can see how they affect the result; the calibration is then applied — using the outlier-affected fit — to estimate count rates from known concentrations.

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
