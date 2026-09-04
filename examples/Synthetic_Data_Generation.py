#%%
"""Generate the fixed synthetic calibration dataset used by ``example.py``.

This script is run **manually**, on demand, when you want a new synthetic
dataset — it is intentionally *not* wired into ``make regen-examples``,
``make docs``, or ``scripts/prepare-release.sh``, since those need
deterministic output on every run. Running this script writes
``examples/data/synthetic_calibration_standards.csv``, which ``example.py``
then reads as fixed input.

Run:
    uv run python examples/Synthetic_Data_Generation.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

OUTPUT_DIR = Path(__file__).resolve().parent
DATA_DIR = OUTPUT_DIR / "data"
STANDARDS_CSV = DATA_DIR / "synthetic_calibration_standards.csv"

X_COUNTS = np.array([62, 117, 223, 528, 1014, 2001])

# Reproducible: re-running this script regenerates the same numbers.
_RNG = np.random.default_rng(seed=7)


def generate_standards() -> pd.DataFrame:
    """Build a synthetic set of SIMS-style calibration standards.

    x = measured ion count rate (counts), y = known concentration (ppm),
    with 15% relative uncertainty simulated on both axes.
    """
    y_conc_ideal = X_COUNTS * (1 / 125) + 10
    y_conc = np.round(_RNG.normal(1, 0.15, len(X_COUNTS)) * y_conc_ideal, 2)
    x_uncertainty = np.abs(_RNG.normal(1, 0.1, len(X_COUNTS)) * X_COUNTS - X_COUNTS) + 5
    y_uncertainty = y_conc * 0.15

    return pd.DataFrame({
        "x_counts": X_COUNTS,
        "y_conc": y_conc,
        "x_uncertainty": x_uncertainty,
        "y_uncertainty": y_uncertainty,
    })


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    standards = generate_standards()
    standards.to_csv(STANDARDS_CSV, index=False)
    print(f"Saved synthetic calibration standards to {STANDARDS_CSV}")
    print(standards.to_string(index=False))

    plt.plot(X_COUNTS, X_COUNTS * (1 / 125) + 10, linestyle="none", marker=".", label="ideal")
    plt.errorbar(
        standards["x_counts"], standards["y_conc"],
        standards["y_uncertainty"], standards["x_uncertainty"],
        linestyle="none", label="simulated",
    )
    plt.xlim(0, 2300)
    plt.ylim(0)
    plt.xlabel("Count rate (counts)")
    plt.ylabel("Concentration (ppm)")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()

# %%
