========
Examples
========

This page is a complete, runnable walkthrough of the ODR Bootstrap calibration
workflow. Every code sample below is pulled directly from
``examples/example.py`` via Sphinx's ``literalinclude`` directive, so it
always matches the actual, tested script — run the script yourself to
reproduce every figure and table on this page:

.. code-block:: bash

   uv run --extra examples python examples/example.py

This produces:

- **calibration_curve.png** — best-fit line with 68% and 95% confidence bands
- **calibration_estimates.png** — bootstrap distributions of the fitted slope and intercept
- **calibration_curve_outlier.png** — same fit on a dataset that retains two potential outliers
- **calibration_estimates_outlier.png** — how the outliers broaden the parameter distributions
- **calibration_results.html** — a Great Tables results table from applying the calibration

Basic Calibration Fit
======================

Fit a linear calibration curve with bootstrap confidence intervals. The
example uses a fixed set of synthetic SIMS-style standards — a measured ion
count rate (``x``) against a known concentration (``y``) — loaded from
``examples/data/synthetic_calibration_standards.csv``:

.. literalinclude:: ../../examples/example.py
   :language: python
   :start-after: # section:standards
   :end-before: # end-section:standards

That CSV is generated once by ``examples/Synthetic_Data_Generation.py``, which
draws standards from a seeded random generator and is checked into the repo
so ``example.py`` always fits the same data. This generator script is run
**manually only** — it is intentionally excluded from ``make regen-examples``,
``make docs``, and ``scripts/prepare-release.sh``, so that rebuilding the docs
or cutting a release never changes the underlying dataset. Regenerate it with:

.. code-block:: bash

   uv run python examples/Synthetic_Data_Generation.py

``fit_defaults`` derives the three parameters the fitting functions need so
you don't have to set them manually — an initial least-squares guess, and a
``line_max``/``line_interval`` pair sized to the data — and ``odr_bootstrap``
runs the bootstrap fit itself:

.. literalinclude:: ../../examples/example.py
   :language: python
   :start-after: # section:clean-fit
   :end-before: # end-section:clean-fit

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

``evaluate_confidence`` builds the confidence bands used for plotting at any
confidence level you choose — here 68% and 95% are computed side by side so
they can be overlaid on the same plot:

.. code-block:: python

   conf_68 = evaluate_confidence(all_params, line_max=line_max, line_interval=line_interval, confidence_level=0.68)
   conf_95 = evaluate_confidence(all_params, line_max=line_max, line_interval=line_interval, confidence_level=0.95)

Plotting the Regression
========================

.. literalinclude:: ../../examples/example.py
   :language: python
   :start-after: # section:plot-clean
   :end-before: # end-section:plot-clean

.. figure:: _static/calibration_curve.png
   :alt: Calibration curve with 68% and 95% bootstrap confidence intervals
   :width: 100%

   The fitted regression line with 68% (darker) and 95% (lighter) bootstrap confidence
   bands. The bands capture the combined effect of uncertainty in both x and y, so
   points with larger error bars contribute less to the fit.

Visualising Parameter Uncertainty
===================================

Use ``gaussian_aggregate`` and ``plot_density`` to see how stable the fitted
slope and intercept are across bootstrap resamples:

.. literalinclude:: ../../examples/example.py
   :language: python
   :start-after: # section:plot-clean-estimates
   :end-before: # end-section:plot-clean-estimates

.. figure:: _static/calibration_estimates.png
   :alt: Bootstrap distributions of the fitted slope and intercept
   :width: 100%

   The spread of slope and intercept estimates across 2000 bootstrap resamples.
   A narrow, symmetric peak indicates a well-constrained fit.

Handling Potential Outliers
============================

A point that appears unusual is not necessarily a bad datapoint. Exclude a
point from the regression only when there is an independent reason to do so,
such as a known instrument failure, sample-handling error, or invalid
measurement.

When a potential outlier cannot be excluded objectively, retain it in the
regression. The bootstrap results can then quantify how much the point
affects the fitted parameters and confidence bands. A useful sensitivity
analysis is to run the fit both with and without the point and compare:

- the best-fit slope and intercept,
- the widths of the confidence bands, and
- the bootstrap distributions of the parameters.

This approach makes the influence of the potential outlier explicit without
silently treating it as either valid or invalid. The example script does
exactly this: it retains two extra standards that fall well off the fitted
trend and refits:

.. literalinclude:: ../../examples/example.py
   :language: python
   :start-after: # section:outlier-fit
   :end-before: # end-section:outlier-fit

.. figure:: _static/calibration_curve_outlier.png
   :alt: Calibration curve with outlier data and dual confidence intervals
   :width: 100%

   The two additional points are treated as potential outliers and are intentionally
   retained in the regression. Because they cannot be excluded using an independent
   criterion, the comparison with the clean fit shows how much they shift the fitted
   line and increase the confidence envelope.

.. figure:: _static/calibration_estimates_outlier.png
   :alt: Bootstrap parameter distributions for the outlier-affected dataset
   :width: 100%

   The broader and potentially skewed distributions quantify the effect of retaining
   the potential outliers. This provides an uncertainty assessment rather than
   assuming that the points are either unquestionably valid or safe to remove.

Applying the Calibration to New Data
=====================================

After the calibration is fitted, :func:`~odr_bootstrap.apply_calibration`
(and its convenience wrapper :func:`~odr_bootstrap.apply_calibration_y`)
applies that fitted model to new measurements and propagates the full
bootstrap uncertainty into confidence intervals on each estimate.

