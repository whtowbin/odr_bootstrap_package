========
Examples
========

Run the included example script to generate four publication-quality figures from
synthetic calibration data:

.. code-block:: bash

   python examples/example.py

This produces:

- **calibration_curve.png** — best-fit line with 68% and 95% confidence bands
- **calibration_estimates.png** — bootstrap distributions of the fitted slope and intercept
- **calibration_curve_outlier.png** — same fit on a dataset that includes two outliers
- **calibration_estimates_outlier.png** — how the outliers broaden the parameter distributions

Example Output
==============

Clean Calibration Fit
---------------------

.. figure:: _static/calibration_curve.png
   :alt: Calibration curve with 68% and 95% bootstrap confidence intervals
   :width: 100%

   The fitted regression line with 68% (darker) and 95% (lighter) bootstrap confidence
   bands. The bands capture the combined effect of uncertainty in both x and y, so
   points with larger error bars contribute less to the fit.

Clean Parameter Distributions
------------------------------

.. figure:: _static/calibration_estimates.png
   :alt: Bootstrap distributions of the fitted slope and intercept
   :width: 100%

   The spread of slope and intercept estimates across 2000 bootstrap resamples.
   A narrow, symmetric peak indicates a well-constrained fit.

Outlier Sensitivity
-------------------

.. figure:: _static/calibration_curve_outlier.png
   :alt: Calibration curve with outlier data and dual confidence intervals
   :width: 100%

   The two additional points are treated as potential outliers and are intentionally
   retained in the regression. Because they cannot be excluded using an independent
   criterion, the comparison with the clean fit shows how much they shift the fitted
   line and increase the confidence envelope.

Outlier-Affected Parameter Distributions
-----------------------------------------

.. figure:: _static/calibration_estimates_outlier.png
   :alt: Bootstrap parameter distributions for the outlier-affected dataset
   :width: 100%

   The broader and potentially skewed distributions quantify the effect of retaining
   the potential outliers. This provides an uncertainty assessment rather than
   assuming that the points are either unquestionably valid or safe to remove.

Adapting for Your Data
======================

.. code-block:: python

   import numpy as np
   import matplotlib.pyplot as plt
   from odr_bootstrap import odr_bootstrap, fit_defaults, plot_regression

   x = np.array([...])      # known reference values
   y = np.array([...])      # measured values
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
   ax.set_xlabel("Reference Value")
   ax.set_ylabel("Measured Signal")
   plt.savefig("my_calibration.png")
   plt.show()

   slope, intercept = params
   print(f"y = {slope:.2f} * x + {intercept:.2f}")

Complete Example Script
=======================

Unknown Sample Results Table
============================

Run ``examples/calibration_application_example.py`` to see a complete
worked example converting measured ion count rates into concentration estimates.
The script uses fixed calibration standards so the output is reproducible.

.. code-block:: bash

   uv run --extra examples python examples/calibration_application_example.py

Calibration axis convention: **x = count rate, y = concentration (ppm)**.
This means ``apply_calibration(variable="x")`` converts a measured count rate
directly into a concentration — no inversion required.

Count rate → concentration results
------------------------------------

The rendered results table shows the best-fit concentration and 68 % / 95 %
bootstrap confidence intervals for four unknown samples:

.. raw:: html

   <iframe src="_static/calibration_results.html"
          style="width:100%;min-height:420px;border:0;margin:1rem 0">
   </iframe>

The full calibration application script:

.. literalinclude:: ../../examples/calibration_application_example.py
   :language: python
   :linenos:


.. literalinclude:: ../../examples/example.py
   :language: python
   :linenos:

Troubleshooting
===============
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

See Also
========

- :doc:`tutorial` for a detailed walkthrough
- :doc:`api` for full function reference
- `GitHub Issues <https://github.com/whtowbin/odr_bootstrap_package/issues>`_ for bugs or questions
