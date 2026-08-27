# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-08-27

### Added
- `fit_defaults(x, y, fit_intercept=True)` — computes `initial_guess`,
  `line_max`, and `line_interval` from data via a least-squares pre-fit
  (`numpy.polyfit`). Use this before calling any fitting or confidence function
  to get starting parameters appropriate for the scale of your data.

### Changed
- **Breaking rename** — all public names now follow PEP 8 `snake_case`:

  | Old name | New name |
  |---|---|
  | `ODR_Linear` | `fit_odr_linear` |
  | `ODR_Linear_Test` | `fit_odr_linear_debug` |
  | `Bootstrap_fit` | `bootstrap_odr_fit` |
  | `Eval_Conf` | `evaluate_confidence` |
  | `gauss_agv_err` | `gaussian_aggregate` |
  | `plot_datapoints` | `plot_density` |
  | `plot_Calibration_Estimates` | `plot_calibration_estimates` |
  | `yint_func` | `linear_with_intercept` |
  | `slope_func` | `linear_through_origin` |

- **Parameter renames** — all parameters follow `snake_case`:
  `InitialGuess→initial_guess`, `InterceptFit/intercept→fit_intercept`,
  `Confidence_Bound→confidence_level`, `LineMax→line_max`,
  `LineInt/LineInterval→line_interval`, `Fit_Param→fit_params`, `Title→title`

- `initial_guess` defaults to `None` everywhere; the function auto-derives a
  starting point from a least-squares fit when `None` is passed.

- `fit_intercept` default unified to `True` across all functions (`ODR_Linear`
  previously defaulted to `False`).

- `line_max` and `line_interval` are now **required** in `evaluate_confidence`;
  `odr_bootstrap` auto-derives them from `fit_defaults` when `None`.

### Removed
- Dead parameters that did nothing at runtime:
  - `sigma` from `plot_regression`
  - `plot` from `odr_bootstrap`
  - `cut_off` from `gaussian_aggregate`
  - `**kwargs` aliases `line_max`/`line_interval` from `evaluate_confidence`
- Duplicate nested definitions of `linear_with_intercept` /
  `linear_through_origin` inside the two ODR fit functions.

## [0.1.0] - 2025-04-21

### Added
- Initial release of `odr-bootstrap` package
- **Core Functions**:
  - `ODR_Linear()`: Single ODR fit with optional intercept
  - `ODR_Linear_Test()`: ODR fit with full diagnostics output
  - `Bootstrap_fit()`: Bootstrap resampling with ODR refitting
  - `Eval_Conf()`: Confidence interval evaluation from bootstrap samples
  - `ODR_Bootstrap()`: Convenience wrapper combining Bootstrap_fit + Eval_Conf

- **Statistics Functions**:
  - `gauss_agv_err()`: Aggregate Gaussian distributions into KDE
  - Helper functions: `yint_func()`, `slope_func()`, `plot_datapoints()`

- **Plotting Functions**:
  - `plot_regression()`: Best-fit line with confidence band
  - `plot_Calibration_Estimates()`: Side-by-side slope/intercept distributions

- **Testing**: 22 comprehensive unit tests with 100% pass rate
- **Documentation**: NumPy-style docstrings for all functions
- **Examples**: Complete workflow example in `examples/example.py`
- **Packaging**: Proper Python package structure with pyproject.toml (hatchling backend)
- **License**: MIT License

### Technical Details
- **Python Version**: 3.12+ required
- **Dependencies**:
  - numpy >= 2.2.4
  - scipy >= 1.15.2 (includes fix for deprecated `scipy.odr`)
  - pandas >= 2.2.3
  - matplotlib >= 3.10.1
- **Compatibility**: Fixed zero-intercept ODR initialization for scipy.odr
- **Deprecation Handling**: Updated `np.trapz` → `np.trapezoid` for scipy 1.15+ compatibility

---

[Unreleased]: https://github.com/whtowbin/odr_bootstrap_package/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/whtowbin/odr_bootstrap_package/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/whtowbin/odr_bootstrap_package/releases/tag/v0.1.0
