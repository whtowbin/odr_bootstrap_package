========
Examples
========

Complete Working Examples
==========================

The package includes a complete runnable example:

.. code-block:: bash

   cd examples
   python example.py

This generates:

- **calibration_curve.png** - Best-fit line with 95% confidence band
- **calibration_estimates.png** - Bootstrap parameter distributions

Example Output
==============

When you run ``example.py``, you'll see:

.. code-block:: text

   ======================================================================
   ODR Bootstrap Calibration Example
   ======================================================================

   [1/4] Creating synthetic calibration data...
      Standards: [0.1  0.5  1.   2.   5.  10. ]
      Measurements: [  32.  100.  315.  643. 1335. 2750.]
      X uncertainties: [0.01 0.05  0.1  0.2  0.5  1. ]
      Y uncertainties: [ 20  30  50  60 100 150]

   [2/4] Running ODR Bootstrap (N=2000 resamples)...
      Best fit slope: 125.43
      Best fit intercept: 14.28
      Bootstrap resamples computed: 2000
      Data points after NaN removal: 6

   [3/4] Plotting regression with confidence intervals...
      ✓ Saved: calibration_curve.png

   [4/4] Plotting calibration estimate distributions...
      ✓ Saved: calibration_estimates.png

   ======================================================================
   SUMMARY
   ======================================================================

   Fit Parameters (from full dataset):
     Slope:          125.43
     Intercept:       14.28

   Bootstrap Statistics (N=2000):
     Slope mean:     125.43 ± 12.34
     Intercept mean:  14.28 ± 8.56

Source Code
===========

The example demonstrates:

1. **Creating synthetic data** with known true values and random noise
2. **Running ODR bootstrap** with proper error propagation
3. **Plotting results** with publication-quality figures
4. **Extracting statistics** from bootstrap distributions

See ``examples/example.py`` in the source repository or browse online:
```
https://github.com/whtowbin/odr-bootstrap/blob/main/examples/example.py
```

Adapting for Your Data
======================

To use ODR Bootstrap with your own data:

1. **Prepare your data**

   .. code-block:: python

      import numpy as np
      from odr_bootstrap import ODR_Bootstrap, plot_regression

      # Load your calibration standards and measurements
      x_standards = np.array([...])      # Known concentrations
      y_measured = np.array([...])       # Measured values
      x_uncertainty = np.array([...])    # Errors in x
      y_uncertainty = np.array([...])    # Errors in y

2. **Run the fit**

   .. code-block:: python

      confidence_data, params, points, all_params, _ = ODR_Bootstrap(
          x=x_standards,
          y=y_measured,
          x_err=x_uncertainty,
          y_err=y_uncertainty,
          resample_draws=5000,  # More resamples for better accuracy
          InterceptFit=True,    # or False for zero-intercept
          Confidence_Bound=0.95,
      )

3. **Visualize and analyze**

   .. code-block:: python

      import matplotlib.pyplot as plt

      fig, ax = plt.subplots(figsize=(10, 6))
      plot_regression(confidence_data, datapoints=points, ax=ax)
      ax.set_xlabel('Concentration')
      ax.set_ylabel('Measured Signal')
      plt.savefig('my_calibration.png')
      plt.show()

      # Extract results
      slope, intercept = params
      print(f"y = {slope:.2f}*x + {intercept:.2f}")

Troubleshooting
===============

**Problem: Poor fit quality**

- Check for outliers in your data
- Verify uncertainty estimates are realistic
- Try different InitialGuess values
- Increase resample_draws for better bootstrap estimates

**Problem: Slow execution**

- Decrease resample_draws for testing
- Use smaller LineInterval for plotting
- Consider reducing data size or excluding low-quality measurements

**Problem: NaN or Inf in results**

- Check input data for NaN or Inf values
- Verify uncertainty values are positive
- Ensure you have at least 3 data points for intercept fit, 2 for zero-intercept

More Help
=========

- :doc:`tutorial` for detailed explanations
- :doc:`api` for function reference
- `GitHub Issues <https://github.com/whtowbin/odr-bootstrap/issues>`_ for bugs or questions
