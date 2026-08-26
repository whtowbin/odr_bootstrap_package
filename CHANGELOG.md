# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Pre-commit configuration for automated code quality checks
- GitHub Actions CI/CD workflows for testing and PyPI publishing
- Comprehensive type hints (PEP 484) for all public functions
- Coverage reporting with `pytest-cov` (85% threshold)
- Sphinx documentation setup with Read the Docs integration
- Makefile for development workflows (test, lint, build, publish)
- `CONTRIBUTING.md` guidelines for contributors
- Enhanced README with badges, expanded examples, and API reference

### Changed
- Updated `pyproject.toml` with enhanced tool configurations (ruff, mypy, coverage)
- Improved documentation with complete API reference and tutorial
- Split development dependencies (`dev`, `test`, `docs` groups)
- Updated documentation URLs to point to Read the Docs

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

[Unreleased]: https://github.com/whtowbin/odr_bootstrap_package/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/whtowbin/odr_bootstrap_package/releases/tag/v0.1.0
