"""
Unit tests for ODR bootstrapping and calibration functions.
"""

import unittest

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from odr_bootstrap import (
    bootstrap_odr_fit,
    evaluate_confidence,
    fit_defaults,
    fit_odr_linear,
    fit_odr_linear_debug,
    gaussian_aggregate,
    odr_bootstrap,
    plot_calibration_estimates,
    plot_density,
    plot_regression,
)


class TestFitDefaults(unittest.TestCase):
    """Test fit_defaults helper function."""

    def setUp(self):
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)

    def test_returns_dict_with_required_keys(self):
        result = fit_defaults(self.x, self.y)
        self.assertIn("initial_guess", result)
        self.assertIn("line_max", result)
        self.assertIn("line_interval", result)

    def test_intercept_guess_has_two_elements(self):
        result = fit_defaults(self.x, self.y, fit_intercept=True)
        self.assertEqual(len(result["initial_guess"]), 2)

    def test_no_intercept_guess_has_one_element(self):
        result = fit_defaults(self.x, self.y, fit_intercept=False)
        self.assertEqual(len(result["initial_guess"]), 1)

    def test_line_max_is_above_data(self):
        result = fit_defaults(self.x, self.y)
        self.assertGreater(result["line_max"], float(np.max(self.x)))

    def test_line_interval_is_positive(self):
        result = fit_defaults(self.x, self.y)
        self.assertGreater(result["line_interval"], 0)

    def test_raises_on_insufficient_data(self):
        with self.assertRaises(ValueError):
            fit_defaults([1.0], [2.0])


class TestFitODRLinear(unittest.TestCase):
    """Test fit_odr_linear function."""

    def setUp(self):
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        self.x_err = np.ones_like(self.x) * 0.1
        self.y_err = np.ones_like(self.y) * 0.5

    def test_fit_with_intercept(self):
        params, param_errors = fit_odr_linear(
            self.x, self.y, self.x_err, self.y_err, fit_intercept=True
        )
        self.assertEqual(len(params), 2)
        self.assertEqual(len(param_errors), 2)
        self.assertTrue(np.all(param_errors > 0))

    def test_fit_no_intercept(self):
        params, param_errors = fit_odr_linear(
            self.x, self.y, self.x_err, self.y_err, fit_intercept=False
        )
        self.assertEqual(len(params), 1)
        self.assertEqual(len(param_errors), 1)

    def test_auto_initial_guess(self):
        """initial_guess=None should succeed via fit_defaults."""
        params, param_errors = fit_odr_linear(
            self.x, self.y, self.x_err, self.y_err, fit_intercept=True,
            initial_guess=None,
        )
        self.assertEqual(len(params), 2)

    def test_explicit_initial_guess(self):
        params, _ = fit_odr_linear(
            self.x, self.y, self.x_err, self.y_err,
            fit_intercept=True, initial_guess=[2.5, 10.0],
        )
        self.assertEqual(len(params), 2)


class TestFitODRLinearDebug(unittest.TestCase):
    """Test fit_odr_linear_debug function."""

    def setUp(self):
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        self.x_err = np.ones_like(self.x) * 0.1
        self.y_err = np.ones_like(self.y) * 0.5

    def test_returns_three_values(self):
        params, param_errors, out = fit_odr_linear_debug(
            self.x, self.y, self.x_err, self.y_err, fit_intercept=True
        )
        self.assertEqual(len(params), 2)
        self.assertIsNotNone(out)


class TestBootstrapODRFit(unittest.TestCase):
    """Test bootstrap_odr_fit function."""

    def setUp(self):
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        self.x_err = np.ones_like(self.x) * 0.1
        self.y_err = np.ones_like(self.y) * 0.5

    def test_returns_tuple(self):
        fit_params, subsamples = bootstrap_odr_fit(
            self.x, self.y, self.x_err, self.y_err,
            resample_draws=10, fit_intercept=True,
        )
        self.assertIsInstance(fit_params, list)
        self.assertIsInstance(subsamples, list)
        self.assertEqual(len(fit_params), 11)  # 1 original + 10 resamples
        self.assertEqual(len(subsamples), 10)

    def test_parameter_shapes_with_intercept(self):
        fit_params, _ = bootstrap_odr_fit(
            self.x, self.y, self.x_err, self.y_err,
            resample_draws=5, fit_intercept=True,
        )
        for param in fit_params:
            self.assertEqual(len(param), 2)

    def test_parameter_shapes_no_intercept(self):
        fit_params, _ = bootstrap_odr_fit(
            self.x, self.y, self.x_err, self.y_err,
            resample_draws=5, fit_intercept=False,
        )
        for param in fit_params:
            self.assertEqual(len(param), 1)


