# Examples

## Complete Working Examples

The package includes a complete runnable example:

```bash
cd examples
python example.py
```

This generates:

- **calibration_curve.png** - Best-fit line with both 68% and 95% confidence bands
- **calibration_curve_outlier.png** - Synthetic outlier example with a larger anomalous point
- **calibration_estimates.png** - Bootstrap parameter distributions

## Example Output

The example writes three publication-quality figures from synthetic calibration datasets. Together they show the fitted calibration relationship, the effect of a larger outlier on the uncertainty bands, and the distribution of the fitted slope and intercept estimates.

The first plot shows the best-fit line with both the 68% and 95% bootstrap confidence bands in one figure, while the second demonstrates larger outliers and how they broaden the uncertainty envelope in a single plot. The third summarizes the distribution of the slope and intercept estimates across many resampled fits.

### Calibration Fit

![Calibration curve with 68% and 95% bootstrap confidence intervals](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_curve.png)

The fitted regression line follows the expected linear trend while the narrower 68% band and broader 95% band capture the uncertainty estimated by bootstrap resampling.

### Outlier Sensitivity

![Synthetic calibration curve with larger outliers and dual confidence intervals](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_curve_outlier.png)

Larger outliers widen the uncertainty envelope and shift the fitted trend, which helps illustrate the value of robust calibration checks and careful outlier review.

### Parameter Uncertainty

![Bootstrap calibration slope and intercept distributions](https://raw.githubusercontent.com/whtowbin/odr_bootstrap_package/main/calibration_estimates.png)

The distribution of slope and intercept estimates provides a compact view of parameter uncertainty, which is especially useful for scientific reporting.

## What to look for in these figures

- The regression fit should align closely with the measured calibration points.
- The 68% band should be narrower than the 95% band, reflecting the larger confidence range at the 95% level.
- The outlier example should show a broader uncertainty band and a larger spread in the fitted parameters.
- The parameter histograms should be centered near the best-fit slope and intercept values.
- Larger resample counts usually produce smoother, more stable distributions.

The console output is structured as follows:

```text
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

[3/5] Plotting regression with 68% and 95% confidence intervals...
   ✓ Saved: calibration_curve.png

[4/5] Plotting outlier sensitivity example...
   ✓ Saved: calibration_curve_outlier.png

[5/5] Plotting calibration estimate distributions...
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
```

## Source Code

The example demonstrates:

1. Creating synthetic data with known true values and random noise.
2. Running ODR bootstrap with proper error propagation.
3. Plotting results with publication-quality figures.
4. Extracting statistics from bootstrap distributions.

See the example source here: https://github.com/whtowbin/odr_bootstrap_package/blob/main/examples/example.py

## Adapting for Your Data

To use ODR Bootstrap with your own data:

1. Prepare your data.

   ```python
   import numpy as np
   from odr_bootstrap import ODR_Bootstrap, plot_regression

   x_standards = np.array([...])
   y_measured = np.array([...])
   x_uncertainty = np.array([...])
   y_uncertainty = np.array([...])
   ```

2. Run the fit.

   ```python
   confidence_data, params, points, all_params, _ = ODR_Bootstrap(
       x=x_standards,
       y=y_measured,
       x_err=x_uncertainty,
       y_err=y_uncertainty,
       resample_draws=5000,
       InterceptFit=True,
       Confidence_Bound=0.95,
   )
   ```

3. Visualize and analyze.

   ```python
   import matplotlib.pyplot as plt

   fig, ax = plt.subplots(figsize=(10, 6))
   plot_regression(confidence_data, datapoints=points, ax=ax)
   ax.set_xlabel("Concentration")
   ax.set_ylabel("Measured Signal")
   plt.savefig("my_calibration.png")
   plt.show()

   slope, intercept = params
   print(f"y = {slope:.2f}*x + {intercept:.2f}")
   ```

## Troubleshooting

### Problem: Poor fit quality

- Check for outliers in your data.
- Verify uncertainty estimates are realistic.
- Try different InitialGuess values.
- Increase resample_draws for better bootstrap estimates.

### Problem: Slow execution

- Decrease resample_draws for testing.
- Use smaller LineInterval for plotting.
- Consider reducing data size or excluding low-quality measurements.

### Problem: NaN or Inf in results

- Check input data for NaN or Inf values.
- Verify uncertainty values are positive.
- Ensure you have at least 3 data points for intercept fit, 2 for zero-intercept.

## More Help

- [Tutorial](tutorial.rst)
- [API Reference](api.rst)
- [GitHub Issues](https://github.com/whtowbin/odr_bootstrap_package/issues)
