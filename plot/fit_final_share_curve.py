import argparse
import glob
import os
from typing import List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def compute_r_A(alpha_a: float, T: float, Delta: np.ndarray) -> np.ndarray:
    """Theoretical r_A from fitting_curve.py.

    r_A = pi_A * W_A + (1 - pi_A) * W_O, where
      E = exp(- alpha_a * Delta / T)
      pi_A = (alpha_a*E + Delta * alpha_a^2 * E / T + 1 - E - Delta * alpha_a * E / T)
             / (1 + Delta * alpha_a^2 * E / T - Delta * alpha_a * E / T)
      W_A = 1
      W_1 = Delta * alpha_a * E / T
      W_2 = 1 - E - Delta * alpha_a * E / T
      S = (alpha_a - alpha_a * W_2 + W_2) / (1 + alpha_a * W_1 - W_1)
      W_O = W_1 * S + W_2
    """
    Delta = np.asarray(Delta, dtype=np.float64)
    E = np.exp(- alpha_a * Delta / T)
    numerator = (
        alpha_a * E
        + Delta * alpha_a * alpha_a * E / T
        + 1 - E
        - Delta * alpha_a * E / T
    )
    denominator = 1 + Delta * alpha_a * alpha_a * E / T - Delta * alpha_a * E / T
    pi_A = numerator / denominator
    W_A = 1.0
    W_1 = Delta * alpha_a * E / T
    W_2 = 1 - E - Delta * alpha_a * E / T
    S = (alpha_a - alpha_a * W_2 + W_2) / (1 + alpha_a * W_1 - W_1)
    W_O = W_1 * S + W_2
    r_A = pi_A * W_A + (1 - pi_A) * W_O
    return r_A


def load_final_share_points(data_dir: str, data_type: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load (Delta, T, final_share) from CSV files under data_dir.

    Returns
    - Delta: array of delays (ms)
    - T: array of T (ms)
    - y: array of final shares
    """
    pattern = os.path.join(data_dir, "*_plot.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matched: {pattern}")

    deltas: List[float] = []
    Ts: List[float] = []
    ys: List[float] = []

    for fp in files:
        base = os.path.basename(fp)
        # Filter by requested data type
        is_static = base.endswith("_static_plot.csv")
        if data_type == "dynamic" and is_static:
            continue
        if data_type == "static" and not is_static:
            continue
        # filename: {delay}_{generationTime}_{endRound}[_static]_plot.csv
        name = base.replace("_static_plot.csv", "_plot.csv")
        core = name[:-9]  # strip "_plot.csv"
        try:
            parts = core.split("_")
            delay = float(parts[0])
            T = float(parts[1])
        except Exception:
            # Skip unexpected names
            continue

        df = pd.read_csv(fp, header=None, names=["block_number", "time", "mining_share", "difficulty"])  # noqa: PD901
        if df.empty:
            continue
        final_share = float(df["mining_share"].iloc[-1])

        deltas.append(delay)
        Ts.append(T)
        ys.append(final_share)

    if not deltas:
        raise RuntimeError("No usable data points found.")

    return np.array(deltas, dtype=float), np.array(Ts, dtype=float), np.array(ys, dtype=float)

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    """Return (MSE, R^2)."""
    mse = float(np.mean((y_true - y_pred) ** 2))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot != 0.0 else 1.0
    return mse, r2


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare theoretical r_A(Delta) (alpha=0.5) to final-share data and plot.")
    parser.add_argument("--data-dir", type=str, default="data", help="Directory containing *_plot.csv files (default: ./data)")
    parser.add_argument("--data-type", type=str, default="dynamic", choices=["dynamic", "static", "both"], help="Which CSVs to use: dynamic (_plot.csv), static (_static_plot.csv), or both")
    parser.add_argument("--out", type=str, default="compare_r_A_to_final_share.png", help="Output figure filename")
    parser.add_argument("--no-show", action="store_true", help="Do not display the plot window")
    args = parser.parse_args()

    Delta, T, y = load_final_share_points(args.data_dir, args.data_type)

    # Sort and compute theoretical values with fixed alpha=0.5
    order = np.argsort(Delta)
    Delta_sorted = Delta[order]
    T_fixed = 600000
    y_sorted = y[order]
    alpha_fixed = 0.5
    y_theory = compute_r_A(alpha_fixed, T_fixed, Delta_sorted)

    mse, r2 = compute_metrics(y_sorted, y_theory)
    print(f"alpha (fixed): {alpha_fixed:.3f}")
    print(f"points: {len(y_sorted)}  MSE: {mse:.6g}  R^2: {r2:.6f}")

    # Plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 7))
    label_suffix = {
        "dynamic": "dynamic",
        "static": "static",
        "both": "both",
    }[args.data_type]
    ax.scatter(Delta_sorted / T_fixed, y_sorted, s=24, alpha=0.8, label=f"data (final share, {label_suffix})")
    ax.plot(Delta_sorted / T_fixed, y_theory, color="crimson", lw=2.0, label="theory (alpha=0.5)")
    ax.set_xlabel(r"$\Delta/T$")
    ax.set_ylabel("Final Share / r_A")
    ax.set_title(r"Comparison: theoretical $r_A(\Delta)$ vs. final-share data (no fitting)")
    ax.legend()
    fig.tight_layout()
    plt.savefig(args.out, dpi=300)
    print(f"Saved figure to: {args.out}")
    if not args.no_show:
        try:
            plt.show()
        except Exception:
            pass


if __name__ == "__main__":
    main()

