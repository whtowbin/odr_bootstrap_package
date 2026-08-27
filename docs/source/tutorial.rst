========
Tutorial
========

This tutorial walks through a complete calibration workflow using ODR Bootstrap.

Basic Calibration Fit
=====================

The simplest use case: fit a linear calibration curve with confidence intervals.

.. code-block:: python

   import numpy as np
   import matplotlib.pyplot as plt
   from odr_bootstrap import odr_bootstrap, fit_defaults, plot_regression

   # Define calibration standards (known concentrations)
   x_standards = np.array([0.1, 0.5, 1.0, 2.0, 5.0, 10.0])

   # Simulated measurements (ion intensity in counts)
   # True relationship: y = 125*x + 15
   y_measured = 125 * x_standards + 15 + np.random.normal(0, 40, len(x_standards))

   # Measurement uncertainties
   x_uncertainty = np.array([0.01, 0.05, 0.1, 0.2, 0.5, 1.0])
   y_uncertainty = np.array([20, 30, 50, 60, 100, 150])

   # Derive sensible starting parameters from the data
   defaults = fit_defaults(x_standards, y_measured, fit_intercept=True)

   # Run bootstrap with 2000 resamples
   confidence_data, best_fit_params, points, all_params, subsamples = odr_bootstrap(
       x=x_standards,
       y=y_measured,
       x_err=x_uncertainty,
       y_err=y_uncertainty,
       resample_draws=2000,
       fit_intercept=True,
       initial_guess=defaults["initial_guess"],
       confidence_level=0.95,
       line_max=defaults["line_max"],
       line_interval=defaults["line_interval"],
   )

   # Extract results
   slope, intercept = best_fit_params
   print(f"Fitted slope: {slope:.2f}")
   print(f"Fitted intercept: {intercept:.2f}")

Using fit_defaults
==================

``fit_defaults`` computes three parameters that all the fitting functions need:

.. code-block:: python

   from odr_bootstrap import fit_defaults

   defaults = fit_defaults(x_standards, y_measured, fit_intercept=True)
   # defaults["initial_guess"]  → [slope, intercept] from a least-squares fit
   # defaults["line_max"]       → max(x) * 1.1
   # defaults["line_interval"]  → line_max / 1000

   print(defaults)

You can pass the values directly or override any of them:

.. code-block:: python

   # Use auto-derived defaults
   confidence_data, *_ = odr_bootstrap(
       x_standards, y_measured, x_uncertainty, y_uncertainty,
       initial_guess=defaults["initial_guess"],
       line_max=defaults["line_max"],
       line_interval=defaults["line_interval"],
   )

   # Or let odr_bootstrap call fit_defaults internally
   confidence_data, *_ = odr_bootstrap(
       x_standards, y_measured, x_uncertainty, y_uncertainty,
   )

Plotting Results
================

Visualize the fitted line with bootstrap confidence interval:

.. code-block:: python

   # Create figure
   fig, ax = plt.subplots(figsize=(10, 6))

   # Plot best-fit line and confidence band
   plot_regression(
       confidence_data,
       datapoints=points,
       ax=ax,
       ecolor='lightblue',
       line_color='darkblue',
       e_alpha=0.4,
       linewidth=2.5,
   )

   # Customize plot
   ax.set_xlabel('Concentration (ppm)', fontsize=12)
   ax.set_ylabel('Ion Intensity (counts)', fontsize=12)
   ax.set_title('SIMS Calibration Curve with 95% Bootstrap CI', fontsize=14)
   ax.grid(True, alpha=0.3)

   # Save and show
   fig.tight_layout()
   fig.savefig('calibration_curve.png', dpi=150, bbox_inches='tight')
   plt.show()

Understanding the Results
=========================

Return Values Explained
-----------------------

The ``odr_bootstrap`` function returns a 5-tuple:

.. code-block:: python

   confidence_data, best_fit_params, points, all_params, subsamples = odr_bootstrap(...)

- ``confidence_data`` (``pandas.DataFrame``): Confidence interval bounds indexed by x-values. Columns:

  - ``best_fit``: fitted values at each x
  - ``neg_error_bound``: lower confidence bound
  - ``pos_error_bound``: upper confidence bound
  - ``percent_error_neg``: negative percent error
  - ``percent_error_pos``: positive percent error

- ``best_fit_params`` (``numpy.ndarray``): Best-fit parameters ``[slope, intercept]`` from the full dataset.

- ``points`` (``pandas.DataFrame``): Cleaned input data with columns ``x``, ``y``, ``xerr``, and ``yerr`` after NaN rows are removed.

- ``all_params`` (list of ``numpy.ndarray``): Bootstrap parameter estimates. The first element is ``best_fit_params`` and the remaining elements are bootstrap resamples.

- ``subsamples`` (list of ``pandas.DataFrame``): DataFrames used for each bootstrap resample.

