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

The resulting calibration curve includes the fitted line and bootstrap confidence
bands:

.. figure:: _static/calibration_curve.png
   :alt: Calibration curve with 68% and 95% bootstrap confidence intervals
   :width: 100%

   Calibration curve with 68% and 95% bootstrap confidence bands.

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

The parameter distributions provide a direct view of the uncertainty in the fitted
slope and intercept:

.. figure:: _static/calibration_estimates.png
   :alt: Bootstrap distributions of the fitted slope and intercept
   :width: 100%

   Bootstrap distributions of the calibration slope and intercept.

Applying the Calibration to New Data
=====================================

After the calibration is fitted, :func:`~odr_bootstrap.apply_calibration`
applies that fitted model to new measurements and propagates the full bootstrap
uncertainty into confidence intervals on each estimate.

The complete runnable example lives in
``examples/calibration_application_example.py``.

Calibration axis convention
----------------------------

For a SIMS-style calibration the natural choice is to place the measured ion
count rate on the x-axis and the known concentration on the y-axis:

.. code-block:: text

    concentration (ppm) = slope × count rate (counts) + intercept

With this convention ``apply_calibration(variable="x")`` converts an unknown
count rate directly into a concentration estimate — no inversion required.

Setting up the calibration
--------------------------

.. code-block:: python

    import numpy as np
    from odr_bootstrap import odr_bootstrap, fit_defaults, apply_calibration

    # SIMS calibration standards
    # x = measured count rate from reference standards
    # y = known concentration of those standards
    x_counts      = np.array([62,   117,  223,   528,   1014,  2001])   # count rate
    y_conc        = np.array([0.5,  1.0,  2.0,   5.0,   10.0,  20.0])   # ppm
    x_uncertainty = np.array([15,   20,   25,    40,     60,    80])     # counting σ
    y_uncertainty = y_conc * 0.02                                         # 2 % of concentration

    defaults = fit_defaults(x_counts, y_conc, fit_intercept=True)

    confidence_data, best_fit_params, points, all_params, _ = odr_bootstrap(
        x=x_counts,
        y=y_conc,
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
    # Best-fit slope: ~0.00999 ppm / count
    # Best-fit intercept: ~-0.158 ppm

Converting unknown count rates to concentration
-----------------------------------------------

Pass the unknown count rates directly to
:func:`~odr_bootstrap.apply_calibration` with ``variable="x"``:

.. code-block:: python

    unknown_counts = np.array([150.0, 430.0, 850.0, 1600.0])   # measured counts
    results = apply_calibration(
        unknown_counts,
        all_params,
        variable="x",
        fit_intercept=True,
        confidence_levels=(0.68, 0.95),
    )
    print(results.to_string(float_format="{:.3f}".format, index=False))

Example output::

     input_value  best_fit  median  neg_ci_68  pos_ci_68  neg_ci_95  pos_ci_95
         150.000     1.340   1.337      1.289      1.359      1.232      1.376
         430.000     4.137   4.126      4.078      4.158      3.994      4.180
         850.000     8.333   8.328      8.241      8.368      8.039      8.397
        1600.000    15.825  15.838     15.642     15.912     15.230     15.941

The columns are:

- **input_value** — the measured count rate you supplied.
- **best_fit** — concentration predicted from the best-fit line.
- **median** — median of all bootstrap estimates for that count rate.
- **neg_ci_68 / pos_ci_68** — lower and upper bounds of the 68 % CI.
- **neg_ci_95 / pos_ci_95** — lower and upper bounds of the 95 % CI.

Rendering the results with Great Tables
----------------------------------------

The `great_tables <https://pypi.org/project/great_tables/>`_ package creates publication-ready HTML tables from
the DataFrames returned by the calibration helpers.  It is an optional
dependency (install with ``uv sync --extra examples``).

.. code-block:: python

    from great_tables import GT, md

    display = results.copy()
    display.insert(0, "Sample ID", [f"Unknown {i+1}" for i in range(len(display))])
    display = display.rename(columns={
        "input_value": "Count rate (counts)",
        "best_fit":    "Best-fit conc. (ppm)",
        "median":      "Median conc. (ppm)",
        "neg_ci_68":   "Lower 68 % CI (ppm)",
        "pos_ci_68":   "Upper 68 % CI (ppm)",
        "neg_ci_95":   "Lower 95 % CI (ppm)",
        "pos_ci_95":   "Upper 95 % CI (ppm)",
    })

    tbl = (
        GT(display, rowname_col="Sample ID")
        .tab_header(
            title="Unknown sample concentrations",
            subtitle="Count rate converted to concentration (ppm) using the bootstrap calibration",
        )
        .fmt_number(columns=["Count rate (counts)"], decimals=0)
        .fmt_number(
            columns=[
                "Best-fit conc. (ppm)", "Median conc. (ppm)",
                "Lower 68 % CI (ppm)", "Upper 68 % CI (ppm)",
                "Lower 95 % CI (ppm)", "Upper 95 % CI (ppm)",
            ],
            decimals=2,
        )
        .tab_spanner(
            label="68 % CI (ppm)",
            columns=["Lower 68 % CI (ppm)", "Upper 68 % CI (ppm)"],
        )
        .tab_spanner(
            label="95 % CI (ppm)",
            columns=["Lower 95 % CI (ppm)", "Upper 95 % CI (ppm)"],
        )
        .tab_source_note(source_note=md(
            "Calibration fit: **concentration (ppm) = slope × count rate + intercept**. "
            "Confidence intervals propagated from 2000 bootstrap resamples."
        ))
    )

    tbl.show()           # renders inline in Jupyter
    tbl.as_raw_html()    # returns HTML string

The example script saves the rendered table as a static HTML file:

.. raw:: html

   <iframe src="_static/calibration_results.html"
           style="width:100%;min-height:420px;border:0;margin:1rem 0">
   </iframe>

Handling Potential Outliers
===========================

A point that appears unusual is not necessarily a bad datapoint. Exclude a point
from the regression only when there is an independent reason to do so, such as a
known instrument failure, sample-handling error, or invalid measurement.

When a potential outlier cannot be excluded objectively, retain it in the
regression. The bootstrap results can then quantify how much the point affects
the fitted parameters and confidence bands. A useful sensitivity analysis is to
run the fit both with and without the point and compare:

- the best-fit slope and intercept,
- the widths of the confidence bands, and
- the bootstrap distributions of the parameters.

This approach makes the influence of the potential outlier explicit without
silently treating it as either valid or invalid.

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