class TestEvaluateConfidence(unittest.TestCase):
    """Test evaluate_confidence function."""

    def setUp(self):
        np.random.seed(42)
        slopes = np.random.normal(2.5, 0.2, 100)
        intercepts = np.random.normal(10, 1, 100)
        self.fit_params = [np.array([s, i]) for s, i in zip(slopes, intercepts)]

    def test_returns_dataframe(self):
        result = evaluate_confidence(
            self.fit_params, line_max=6.0, line_interval=0.01
        )
        self.assertIsInstance(result, pd.DataFrame)

    def test_dataframe_columns(self):
        result = evaluate_confidence(
            self.fit_params, line_max=6.0, line_interval=0.01
        )
        required_cols = [
            "best_fit", "neg_error_bound", "pos_error_bound",
            "percent_error_neg", "percent_error_pos",
        ]
        for col in required_cols:
            self.assertIn(col, result.columns)

    def test_slope_only_parameters(self):
        slopes = np.random.normal(2.5, 0.2, 100)
        fit_params = [np.array([s]) for s in slopes]
        result = evaluate_confidence(fit_params, line_max=6.0, line_interval=0.01)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("best_fit", result.columns)

    def test_custom_line_spacing_and_max(self):
        conf = evaluate_confidence(self.fit_params, line_max=10.0, line_interval=0.25)
        self.assertGreater(len(conf), 30)
        self.assertAlmostEqual(conf.index[0], 0.0)
        self.assertAlmostEqual(conf.index[-1], 10.0)

    def test_raises_on_too_many_params(self):
        bad_params = [np.array([1.0, 2.0, 3.0])]
        with self.assertRaises(ValueError):
            evaluate_confidence(bad_params, line_max=6.0, line_interval=0.01)


class TestODRBootstrap(unittest.TestCase):
    """Test odr_bootstrap convenience function."""

    def setUp(self):
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        self.x_err = np.ones_like(self.x) * 0.1
        self.y_err = np.ones_like(self.y) * 0.5

    def test_returns_five_items(self):
        result = odr_bootstrap(
            self.x, self.y, self.x_err, self.y_err, resample_draws=10
        )
        self.assertEqual(len(result), 5)

    def test_confidence_data_is_dataframe(self):
        confidence_data, _, _, _, _ = odr_bootstrap(
            self.x, self.y, self.x_err, self.y_err, resample_draws=10
        )
        self.assertIsInstance(confidence_data, pd.DataFrame)

    def test_points_dataframe_structure(self):
        _, _, points, _, _ = odr_bootstrap(
            self.x, self.y, self.x_err, self.y_err, resample_draws=10
        )
        self.assertIsInstance(points, pd.DataFrame)
        required = {"x", "y", "xerr", "yerr"}
        self.assertTrue(required.issubset(set(points.columns)))

    def test_auto_derived_line_params(self):
        """line_max/line_interval=None should auto-derive from data."""
        confidence_data, _, _, _, _ = odr_bootstrap(
            self.x, self.y, self.x_err, self.y_err,
            resample_draws=10, line_max=None, line_interval=None,
        )
        # line_max should be ~ max(x) * 1.1 = 5.5, index should go there
        self.assertGreaterEqual(float(confidence_data.index[-1]), float(np.max(self.x)))

    def test_respects_confidence_level(self):
        np.random.seed(42)
        result_95 = odr_bootstrap(
            self.x, self.y, self.x_err, self.y_err,
            resample_draws=50, confidence_level=0.95,
        )
        result_68 = odr_bootstrap(
            self.x, self.y, self.x_err, self.y_err,
            resample_draws=50, confidence_level=0.68,
        )
        conf_95 = result_95[0]
        conf_68 = result_68[0]
        width_95 = (conf_95["pos_error_bound"] - conf_95["neg_error_bound"]).mean()
        width_68 = (conf_68["pos_error_bound"] - conf_68["neg_error_bound"]).mean()
        self.assertGreater(width_95, width_68 * 0.9)


class TestGaussianAggregate(unittest.TestCase):
    """Test gaussian_aggregate function."""

    def setUp(self):
        np.random.seed(42)
        self.concentrations = np.array([100.0, 105.0, 98.0, 102.0, 101.0])
        self.errors = np.array([5.0, 6.0, 4.0, 5.5, 4.5])

    def test_returns_tuple_of_dicts(self):
        dist, stats_dict = gaussian_aggregate(self.concentrations, self.errors)
        self.assertIsInstance(dist, dict)
        self.assertIsInstance(stats_dict, dict)
        self.assertIn("x", dist)
        self.assertIn("y", dist)

    def test_statistics_keys(self):
        _, stats_dict = gaussian_aggregate(self.concentrations, self.errors)
        required_keys = [
            "mean", "mode", "mid_point",
            "one_sigma_bounds", "two_sigma_bounds",
            "CI_one_sigma", "CI_two_sigma", "n",
        ]
        for key in required_keys:
            self.assertIn(key, stats_dict)

    def test_n_matches_input(self):
        _, stats_dict = gaussian_aggregate(self.concentrations, self.errors)
        self.assertEqual(stats_dict["n"], len(self.concentrations))

    def test_handles_outlier_spread(self):
        concentrations = np.array([100.0, 120.0, 110.0, 175.0, 3000.0, 90.0])
        errors = np.array([5.0, 6.0, 5.0, 10.0, 25.0, 4.0])
        dist, stats_dict = gaussian_aggregate(concentrations, errors)
        self.assertTrue(np.isfinite(dist["x"]).all())
        self.assertTrue(np.isfinite(dist["y"]).all())
        self.assertLess(len(dist["x"]), 50000)


