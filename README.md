# ODR Bootstrap

Orthogonal Distance Regression with Bootstrap Resampling for SIMS Calibration

A Python package for robust calibration curve fitting with proper uncertainty quantification in both x and y measurements.

## Overview

**ODR Bootstrap** is a specialized tool for secondary ion mass spectrometry (SIMS) calibration analysis. It implements:

- **Orthogonal Distance Regression (ODR)**: Fit linear calibration curves when measurement uncertainties exist in both x and y
- **Bootstrap Resampling**: Quantify parameter uncertainty through repeated random subsampling
- **Confidence Interval Estimation**: Compute and visualize confidence bands around fitted lines
- **Robust Statistics**: Aggregate multiple calibration measurements into distribution estimates

The code handles publication-quality analysis with proper error propagation and visualization.

## Features

✅ NumPy-style documentation for all functions  
✅ 22 comprehensive unit tests (100% pass rate)  
✅ Runnable example workflow with synthetic data  
✅ Compatible with scipy 1.15+ (deprecated API updates)  
✅ Zero-intercept fits with proper parameter handling  
✅ Publication-ready calibration plots  

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
git clone https://github.com/whtowbin/odr-bootstrap.git
cd odr-bootstrap
uv sync
# or
pip install -e .
```

## Quick Start

### Basic Calibration Fit

```python
import numpy as np
import matplotlib.pyplot as plt
from odr_bootstrap import ODR_Bootstrap, plot_regression

# Prepare calibration data
x_standards = np.array([0.1, 0.5, 1.0, 2.0, 5.0])      # Concentrations
y_intensity = np.array([45, 200, 350, 700, 1450])      # Ion counts
x_uncertainty = np.array([0.01, 0.05, 0.1, 0.2, 0.5]) # Measurement errors in x
y_uncertainty = np.array([5, 20, 35, 60, 120])         # Measurement errors in y

# Run ODR bootstrap with 2000 resamples
confidence_data, best_fit_params, points, all_params, subsamples = ODR_Bootstrap(
    x=x_standards,
    y=y_intensity,
    x_err=x_uncertainty,
    y_err=y_uncertainty,
    resample_draws=2000,
    InterceptFit=True,
    InitialGuess=[250, 10],
    Confidence_Bound=0.95,
    LineMax=6,
)

# Plot the result
fig, ax = plt.subplots(figsize=(8, 5))
plot_regression(confidence_data, datapoints=points, ax=ax, 
                ecolor='lightblue', line_color='darkblue', linewidth=2)
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
from odr_bootstrap import plot_Calibration_Estimates
import numpy as np

# Extract bootstrap parameter distributions
all_slopes = np.array([p[0] for p in all_params])
all_intercepts = np.array([p[1] for p in all_params])

# Create synthetic measurement ensemble (for visualization)
fit_params = np.array([[all_slopes.mean(), all_intercepts.mean()]] * 5)
fit_params += np.random.normal(0, [all_slopes.std(), all_intercepts.std()], (5, 2))
fit_error = np.array([[all_slopes.std(), all_intercepts.std()]] * 5)

# Generate plot
fig = plot_Calibration_Estimates(fit_params, fit_error,
                               Title="Calibration Slope & Intercept Distributions")
plt.savefig('calibration_estimates.png', dpi=150)
plt.show()
```

## Module Functions

### Core Fitting

- **`ODR_Linear(x, y, x_err, y_err, intercept=False, InitialGuess=[100, 1])`**  
  Single orthogonal distance regression fit with optional y-intercept.
  Returns: (fitted_params, param_uncertainties)

- **`ODR_Linear_Test(x, y, x_err, y_err, ...)`**  
  ODR fit returning full scipy.odr output object for diagnostics.

- **`Bootstrap_fit(x, y, x_err, y_err, resample_draws, ...)`**  
  Resample data N times and fit ODR model to each resample.
  Returns: (all_fit_params, resampled_data)

### Confidence Intervals

- **`Eval_Conf(Fit_Param, Confidence_Bound=0.95, LineMax=200, ...)`**  
  Compute confidence intervals from bootstrap parameter distributions.
  Returns: DataFrame with confidence bounds indexed by x-values.

- **`ODR_Bootstrap(...)`**  
  Convenience wrapper combining Bootstrap_fit + Eval_Conf in one call.

### Statistics

- **`gauss_agv_err(concentrations, errors, ...)`**  
  Aggregate multiple normal distributions into single KDE estimate.
  Returns: (distribution_dict, statistics_dict)

### Plotting

- **`plot_regression(confidence_df, datapoints=None, ax=None, ...)`**  
  Plot best-fit line with shaded confidence band.

- **`plot_datapoints(data, bounds, ax=None, ...)`**  
  Plot probability density curve with summary statistics.

- **`plot_Calibration_Estimates(fit_params, fit_error, Title=...)`**  
  Side-by-side slope and intercept distribution plots.

## Testing

Run the comprehensive test suite:

```bash
python -m unittest tests/test_odr_bootstrap.py -v
```

Or with pytest:

```bash
pytest tests/ -v
```

All 22 tests should pass.

## Example Workflow

See [examples/example.py](examples/example.py) for a complete working example:

```bash
cd examples
python example.py
```

This generates:
- `calibration_curve.png` - Fitted line with confidence band
- `calibration_estimates.png` - Bootstrap parameter distributions

## Recent Updates (April 2025)

- ✅ Fixed zero-intercept ODR fits with proper scipy.odr parameter wrapping
- ✅ Updated deprecated np.trapz API to np.trapezoid (scipy 1.15+ compatible)
- ✅ Added comprehensive NumPy-style docstrings to all functions
- ✅ Created 22 unit tests with 100% pass rate
- ✅ Generated runnable example workflow

## API Reference

Full documentation is available in function docstrings:

```python
from odr_bootstrap import ODR_Bootstrap
help(ODR_Bootstrap)
```

## Requirements

- Python >= 3.12
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
  url={https://github.com/whtowbin/odr-bootstrap}
}
```

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Acknowledgments

Developed at Caltech for SIMS calibration analysis workflows.

---

**Status**: Beta (0.1.0) | **Last Updated**: April 2025
