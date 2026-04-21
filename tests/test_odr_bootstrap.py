"""
Unit tests for ODR bootstrapping and calibration functions.
"""

import unittest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from odr_bootstrap import (
    ODR_Linear,
    ODR_Linear_Test,
    Bootstrap_fit,
    Eval_Conf,
    plot_regression,
    ODR_Bootstrap,
    gauss_agv_err,
    plot_datapoints,
    plot_Calibration_Estimates,
)


class TestODRLinear(unittest.TestCase):
    """Test ODR_Linear function."""

    def setUp(self):
        """Create synthetic test data."""
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        self.x_err = np.ones_like(self.x) * 0.1
        self.y_err = np.ones_like(self.y) * 0.5

    def test_odr_linear_with_intercept(self):
        """Test ODR fit with intercept."""
        Popt, Perr = ODR_Linear(
            self.x, self.y, self.x_err, self.y_err, intercept=True
        )
        self.assertEqual(len(Popt), 2)  # slope and intercept
        self.assertEqual(len(Perr), 2)
        self.assertTrue(np.all(Perr > 0))  # uncertainties are positive

    def test_odr_linear_no_intercept(self):
        """Test ODR fit through origin."""
        Popt, Perr = ODR_Linear(
            self.x, self.y, self.x_err, self.y_err, intercept=False
        )
        self.assertEqual(len(Popt), 1)  # slope only
        self.assertEqual(len(Perr), 1)

    def test_odr_linear_test_returns_three(self):
        """Test that ODR_Linear_Test returns full output object."""
        Popt, Perr, out = ODR_Linear_Test(
            self.x, self.y, self.x_err, self.y_err, intercept=True
        )
        self.assertEqual(len(Popt), 2)
        self.assertIsNotNone(out)  # ODR output object exists


class TestBootstrapFit(unittest.TestCase):
    """Test Bootstrap_fit function."""

    def setUp(self):
        """Create synthetic test data."""
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        self.x_err = np.ones_like(self.x) * 0.1
        self.y_err = np.ones_like(self.y) * 0.5

    def test_bootstrap_fit_returns_tuple(self):
        """Test Bootstrap_fit returns correct structure."""
        fit_params, subsamples = Bootstrap_fit(
            self.x, self.y, self.x_err, self.y_err, resample_draws=10, InterceptFit=True
        )
        self.assertIsInstance(fit_params, list)
        self.assertIsInstance(subsamples, list)
        self.assertEqual(len(fit_params), 11)  # 1 original + 10 resamples
        self.assertEqual(len(subsamples), 10)

    def test_bootstrap_fit_parameter_shapes(self):
        """Test Bootstrap_fit output parameter shapes."""
        fit_params, _ = Bootstrap_fit(
            self.x, self.y, self.x_err, self.y_err, resample_draws=5, InterceptFit=True
        )
        # All params should have 2 elements (slope, intercept)
        for param in fit_params:
            self.assertEqual(len(param), 2)

    def test_bootstrap_fit_no_intercept(self):
        """Test Bootstrap_fit through origin."""
        fit_params, _ = Bootstrap_fit(
            self.x, self.y, self.x_err, self.y_err, resample_draws=5, InterceptFit=False
        )
        # All params should have 1 element (slope only)
        for param in fit_params:
            self.assertEqual(len(param), 1)


class TestEvalConf(unittest.TestCase):
    """Test Eval_Conf function."""

    def setUp(self):
        """Create synthetic bootstrap parameters."""
        np.random.seed(42)
        # Simulate 100 bootstrap fits
        slopes = np.random.normal(2.5, 0.2, 100)
        intercepts = np.random.normal(10, 1, 100)
        self.fit_params = [np.array([s, i]) for s, i in zip(slopes, intercepts)]

    def test_eval_conf_returns_dataframe(self):
        """Test Eval_Conf output type."""
        result = Eval_Conf(self.fit_params, Confidence_Bound=0.95)
        self.assertIsInstance(result, pd.DataFrame)

    def test_eval_conf_dataframe_columns(self):
        """Test Eval_Conf contains required columns."""
        result = Eval_Conf(self.fit_params, Confidence_Bound=0.95)
        required_cols = [
            "best_fit",
            "neg_error_bound",
            "pos_error_bound",
            "percent_error_neg",
            "percent_error_pos",
        ]
        for col in required_cols:
            self.assertIn(col, result.columns)

    def test_eval_conf_with_single_param(self):
        """Test Eval_Conf with slope-only parameters."""
        slopes = np.random.normal(2.5, 0.2, 100)
        fit_params = [np.array([s]) for s in slopes]
        result = Eval_Conf(fit_params, Confidence_Bound=0.95)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("best_fit", result.columns)


class TestODRBootstrap(unittest.TestCase):
    """Test ODR_Bootstrap convenience function."""

    def setUp(self):
        """Create synthetic test data."""
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        self.x_err = np.ones_like(self.x) * 0.1
        self.y_err = np.ones_like(self.y) * 0.5

    def test_odr_bootstrap_returns_five_items(self):
        """Test ODR_Bootstrap output has 5 elements."""
        result = ODR_Bootstrap(
            self.x,
            self.y,
            self.x_err,
            self.y_err,
            resample_draws=10,
            LineMax=10,
        )
        self.assertEqual(len(result), 5)

    def test_odr_bootstrap_confidence_data_is_dataframe(self):
        """Test first return value is DataFrame."""
        confidence_data, _, _, _, _ = ODR_Bootstrap(
            self.x, self.y, self.x_err, self.y_err, resample_draws=10
        )
        self.assertIsInstance(confidence_data, pd.DataFrame)

    def test_odr_bootstrap_points_dataframe(self):
        """Test points DataFrame structure."""
        _, _, points, _, _ = ODR_Bootstrap(
            self.x, self.y, self.x_err, self.y_err, resample_draws=10
        )
        self.assertIsInstance(points, pd.DataFrame)
        required = {"x", "y", "xerr", "yerr"}
        self.assertTrue(required.issubset(set(points.columns)))


