# ODR Bootstrap

[![Tests](https://github.com/whtowbin/odr_bootstrap_package/actions/workflows/tests.yml/badge.svg)](https://github.com/whtowbin/odr_bootstrap_package/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/static/v1?label=PyPI&message=odr-bootstrap&color=blue)](https://pypi.org/project/odr-bootstrap/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Orthogonal Distance Regression with Bootstrap Resampling for SIMS (Secondary Ion Mass Spectrometry) Calibration

A Python package for robust calibration curve fitting with proper uncertainty quantification in both x and y measurements. 



## Overview

**What is ODR Bootstrap?**

When fitting calibration curves to scientific data, measurement errors exist in both the independent variable (x, e.g., concentration) and dependent variable (y, e.g., ion intensity). Ordinary least squares regression assumes errors only in y, leading to biased fits. 

**Orthogonal Distance Regression (ODR)** properly accounts for uncertainties in both x and y. **Bootstrap resampling** estimates confidence intervals by repeatedly refitting the model to random subsamples of the calibration data.

This package combines these techniques for publication-ready uncertainty quantification in SIMS (Secondary Ion Mass Spectrometry) calibration analysis. It is broadly applicable to other types of analytical calibrations and uses of linear regressions. Bootstrapping ensures that the fits are not overly skewed by outliers.



## Installation

### With UV (recommended)

```bash
uv pip install odr-bootstrap
```

### With pip

```bash
pip install odr-bootstrap
```

### From source

```bash
git clone https://github.com/whtowbin/odr_bootstrap_package.git
cd odr_bootstrap_package
uv sync
# or
pip install -e .
```

## Documentation

Full documentation is available at [Read the Docs](https://odr-bootstrap-package.readthedocs.io/en/latest/index.html).


For quick reference, see:
- [API Reference](https://odr-bootstrap-package.readthedocs.io/en/latest/api.html)
- [Tutorial & Examples](https://odr-bootstrap-package.readthedocs.io/en/latest/tutorial.html)
- [Examples Directory](./examples)

## Quick Start

```python
import numpy as np
import matplotlib.pyplot as plt
from odr_bootstrap import odr_bootstrap, fit_defaults, plot_regression

# Prepare calibration data
x_standards = np.array([0.1, 0.5, 1.0, 2.0, 5.0])      # Concentrations
y_intensity = np.array([45, 200, 350, 700, 1450])        # Ion counts
x_uncertainty = np.array([0.01, 0.05, 0.1, 0.2, 0.5])   # Errors in x
y_uncertainty = np.array([5, 20, 35, 60, 120])           # Errors in y

# Derive sensible starting parameters from the data
defaults = fit_defaults(x_standards, y_intensity)

# Run ODR bootstrap with 2000 resamples
confidence_data, best_fit_params, points, all_params, subsamples = odr_bootstrap(
    x=x_standards,
    y=y_intensity,
    x_err=x_uncertainty,
    y_err=y_uncertainty,
    resample_draws=2000,
    fit_intercept=True,
    initial_guess=defaults["initial_guess"],
    confidence_level=0.95,
    line_max=defaults["line_max"],
    line_interval=defaults["line_interval"],
)

# Plot the result
fig, ax = plt.subplots(figsize=(8, 5))
plot_regression(
    confidence_data,
    datapoints=points,
    ax=ax,
    ecolor='lightblue',
    line_color='darkblue',
    linewidth=2,
)
ax.set_xlabel('Concentration (ppm)')
ax.set_ylabel('Ion Intensity (counts)')
ax.set_title('SIMS Calibration Curve with 95% Bootstrap CI')
plt.tight_layout()
plt.savefig('calibration_curve.png', dpi=150)
plt.show()

# Access results
print(f"Slope: {best_fit_params[0]:.2f}")
print(f"Intercept: {best_fit_params[1]:.2f}")
```

### Plotting Calibration Estimate Distributions

```python
from odr_bootstrap import gaussian_aggregate, plot_density
import numpy as np

# Extract bootstrap parameter distributions
all_params_array = np.asarray(all_params, dtype=float)
all_slopes = all_params_array[:, 0]
all_intercepts = all_params_array[:, 1]

# Aggregate into smooth distributions
slope_dist, slope_stats = gaussian_aggregate(
    all_slopes, np.full_like(all_slopes, all_slopes.std())
)
intercept_dist, intercept_stats = gaussian_aggregate(
    all_intercepts, np.full_like(all_intercepts, all_intercepts.std())
)

# Generate plot
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
plot_density(slope_dist, slope_stats, ax=axes[0])
plot_density(intercept_dist, intercept_stats, ax=axes[1])
axes[0].set_title('Slope Distribution')
axes[1].set_title('Intercept Distribution')
plt.tight_layout()
plt.savefig('calibration_estimates.png', dpi=150)
plt.show()
```

## Example Output

The example script produces four useful figures for calibration analysis:

### Calibration curve with 68% and 95% bootstrap confidence bands

![Calibration curve with 68% and 95% bootstrap confidence intervals](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_curve.png)

This single figure shows the fitted calibration line with both the narrower 68% interval and the broader 95% interval. It is useful for publication figures and for interpreting the precision of the calibration at different confidence levels.

### Synthetic outlier sensitivity example

![Synthetic calibration data with larger outliers and dual confidence bands](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_curve_outlier.png)

This second regression plot demonstrates how larger outliers affect the fit and broaden the uncertainty band, while also showing the 68% and 95% confidence envelopes in the same plot.

### Bootstrap parameter distributions

![Bootstrap slope and intercept distributions](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_estimates.png)

This plot summarizes the distribution of the fitted slope and intercept across bootstrap resamples. It helps communicate how stable the calibration parameters are and how much uncertainty is associated with the estimated fit.

### Outlier-affected parameter statistics

![Outlier-affected slope and intercept distributions](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_estimates_outlier.png)

This comparison shows how a larger anomalous point broadens and shifts the parameter distributions. The Gaussian aggregate representation makes the effect of the outlier easy to visualize in the same statistical language as the clean calibration fit.

## Module Functions

### Defaults Helper

- **`fit_defaults(x, y, fit_intercept=True)`**  
  Compute sensible starting parameters from data using a least-squares pre-fit.  
  Returns: `{"initial_guess": [...], "line_max": float, "line_interval": float}`

### Core Fitting

- **`fit_odr_linear(x, y, x_err, y_err, fit_intercept=True, initial_guess=None)`**  
  Single orthogonal distance regression fit. `initial_guess=None` auto-derives from the data.  
  Returns: `(params, param_errors)`

- **`fit_odr_linear_debug(x, y, x_err, y_err, ...)`**  
  Same as `fit_odr_linear` but also returns the raw `scipy.odr.Output` object for diagnostics.

- **`bootstrap_odr_fit(x, y, x_err, y_err, resample_draws, ...)`**  
  Resample data N times and refit the ODR model to each resample.  
  Returns: `(all_fit_params, resampled_data)`

### Confidence Intervals

- **`evaluate_confidence(fit_params, line_max, line_interval, confidence_level=0.95)`**  
  Compute confidence intervals from bootstrap parameter distributions.  
  Returns: DataFrame with confidence bounds indexed by x-values.

- **`odr_bootstrap(...)`**  
  Top-level convenience wrapper: calls `bootstrap_odr_fit` + `evaluate_confidence`.  
  `line_max`, `line_interval`, and `initial_guess` are auto-derived when `None`.

### Statistics

- **`gaussian_aggregate(concentrations, errors)`**  
  Aggregate multiple normal distributions into a single KDE estimate.  
  Returns: `(distribution_dict, statistics_dict)`

### Plotting

- **`plot_regression(confidence_df, datapoints=None, ax=None, ...)`**  
  Plot best-fit line with shaded confidence band(s).

- **`plot_density(data, bounds, ax=None, ...)`**  
  Plot a probability density curve from `gaussian_aggregate` output with summary statistics.

- **`plot_calibration_estimates(fit_params, fit_error, title=...)`**  
  Side-by-side slope and intercept distribution plots.


## Example Workflow

See [examples/example.py](examples/example.py) for a complete working example:

```bash
cd examples
python example.py
```

This generates:
- `calibration_curve.png` - Fitted line with both 68% and 95% confidence bands
- `calibration_curve_outlier.png` - Synthetic example with a larger outlier and dual confidence bands
- `calibration_estimates.png` - Bootstrap parameter distributions

## API Reference

Full documentation is available in function docstrings:

```python
from odr_bootstrap import odr_bootstrap
help(odr_bootstrap)
```

## Requirements

- Python >= 3.11
- numpy >= 2.2.4
- scipy >= 1.15.2
- pandas >= 2.2.3
- matplotlib >= 3.10.1

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Citation

If you use this package in research, please cite:

```bibtex
@software{towbin2025odr,
  title={ODR Bootstrap: Orthogonal Distance Regression with Bootstrap Resampling},
  author={Towbin, Henry},
  year={2025},
  url={https://github.com/whtowbin/odr_bootstrap_package}
}
```


---

**Status**: Beta (0.2.0) | **Last Updated**: August 2025