class TestPlottingFunctions(unittest.TestCase):
    """Test plotting functions return correct matplotlib objects."""

    def setUp(self):
        np.random.seed(42)
        self.x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        self.y = self.x * 2.5 + 10 + np.random.normal(0, 0.5, 5)
        self.x_err = np.ones_like(self.x) * 0.1
        self.y_err = np.ones_like(self.y) * 0.5

        slopes = np.random.normal(2.5, 0.1, 50)
        intercepts = np.random.normal(10, 0.5, 50)
        self.fit_params = [np.array([s, i]) for s, i in zip(slopes, intercepts)]
        self.confidence_df = evaluate_confidence(
            self.fit_params, line_max=6.0, line_interval=0.01
        )

    def test_plot_regression_returns_axes(self):
        ax = plot_regression(self.confidence_df)
        self.assertTrue(isinstance(ax, plt.Axes))
        plt.close()

    def test_plot_regression_with_datapoints(self):
        datapoints = pd.DataFrame(
            {"x": self.x, "y": self.y, "xerr": self.x_err, "yerr": self.y_err}
        )
        ax = plot_regression(self.confidence_df, datapoints=datapoints)
        self.assertTrue(isinstance(ax, plt.Axes))
        plt.close()

    def test_plot_regression_accepts_multiple_confidence_levels(self):
        conf_68 = self.confidence_df.copy()
        conf_95 = self.confidence_df.copy()
        conf_95["neg_error_bound"] = conf_95["neg_error_bound"] - 0.25
        conf_95["pos_error_bound"] = conf_95["pos_error_bound"] + 0.25

        fig, ax = plt.subplots()
        rendered = plot_regression(
            [conf_68, conf_95],
            ax=ax,
            ecolor=["#93c5fd", "#1d4ed8"],
            e_alpha=[0.2, 0.5],
        )
        self.assertTrue(isinstance(rendered, plt.Axes))
        self.assertGreaterEqual(len(ax.collections), 2)
        self.assertGreater(
            ax.get_xlim()[1],
            np.max(self.confidence_df.index.to_numpy()) * 1.05,
        )
        labels = (
            [text.get_text() for text in ax.get_legend().get_texts()]
            if ax.get_legend()
            else []
        )
        self.assertIn("Best fit", labels)
        self.assertIn("95% CI", labels)
        self.assertIn("68% CI", labels)
        self.assertEqual(len(labels), 3)
        plt.close(fig)

    def test_plot_density_returns_axes(self):
        concentrations = np.array([100.0, 105.0, 98.0])
        errors = np.array([5.0, 6.0, 4.0])
        dist, stats_dict = gaussian_aggregate(concentrations, errors)
        ax = plot_density(dist, stats_dict)
        self.assertTrue(isinstance(ax, plt.Axes))
        plt.close()

    def test_plot_calibration_estimates_returns_figure(self):
        fit_params = np.array([[100, 5], [105, 8], [98, 6]])
        fit_error = np.array([[5, 1], [6, 1.5], [4, 0.8]])
        fig = plot_calibration_estimates(fit_params, fit_error)
        self.assertTrue(isinstance(fig, plt.Figure))
        plt.close(fig)


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and edge cases."""

    def test_evaluate_confidence_raises_on_too_many_params(self):
        bad_params = [np.array([1.0, 2.0, 3.0])]
        with self.assertRaises(ValueError):
            evaluate_confidence(bad_params, line_max=6.0, line_interval=0.01)

    def test_bootstrap_handles_nan(self):
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.5, 5.0, 7.5, 10.0, 12.5])
        x_err = np.ones_like(x) * 0.1
        y_err = np.ones_like(y) * 0.5

        fit_params, subsamples = bootstrap_odr_fit(
            x, y, x_err, y_err, resample_draws=5, fit_intercept=True
        )
        self.assertIsInstance(fit_params, list)
        self.assertGreater(len(fit_params), 0)


if __name__ == "__main__":
    unittest.main()