class TestGaussAvgErr(unittest.TestCase):
    """Test gauss_agv_err function."""

    def setUp(self):
        """Create synthetic concentration data."""
        np.random.seed(42)
        self.concentrations = np.array([100.0, 105.0, 98.0, 102.0, 101.0])
        self.errors = np.array([5.0, 6.0, 4.0, 5.5, 4.5])

    def test_gauss_agv_err_returns_tuple(self):
        """Test gauss_agv_err output structure."""
        dist, stats = gauss_agv_err(self.concentrations, self.errors)
        self.assertIsInstance(dist, dict)
        self.assertIsInstance(stats, dict)
        self.assertIn("x", dist)
        self.assertIn("y", dist)

    def test_gauss_agv_err_statistics_keys(self):
        """Test statistics dictionary contains required keys."""
        _, stats = gauss_agv_err(self.concentrations, self.errors)
        required_keys = [
            "mean",
            "mode",
            "mid_point",
            "one_sigma_bounds",
            "two_sigma_bounds",
            "CI_one_sigma",
            "CI_two_sigma",
            "n",
        ]
        for key in required_keys:
            self.assertIn(key, stats)

    def test_gauss_agv_err_n_matches_input(self):
        """Test sample count matches input length."""
        _, stats = gauss_agv_err(self.concentrations, self.errors)
        self.assertEqual(stats["n"], len(self.concentrations))


class TestPlottingFunctions(unittest.TestCase):
    """Test plotting functions return correct matplotlib objects."""

    def setUp(self):
        """Create test data and confidence data."""
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        self.x_err = np.ones_like(self.x) * 0.1
        self.y_err = np.ones_like(self.y) * 0.5

        # Generate confidence data
        slopes = np.random.normal(2.5, 0.1, 50)
        intercepts = np.random.normal(10, 0.5, 50)
        fit_params = [np.array([s, i]) for s, i in zip(slopes, intercepts)]
        self.confidence_df = Eval_Conf(fit_params, LineMax=6)

    def test_plot_regression_returns_axes(self):
        """Test plot_regression returns matplotlib Axes."""
        ax = plot_regression(self.confidence_df)
        self.assertTrue(isinstance(ax, plt.Axes))
        plt.close()

    def test_plot_regression_with_datapoints(self):
        """Test plot_regression with data points."""
        datapoints = pd.DataFrame(
            {"x": self.x, "y": self.y, "xerr": self.x_err, "yerr": self.y_err}
        )
        ax = plot_regression(self.confidence_df, datapoints=datapoints)
        self.assertTrue(isinstance(ax, plt.Axes))
        plt.close()

    def test_plot_datapoints_returns_axes(self):
        """Test plot_datapoints returns matplotlib Axes."""
        concentrations = np.array([100.0, 105.0, 98.0])
        errors = np.array([5.0, 6.0, 4.0])
        dist, stats = gauss_agv_err(concentrations, errors)
        ax = plot_datapoints(dist, stats)
        self.assertTrue(isinstance(ax, plt.Axes))
        plt.close()

    def test_plot_calibration_estimates_returns_figure(self):
        """Test plot_Calibration_Estimates returns matplotlib Figure."""
        fit_params = np.array([[100, 5], [105, 8], [98, 6]])
        fit_error = np.array([[5, 1], [6, 1.5], [4, 0.8]])
        fig = plot_Calibration_Estimates(fit_params, fit_error)
        self.assertTrue(isinstance(fig, plt.Figure))
        plt.close(fig)


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and edge cases."""

    def test_eval_conf_raises_on_too_many_params(self):
        """Test Eval_Conf raises error for invalid parameter count."""
        bad_params = [np.array([1.0, 2.0, 3.0])]  # 3 parameters
        with self.assertRaises(ValueError):
            Eval_Conf(bad_params)

    def test_bootstrap_handles_nan(self):
        """Test Bootstrap_fit drops NaN values."""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.5, 5.0, 7.5, 10.0, 12.5])
        x_err = np.ones_like(x) * 0.1
        y_err = np.ones_like(y) * 0.5

        fit_params, subsamples = Bootstrap_fit(
            x, y, x_err, y_err, resample_draws=5, InterceptFit=True
        )
        # Should complete without error
        self.assertIsInstance(fit_params, list)
        self.assertGreater(len(fit_params), 0)

    def test_odr_bootstrap_preserves_confidence(self):
        """Test ODR_Bootstrap respects Confidence_Bound parameter."""
        np.random.seed(42)
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        x_err = np.ones_like(x) * 0.1
        y_err = np.ones_like(y) * 0.5

        result_95 = ODR_Bootstrap(
            x, y, x_err, y_err, resample_draws=50, Confidence_Bound=0.95
        )
        result_68 = ODR_Bootstrap(
            x, y, x_err, y_err, resample_draws=50, Confidence_Bound=0.68
        )

        # 95% CI should generally be wider than 68% CI
        conf_95 = result_95[0]
        conf_68 = result_68[0]
        width_95 = (conf_95["pos_error_bound"] - conf_95["neg_error_bound"]).mean()
        width_68 = (conf_68["pos_error_bound"] - conf_68["neg_error_bound"]).mean()
        self.assertGreater(width_95, width_68 * 0.9)  # Allow some tolerance


if __name__ == "__main__":
    unittest.main()