Calibration axis convention
----------------------------

For this SIMS-style calibration, the measured ion count rate is on the
x-axis and the known concentration is on the y-axis:

.. code-block:: text

    concentration (ppm) = slope × count rate (counts) + intercept

``apply_calibration(variable="x")`` — the default — converts a measured
count rate directly into a concentration estimate, no inversion required.
The example script applies this to ``UNKNOWN_COUNTS`` and — because the two
potential outliers above cannot be excluded on independent grounds — it
deliberately applies the **outlier-affected** fit (``outlier_params``)
rather than the clean fit, so the reported uncertainty reflects their
influence:

.. literalinclude:: ../../examples/example.py
   :language: python
   :start-after: # section:apply-calibration
   :end-before: # end-section:apply-calibration

Example output::

    input_value  best_fit  median  neg_ci_68  pos_ci_68  neg_ci_95  pos_ci_95
        150.000    11.334  11.289     10.994     11.710     10.706     12.613
        400.000    12.494  12.558     12.155     13.070     11.863     13.831
        850.000    14.583  14.709     13.929     15.859     13.308     16.974
       1600.000    18.064  18.219     16.693     20.720     15.485     23.076

The columns are:

- **input_value** — the measured count rate you supplied.
- **best_fit** — concentration predicted from the best-fit line.
- **median** — median of all bootstrap estimates for that count rate.
- **neg_ci_68 / pos_ci_68** — lower and upper bounds of the 68 % CI.
- **neg_ci_95 / pos_ci_95** — lower and upper bounds of the 95 % CI.

.. note::

   :func:`~odr_bootstrap.apply_calibration` also accepts ``variable="y"``
   (or the :func:`~odr_bootstrap.apply_calibration_y` convenience wrapper) to
   go the other direction — given a known/measured concentration, estimate
   the corresponding count rate. In that case pass ``line_max``/
   ``line_interval`` sized to the **x** (count-rate) axis explicitly, rather
   than letting them default from the supplied concentration values, which
   live on a different scale.

Rendering the Results with Great Tables
-----------------------------------------

The `great_tables <https://pypi.org/project/great_tables/>`_ package creates
publication-ready HTML tables from the DataFrames returned by the
calibration helpers. It is an optional dependency (install with
``uv sync --extra examples``).

.. literalinclude:: ../../examples/example.py
   :language: python
   :start-after: # section:render-table
   :end-before: # end-section:render-table

The example script saves the rendered table as a static HTML file:

.. raw:: html

   <iframe src="_static/calibration_results.html"
           style="width:100%;min-height:420px;border:0;margin:1rem 0">
   </iframe>

Zero-Intercept Fits
=====================

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

Adapting for Your Data
========================

.. code-block:: python

   import numpy as np
   import matplotlib.pyplot as plt
   from odr_bootstrap import odr_bootstrap, fit_defaults, plot_regression

   x = np.array([...])      # measured signal or count rate
   y = np.array([...])      # known reference values
   x_err = np.array([...])  # uncertainties on x
   y_err = np.array([...])  # uncertainties on y

   defaults = fit_defaults(x, y)

   confidence_data, params, points, all_params, _ = odr_bootstrap(
       x=x, y=y, x_err=x_err, y_err=y_err,
       resample_draws=2000,
       fit_intercept=True,
       initial_guess=defaults["initial_guess"],
       line_max=defaults["line_max"],
       line_interval=defaults["line_interval"],
       confidence_level=0.95,
   )

   fig, ax = plt.subplots(figsize=(10, 6))
   plot_regression(confidence_data, datapoints=points, ax=ax)
   ax.set_xlabel("Count Rate")
   ax.set_ylabel("Concentration")
   plt.savefig("my_calibration.png")
   plt.show()

   slope, intercept = params
   print(f"y = {slope:.2f} * x + {intercept:.2f}")

Advanced: Multiple Confidence Levels
========================================

Overlay 68% and 95% confidence bands on the same plot using
``bootstrap_odr_fit`` directly:

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

Troubleshooting
================
**Poor fit quality**

- Verify your uncertainty estimates are realistic (a constant relative error such as
  5 % of each value is a reasonable starting point if you don't have measured errors).
- Call ``fit_defaults(x, y)`` and inspect the ``initial_guess`` to confirm it matches
  your expected slope and intercept.
- Check for outliers that may be dominating the fit.
- Do not remove a potential outlier solely because it disagrees with the fitted trend.
  If there is no independent evidence that it is a bad datapoint, retain it and compare
  the fit and bootstrap uncertainty with and without the point.

**Slow execution**

- Reduce ``resample_draws`` for exploratory work (500 is fine; use 2000–5000 for
  reported results).
- Increase ``line_interval`` to reduce the confidence-band grid resolution.

**NaN or Inf in results**

- Rows where x, y, x_err, or y_err is NaN are dropped automatically. Make sure enough
  valid points remain (at least 3 for an intercept fit, 2 for a zero-intercept fit).
- Check that all uncertainty values are positive.

**Confidence intervals blow up when evaluating the Y variable**

- When calling ``apply_calibration(variable="y")`` / ``apply_calibration_y``, pass
  ``line_max``/``line_interval`` sized to the **x** axis explicitly. Left to default,
  they are inferred from the supplied y-values, which live on a different scale and
  produce a confidence-surface grid that doesn't cover the real x range — leading to
  wildly extrapolated bounds.

See Also
========

- :doc:`api` for full function reference
- `GitHub Issues <https://github.com/whtowbin/odr_bootstrap_package/issues>`_ for bugs or questions
