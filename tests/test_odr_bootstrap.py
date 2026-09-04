"""
Unit tests for ODR bootstrapping and calibration functions.
"""

import re
import unittest

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from odr_bootstrap import (
    apply_calibration,
    apply_calibration_y,
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


class TestApplyCalibration(unittest.TestCase):
    """Test calibration-application helpers."""

    def setUp(self):
        np.random.seed(123)
        slopes = np.random.normal(2.0, 0.05, 200)
        intercepts = np.random.normal(1.0, 0.2, 200)
        self.fit_params = [np.array([2.0, 1.0], dtype=float)]
        self.fit_params.extend(
            [np.array([slope, intercept], dtype=float) for slope, intercept in zip(slopes, intercepts)]
        )

    def test_applies_calibration_to_x_values(self):
        result = apply_calibration(
            [1.0, 2.0, 5.0],
            self.fit_params,
            fit_intercept=True,
            variable="x",
            confidence_levels=(0.68, 0.95),
        )
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue({"input_value", "best_fit", "median", "neg_ci_68", "pos_ci_68"}.issubset(result.columns))
        self.assertAlmostEqual(result["best_fit"].iloc[0], 3.0, places=3)
        self.assertAlmostEqual(result["best_fit"].iloc[-1], 11.0, places=3)

    def test_applies_calibration_to_y_values_and_accepts_percent_levels(self):
        result = apply_calibration_y(
            [3.0, 5.0],
            self.fit_params,
            fit_intercept=True,
            confidence_levels=(68, 95),
        )
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("neg_ci_68", result.columns)
        self.assertIn("pos_ci_95", result.columns)
        self.assertAlmostEqual(result["best_fit"].iloc[0], 1.0, places=2)
        self.assertAlmostEqual(result["best_fit"].iloc[1], 2.0, places=2)


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


class TestGroundTruthRecovery(unittest.TestCase):
    """odr_bootstrap + gaussian_aggregate should recover the parameters used
    to generate synthetic calibration data, within their own bootstrap
    uncertainty, at both "normal" and slope-scale (<<1) magnitudes.
    """

    def _assert_recovers(self, x, true_slope, true_intercept, x_err, y_err, rng):
        y = true_slope * x + true_intercept + rng.normal(0, y_err, size=x.shape)

        confidence_data, best_fit_params, points, all_params, _ = odr_bootstrap(
            x=x, y=y, x_err=x_err, y_err=y_err,
            resample_draws=500, fit_intercept=True,
        )
        del confidence_data, points  # not needed for this assertion

        all_params_arr = np.asarray(all_params, dtype=float)
        slopes = all_params_arr[:, 0]
        intercepts = all_params_arr[:, 1]
        slope_std = slopes.std()
        intercept_std = intercepts.std()

        # The best fit (all_params[0], = best_fit_params) should land within
        # a few bootstrap standard deviations of the true generating values.
        self.assertLess(abs(best_fit_params[0] - true_slope), 3 * slope_std)
        self.assertLess(abs(best_fit_params[1] - true_intercept), 3 * intercept_std)

        # The same check, through the exact aggregation chain used by
        # examples/example.py to plot the bootstrap distributions.
        slope_dist, slope_stats = gaussian_aggregate(
            slopes, np.full_like(slopes, slope_std)
        )
        intercept_dist, intercept_stats = gaussian_aggregate(
            intercepts, np.full_like(intercepts, intercept_std)
        )
        self.assertGreater(len(slope_dist["x"]), 1000)
        self.assertGreater(len(intercept_dist["x"]), 1000)
        self.assertLess(abs(slope_stats["mean"] - true_slope), 3 * slope_std)
        self.assertLess(abs(intercept_stats["mean"] - true_intercept), 3 * intercept_std)

    def test_recovers_normal_scale_parameters(self):
        rng = np.random.default_rng(42)
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        self._assert_recovers(
            x, true_slope=2.5, true_intercept=10.0,
            x_err=np.full_like(x, 0.1), y_err=np.full_like(x, 0.5), rng=rng,
        )

    def test_recovers_small_slope_parameters(self):
        """Mirrors the SIMS-style calibration in examples/example.py, where
        the slope (~0.006-0.01 ppm/count) is small enough to have triggered
        the gaussian_aggregate grid-step bug.
        """
        rng = np.random.default_rng(7)
        x = np.array([62.0, 117.0, 223.0, 528.0, 1014.0, 2001.0])
        true_slope = 1 / 125  # ~0.008
        true_intercept = 10.0
        self._assert_recovers(
            x, true_slope=true_slope, true_intercept=true_intercept,
            x_err=np.abs(rng.normal(1, 0.1, len(x)) * x - x) + 5,
            y_err=(true_slope * x + true_intercept) * 0.15,
            rng=rng,
        )


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


class TestGaussianAggregateSmallMagnitude(unittest.TestCase):
    """Regression tests for gaussian_aggregate with slope-scale values.

    A hardcoded 0.01 grid-step floor used to force a 1-3 point evaluation
    grid for distributions with a spread well under 0.01 (e.g. a calibration
    slope around 0.006), rendering as a triangle instead of a smooth curve.
    These tests fit slope-scale synthetic bootstrap draws directly, mirroring
    ``all_params_array[:, 0]`` in examples/example.py.
    """

    def setUp(self):
        rng = np.random.default_rng(0)
        self.true_mean = 0.00583
        self.true_std = 0.00095
        self.slopes = rng.normal(self.true_mean, self.true_std, 2000)

    def test_grid_has_many_points(self):
        """The old 0.01 floor produced only 1-3 points for this spread."""
        dist, _ = gaussian_aggregate(self.slopes, np.full_like(self.slopes, self.true_std))
        self.assertGreater(len(dist["x"]), 1000)

    def test_mean_and_mode_match_input(self):
        _, stats_dict = gaussian_aggregate(self.slopes, np.full_like(self.slopes, self.true_std))
        self.assertAlmostEqual(stats_dict["mean"], self.true_mean, delta=3 * self.true_std)
        self.assertAlmostEqual(stats_dict["mid_point"], self.true_mean, delta=3 * self.true_std)

    def test_one_sigma_bounds_match_input_std(self):
        _, stats_dict = gaussian_aggregate(self.slopes, np.full_like(self.slopes, self.true_std))
        lower, upper = stats_dict["one_sigma_bounds"]
        # Old rounding to 2 decimals would have collapsed this span to 0.
        self.assertGreater(upper - lower, 0)
        self.assertAlmostEqual(upper - lower, 2 * self.true_std, delta=self.true_std)

    def test_ci_one_sigma_not_rounded_to_zero(self):
        _, stats_dict = gaussian_aggregate(self.slopes, np.full_like(self.slopes, self.true_std))
        neg, pos = stats_dict["CI_one_sigma"]
        self.assertGreater(neg, 0)
        self.assertGreater(pos, 0)


class TestPlotDensityFormatting(unittest.TestCase):
    """plot_density should format annotation text based on value magnitude."""

    def test_small_values_use_general_notation(self):
        rng = np.random.default_rng(1)
        slopes = rng.normal(0.00583, 0.00095, 500)
        dist, stats_dict = gaussian_aggregate(slopes, np.full_like(slopes, slopes.std()))
        fig, ax = plt.subplots()
        plot_density(dist, stats_dict, ax=ax)
        text = ax.texts[0].get_text()
        plt.close(fig)
        # Fixed 2-decimal notation (the pre-fix behavior) would print exactly
        # "0.00" or "0.01" here, discarding all significant digits.
        match = re.search(r"Mean: (\S+)", text)
        self.assertIsNotNone(match)
        self.assertNotIn(match.group(1), {"0.00", "0.01", "-0.00"})
        self.assertAlmostEqual(float(match.group(1)), stats_dict["mean"], delta=1e-4)

    def test_large_values_use_general_notation(self):
        values = np.array([1.5e6, 1.52e6, 1.48e6])
        errors = np.array([1e4, 1e4, 1e4])
        dist, stats_dict = gaussian_aggregate(values, errors)
        fig, ax = plt.subplots()
        plot_density(dist, stats_dict, ax=ax)
        text = ax.texts[0].get_text()
        plt.close(fig)
        self.assertIn("e+06", text)

    def test_normal_scale_values_keep_fixed_point_notation(self):
        concentrations = np.array([100.0, 105.0, 98.0, 102.0, 101.0])
        errors = np.array([5.0, 6.0, 4.0, 5.5, 4.5])
        dist, stats_dict = gaussian_aggregate(concentrations, errors)
        fig, ax = plt.subplots()
        plot_density(dist, stats_dict, ax=ax)
        text = ax.texts[0].get_text()
        plt.close(fig)
        self.assertIn(f"Mean: {stats_dict['mean']:.2f}", text)


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

    def test_plot_density_xlabel_default(self):
        concentrations = np.array([100.0, 105.0, 98.0])
        errors = np.array([5.0, 6.0, 4.0])
        dist, stats_dict = gaussian_aggregate(concentrations, errors)
        ax = plot_density(dist, stats_dict)
        self.assertEqual(ax.get_xlabel(), "Value")
        plt.close()

    def test_plot_density_xlabel_custom(self):
        concentrations = np.array([100.0, 105.0, 98.0])
        errors = np.array([5.0, 6.0, 4.0])
        dist, stats_dict = gaussian_aggregate(concentrations, errors)
        ax = plot_density(dist, stats_dict, xlabel="Calibration Slope")
        self.assertEqual(ax.get_xlabel(), "Calibration Slope")
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