Analyzing Bootstrap Distributions
==================================

The package uses :func:`odr_bootstrap.gaussian_aggregate` to summarize the
bootstrap fit distribution for each parameter. This aggregates the actual
bootstrap fits into a smooth approximate distribution.

.. code-block:: python

   from odr_bootstrap import gaussian_aggregate, plot_density

   # Extract bootstrap parameters directly from the parameter array
   all_params_array = np.asarray(all_params, dtype=float)
   all_slopes = all_params_array[:, 0]
   all_intercepts = all_params_array[:, 1]

   # Compute statistics
   slope_mean = all_slopes.mean()
   slope_std = all_slopes.std()
   intercept_mean = all_intercepts.mean()
   intercept_std = all_intercepts.std()

   print(f"Slope: {slope_mean:.2f} ± {slope_std:.2f}")
   print(f"Intercept: {intercept_mean:.2f} ± {intercept_std:.2f}")

   # Aggregate the bootstrap fit distributions
   slope_dist, slope_stats = gaussian_aggregate(
       all_slopes,
       np.full_like(all_slopes, slope_std),
   )
   intercept_dist, intercept_stats = gaussian_aggregate(
       all_intercepts,
       np.full_like(all_intercepts, intercept_std),
   )

   fig, axes = plt.subplots(1, 2, figsize=(12, 5))
   plot_density(slope_dist, slope_stats, ax=axes[0])
   plot_density(intercept_dist, intercept_stats, ax=axes[1])
   axes[0].set_title("Slope Distribution")
   axes[1].set_title("Intercept Distribution")
   fig.tight_layout()
   plt.show()

Zero-Intercept Fits
===================

For fitting through the origin (y = slope * x):

.. code-block:: python

   defaults = fit_defaults(x_standards, y_measured, fit_intercept=False)

   confidence_data, best_fit_params, points, all_params, subsamples = odr_bootstrap(
       x=x_standards,
       y=y_measured,
       x_err=x_uncertainty,
       y_err=y_uncertainty,
       resample_draws=2000,
       fit_intercept=False,
       initial_guess=defaults["initial_guess"],  # [slope] only
       confidence_level=0.95,
       line_max=defaults["line_max"],
       line_interval=defaults["line_interval"],
   )

   slope = best_fit_params[0]
   print(f"Slope (through origin): {slope:.2f}")

Advanced: Custom Confidence Levels
====================================

Compute multiple confidence intervals on the same fit:

.. code-block:: python

   from odr_bootstrap import bootstrap_odr_fit, evaluate_confidence, fit_defaults

   defaults = fit_defaults(x_standards, y_measured)

   # Generate bootstrap samples
   params, subsamples = bootstrap_odr_fit(
       x=x_standards,
       y=y_measured,
       x_err=x_uncertainty,
       y_err=y_uncertainty,
       resample_draws=2000,
       fit_intercept=True,
       initial_guess=defaults["initial_guess"],
   )

   # Evaluate at different confidence levels
   conf_95 = evaluate_confidence(
       params,
       line_max=defaults["line_max"],
       line_interval=defaults["line_interval"],
       confidence_level=0.95,
   )
   conf_68 = evaluate_confidence(
       params,
       line_max=defaults["line_max"],
       line_interval=defaults["line_interval"],
       confidence_level=0.68,
   )

   # Overlay both bands in one plot
   fig, ax = plt.subplots(figsize=(10, 6))
   plot_regression(
       [conf_95, conf_68],
       datapoints=points,
       ax=ax,
       ecolor=["#bfdbfe", "#1d4ed8"],
       line_color="#0f766e",
       e_alpha=[0.35, 0.7],
   )

   print(f"95% CI width: {(conf_95['pos_error_bound'] - conf_95['neg_error_bound']).mean():.2f}")
   print(f"68% CI width: {(conf_68['pos_error_bound'] - conf_68['neg_error_bound']).mean():.2f}")

Data Quality Considerations
===========================

- **NaN Handling**: The package automatically removes rows with NaN values before fitting, so no explicit data cleaning is required in most workflows.

- **Outlier Detection**: Bootstrap resampling naturally downweights outliers through repeated sampling. For extreme outliers, consider pre-filtering your data.

- **Error Estimates**: Input uncertainties are crucial for proper ODR weighting. If unavailable, use relative percentages such as 5% of the measurement value.

Performance Tips
================

- **Reduce resample_draws** for quick exploratory analysis (e.g., 500 resamples)
- **Increase resample_draws** for publication results (e.g., 5000+ resamples)
- Use **larger line_interval** to reduce plot resolution and speed up confidence-interval evaluation
- **Pre-validate** input data for NaN and infinity values if performance is critical

See Also
========

- :doc:`api` for detailed function signatures and options
- :doc:`examples` for complete working scripts
- `GitHub Issues <https://github.com/whtowbin/odr_bootstrap_package/issues>`_ for questions or bugs
