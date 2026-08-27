========
Tutorial
========

This tutorial walks through a complete calibration workflow using ODR Bootstrap.

Basic Calibration Fit
=====================

Fit a linear calibration curve with bootstrap confidence intervals:

.. code-block:: python

   import numpy as np
   import matplotlib.pyplot as plt
   from odr_bootstrap import odr_bootstrap, fit_defaults, plot_regression

   # Calibration standards: known concentrations and measured signal
   x_standards = np.array([0.1, 0.5, 1.0, 2.0, 5.0, 10.0])
   y_measured   = np.array([28, 78, 143, 265, 637, 1282])

   # Measurement uncertainties
   x_uncertainty = np.array([0.01, 0.05, 0.1, 0.2, 0.5, 1.0])
   y_uncertainty = np.array([20, 30, 50, 60, 100, 150])

   # Derive starting parameters from the data
   defaults = fit_defaults(x_standards, y_measured, fit_intercept=True)

   # Run bootstrap fitting with 2000 resamples
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

   slope, intercept = best_fit_params
   print(f"Fitted slope: {slope:.2f}")
   print(f"Fitted intercept: {intercept:.2f}")

Using fit_defaults
==================

``fit_defaults`` derives the three parameters that the fitting functions need so
you don't have to set them manually:

.. code-block:: python

   from odr_bootstrap import fit_defaults

   defaults = fit_defaults(x_standards, y_measured, fit_intercept=True)
   # defaults["initial_guess"]  → [slope, intercept] from a least-squares pre-fit
   # defaults["line_max"]       → max(x) * 1.1  (extends 10 % past the last standard)
   # defaults["line_interval"]  → line_max / 1000

You can pass these values directly or override any of them:

.. code-block:: python

   # Pass defaults explicitly
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

.. code-block:: python

   fig, ax = plt.subplots(figsize=(10, 6))

   plot_regression(
       confidence_data,
       datapoints=points,
       ax=ax,
       ecolor='lightblue',
       line_color='darkblue',
       e_alpha=0.4,
       linewidth=2.5,
   )

   ax.set_xlabel('Concentration (ppm)', fontsize=12)
   ax.set_ylabel('Ion Intensity (counts)', fontsize=12)
   ax.set_title('Calibration Curve with 95% Bootstrap CI', fontsize=14)
   ax.grid(True, alpha=0.3)

   fig.tight_layout()
   fig.savefig('calibration_curve.png', dpi=150, bbox_inches='tight')
   plt.show()

Understanding the Return Values
================================

``odr_bootstrap`` returns a 5-tuple:

.. code-block:: python

   confidence_data, best_fit_params, points, all_params, subsamples = odr_bootstrap(...)

- ``confidence_data`` (``pandas.DataFrame``): Confidence bounds indexed by x-value. Columns:

  - ``best_fit``: fitted y at each x
  - ``neg_error_bound`` / ``pos_error_bound``: lower and upper confidence bounds
  - ``percent_error_neg`` / ``percent_error_pos``: bounds expressed as percent error

- ``best_fit_params`` (``numpy.ndarray``): Best-fit ``[slope, intercept]`` from the full dataset.

- ``points`` (``pandas.DataFrame``): Input data after NaN removal, with columns ``x``, ``y``, ``xerr``, ``yerr``.

- ``all_params`` (list of ``numpy.ndarray``): All bootstrap parameter estimates. The first entry is ``best_fit_params``; the rest are resamples.

- ``subsamples`` (list of ``pandas.DataFrame``): The data subsets used for each bootstrap resample.

Visualising Parameter Uncertainty
===================================

Use ``gaussian_aggregate`` and ``plot_density`` to see how stable your fitted
slope and intercept are across bootstrap resamples:

.. code-block:: python

   from odr_bootstrap import gaussian_aggregate, plot_density
   import numpy as np

   all_params_array = np.asarray(all_params, dtype=float)
   slopes     = all_params_array[:, 0]
   intercepts = all_params_array[:, 1]

   slope_dist,     slope_stats     = gaussian_aggregate(slopes,     np.full_like(slopes,     slopes.std()))
   intercept_dist, intercept_stats = gaussian_aggregate(intercepts, np.full_like(intercepts, intercepts.std()))

   print(f"Slope:     {slopes.mean():.2f} ± {slopes.std():.2f}")
   print(f"Intercept: {intercepts.mean():.2f} ± {intercepts.std():.2f}")

   fig, axes = plt.subplots(1, 2, figsize=(12, 5))
   plot_density(slope_dist,     slope_stats,     ax=axes[0])
   plot_density(intercept_dist, intercept_stats, ax=axes[1])
   axes[0].set_title("Slope Distribution")
   axes[1].set_title("Intercept Distribution")
   fig.tight_layout()
   plt.show()

Zero-Intercept Fits
===================

To fit a line through the origin (y = slope × x), set ``fit_intercept=False``:

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

   print(f"Slope through origin: {best_fit_params[0]:.2f}")

Advanced: Multiple Confidence Levels
======================================

Overlay 68% and 95% confidence bands on the same plot:

.. code-block:: python

   from odr_bootstrap import bootstrap_odr_fit, evaluate_confidence, fit_defaults

   defaults = fit_defaults(x_standards, y_measured)

   params, subsamples = bootstrap_odr_fit(
       x=x_standards,
       y=y_measured,
       x_err=x_uncertainty,
       y_err=y_uncertainty,
       resample_draws=2000,
       fit_intercept=True,
       initial_guess=defaults["initial_guess"],
   )

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

   fig, ax = plt.subplots(figsize=(10, 6))
   plot_regression(
       [conf_95, conf_68],
       datapoints=points,
       ax=ax,
       ecolor=["#bfdbfe", "#1d4ed8"],
       line_color="#0f766e",
       e_alpha=[0.35, 0.7],
   )

   print(f"95% CI width at midpoint: {(conf_95['pos_error_bound'] - conf_95['neg_error_bound']).mean():.2f}")
   print(f"68% CI width at midpoint: {(conf_68['pos_error_bound'] - conf_68['neg_error_bound']).mean():.2f}")

Tips
====

- **Uncertainty estimates matter.** ODR weights each point by its reported uncertainty.
  If you don't have reliable error estimates, use a constant relative uncertainty such
  as 5 % of each measurement value as a starting point.

- **Choosing resample_draws.** 500 resamples is fine for exploratory work; use 2000–5000
  for results you intend to report.

- **NaN handling.** Any row where x, y, x_err, or y_err is NaN is dropped automatically
  before fitting.

See Also
========

- :doc:`api` for detailed function signatures and options
- :doc:`examples` for complete working scripts
- `GitHub Issues <https://github.com/whtowbin/odr_bootstrap_package/issues>`_ for questions or bugs
