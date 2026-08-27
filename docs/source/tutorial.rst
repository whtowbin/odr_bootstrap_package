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
   from odr_bootstrap import ODR_Bootstrap, plot_regression

   # Define calibration standards (known concentrations)
   x_standards = np.array([0.1, 0.5, 1.0, 2.0, 5.0, 10.0])

   # Simulated measurements (ion intensity in counts)
   # True relationship: y = 125*x + 15
   y_measured = 125 * x_standards + 15 + np.random.normal(0, 40, len(x_standards))

   # Measurement uncertainties
   x_uncertainty = np.array([0.01, 0.05, 0.1, 0.2, 0.5, 1.0])
   y_uncertainty = np.array([20, 30, 50, 60, 100, 150])

   # Estimate a reasonable starting point from a simple least-squares fit
   ls_slope, ls_intercept = np.polyfit(x_standards, y_measured, 1)
   initial_guess = [ls_slope, ls_intercept]

   # Run bootstrap with 2000 resamples
   confidence_data, best_fit_params, points, all_params, subsamples = ODR_Bootstrap(
       x=x_standards,
       y=y_measured,
       x_err=x_uncertainty,
       y_err=y_uncertainty,
       resample_draws=2000,
       InterceptFit=True,
       InitialGuess=initial_guess,
       Confidence_Bound=0.95,
       LineMax=11,
       LineInterval=0.5,
   )

   # Extract results
   slope, intercept = best_fit_params
   print(f"Fitted slope: {slope:.2f}")
   print(f"Fitted intercept: {intercept:.2f}")

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

The ``ODR_Bootstrap`` function returns a 5-tuple:

.. code-block:: python

   confidence_data, best_fit_params, points, all_params, subsamples = ODR_Bootstrap(...)

- ``confidence_data`` (``pandas.DataFrame``): Confidence interval bounds indexed by x-values. It contains columns such as:

  - ``best_fit``: fitted values at each x
  - ``neg_error_bound``: lower confidence bound
  - ``pos_error_bound``: upper confidence bound
  - ``percent_error_neg``: negative percent error
  - ``percent_error_pos``: positive percent error

- ``best_fit_params`` (``numpy.ndarray``): Best-fit parameters [slope, intercept] from the full dataset.

- ``points`` (``pandas.DataFrame``): Cleaned input data with columns ``x``, ``y``, ``xerr``, and ``yerr`` after NaN rows are removed.

- ``all_params`` (list of ``numpy.ndarray``): Bootstrap parameter estimates. The first element is ``best_fit_params`` and the remaining elements are bootstrap resamples.

- ``subsamples`` (list of ``pandas.DataFrame``): DataFrames used for each bootstrap resample.

Analyzing Bootstrap Distributions
==================================

The package uses the Gaussian aggregate helper, :func:`odr_bootstrap.gauss_agv_err`, to summarize the bootstrap fit distribution for each parameter. This directly aggregates the actual bootstrap fits into a smooth approximate distribution, which makes the parameter uncertainty easier to inspect than a hand-built synthetic sample.

Extract and analyze the parameter distributions:

.. code-block:: python

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

   # Aggregate the bootstrap fit distributions directly
   from odr_bootstrap import gauss_agv_err, plot_datapoints

   slope_dist, slope_stats = gauss_agv_err(
       all_slopes,
       np.full_like(all_slopes, slope_std),
   )
   intercept_dist, intercept_stats = gauss_agv_err(
       all_intercepts,
       np.full_like(all_intercepts, intercept_std),
   )

   fig, axes = plt.subplots(1, 2, figsize=(12, 5))
   plot_datapoints(slope_dist, slope_stats, ax=axes[0])
   plot_datapoints(intercept_dist, intercept_stats, ax=axes[1])
   axes[0].set_title("Slope Distribution")
   axes[1].set_title("Intercept Distribution")
   fig.tight_layout()
   plt.show()

For the same comparison with a strong outlier, repeat the same aggregation on the outlier-affected bootstrap fits:

.. code-block:: python

   outlier_params_array = np.asarray(outlier_params, dtype=float)
   outlier_slopes = outlier_params_array[:, 0]
   outlier_intercepts = outlier_params_array[:, 1]
   outlier_slope_dist, outlier_slope_stats = gauss_agv_err(
       outlier_slopes,
       np.full_like(outlier_slopes, outlier_slopes.std()),
   )
   outlier_intercept_dist, outlier_intercept_stats = gauss_agv_err(
       outlier_intercepts,
       np.full_like(outlier_intercepts, outlier_intercepts.std()),
   )

   fig, axes = plt.subplots(1, 2, figsize=(12, 5))
   plot_datapoints(outlier_slope_dist, outlier_slope_stats, ax=axes[0])
   plot_datapoints(outlier_intercept_dist, outlier_intercept_stats, ax=axes[1])
   axes[0].set_title("Outlier-Affected Slope Distribution")
   axes[1].set_title("Outlier-Affected Intercept Distribution")
   fig.tight_layout()
   plt.show()

Zero-Intercept Fits
===================

For fitting through the origin (y = slope * x):

.. code-block:: python

   confidence_data, best_fit_params, points, all_params, subsamples = ODR_Bootstrap(
       x=x_standards,
       y=y_measured,
       x_err=x_uncertainty,
       y_err=y_uncertainty,
       resample_draws=2000,
       InterceptFit=False,      # Force slope only
       InitialGuess=[125],        # Just slope, no intercept
       Confidence_Bound=0.95,
       LineMax=11,
   )

   slope = best_fit_params[0]
   print(f"Slope (through origin): {slope:.2f}")

Advanced: Custom Confidence Levels
==================================

Compute multiple confidence intervals on the same fit:

.. code-block:: python

   from odr_bootstrap import Bootstrap_fit, Eval_Conf

   # Generate bootstrap samples
   ls_slope, ls_intercept = np.polyfit(x_standards, y_measured, 1)
   initial_guess = [ls_slope, ls_intercept]

   params, subsamples = Bootstrap_fit(
       x=x_standards,
       y=y_measured,
       x_err=x_uncertainty,
       y_err=y_uncertainty,
       resample_draws=2000,
       InterceptFit=True,
       InitialGuess=initial_guess,
   )

   # Evaluate at different confidence levels
   conf_95 = Eval_Conf(params, Confidence_Bound=0.95, LineMax=11)
   conf_68 = Eval_Conf(params, Confidence_Bound=0.68, LineMax=11)

   # Compare bounds
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
- Use **LineInterval > 1** to reduce plot resolution and speed up plotting
- **Pre-validate** input data for NaN and infinity values if performance is critical

See Also
========

- :doc:`api` for detailed function signatures and options
- :doc:`examples` for complete working scripts
- `GitHub Issues <https://github.com/whtowbin/odr_bootstrap_package/issues>`_ for questions or bugs
