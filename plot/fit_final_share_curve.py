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


def load_w_and_pi_data(data_dir: str) -> pd.DataFrame:
    """Load w_and_pi data from CSV file.
    
    Returns DataFrame with columns: delay, pi_A, pi_O, w_A, w_O
    """
    w_and_pi_file = os.path.join(data_dir, "1000000static_w_and_pi.csv")
    if not os.path.exists(w_and_pi_file):
        raise FileNotFoundError(f"w_and_pi file not found: {w_and_pi_file}")
    
    df = pd.read_csv(w_and_pi_file)
    return df


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


def create_r_A_comparison_plot(Delta_sorted: np.ndarray, T_fixed: float, r_A_data: np.ndarray, r_A_theory: np.ndarray, output_file: str, show_plot: bool) -> None:
    """Create r_A comparison plot."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x_vals = Delta_sorted / T_fixed
    
    # Plot data and theory
    ax.scatter(x_vals, r_A_data, s=40, alpha=0.8, label="Data (actual share)", color="blue")
    ax.plot(x_vals, r_A_theory, color="crimson", lw=2.5, label="Theory (alpha=0.5)", marker='o', markersize=4)
    
    ax.set_xlabel(r"$\Delta/T$", fontsize=14)
    ax.set_ylabel(r"$r_A$ (Final Share)", fontsize=14)
    ax.set_title(r"Comparison: Theoretical $r_A$ vs. Actual Share Data", fontsize=16)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Add metrics text
    mse, r2 = compute_metrics(r_A_data, r_A_theory)
    textstr = f'MSE: {mse:.2e}\nR²: {r2:.4f}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
    
    fig.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved r_A comparison figure to: {output_file}")
    
    if show_plot:
        try:
            plt.show()
        except Exception:
            pass
    plt.close()


def create_pi_w_comparison_plot(Delta_sorted: np.ndarray, T_fixed: float, 
                               pi_A_data: np.ndarray, pi_O_data: np.ndarray,
                               w_A_data: np.ndarray, w_O_data: np.ndarray,
                               pi_A_theory: np.ndarray, pi_O_theory: np.ndarray,
                               W_A_theory: np.ndarray, W_O_theory: np.ndarray,
                               output_file: str, show_plot: bool) -> None:
    """Create pi and W comparison plots."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(r"Comparison: Theoretical vs. Data for $\pi$ and $W$ values (alpha=0.5)", fontsize=16)
    
    x_vals = Delta_sorted / T_fixed
    
    # pi_A
    axes[0, 0].scatter(x_vals, pi_A_data, s=40, alpha=0.8, label="Data", color="blue")
    axes[0, 0].plot(x_vals, pi_A_theory, color="crimson", lw=2.5, label="Theory", marker='o', markersize=4)
    axes[0, 0].set_xlabel(r"$\Delta/T$", fontsize=12)
    axes[0, 0].set_ylabel(r"$\pi_A$", fontsize=12)
    axes[0, 0].set_title(r"$\pi_A$ comparison", fontsize=14)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # pi_O
    axes[0, 1].scatter(x_vals, pi_O_data, s=40, alpha=0.8, label="Data", color="blue")
    axes[0, 1].plot(x_vals, pi_O_theory, color="crimson", lw=2.5, label="Theory", marker='o', markersize=4)
    axes[0, 1].set_xlabel(r"$\Delta/T$", fontsize=12)
    axes[0, 1].set_ylabel(r"$\pi_O$", fontsize=12)
    axes[0, 1].set_title(r"$\pi_O$ comparison", fontsize=14)
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # W_A
    axes[1, 0].scatter(x_vals, w_A_data, s=40, alpha=0.8, label="Data", color="blue")
    axes[1, 0].plot(x_vals, W_A_theory, color="crimson", lw=2.5, label="Theory", marker='o', markersize=4)
    axes[1, 0].set_xlabel(r"$\Delta/T$", fontsize=12)
    axes[1, 0].set_ylabel(r"$W_A$", fontsize=12)
    axes[1, 0].set_title(r"$W_A$ comparison", fontsize=14)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # W_O
    axes[1, 1].scatter(x_vals, w_O_data, s=40, alpha=0.8, label="Data", color="blue")
    axes[1, 1].plot(x_vals, W_O_theory, color="crimson", lw=2.5, label="Theory", marker='o', markersize=4)
    axes[1, 1].set_xlabel(r"$\Delta/T$", fontsize=12)
    axes[1, 1].set_ylabel(r"$W_O$", fontsize=12)
    axes[1, 1].set_title(r"$W_O$ comparison", fontsize=14)
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    fig.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved pi and W comparison figure to: {output_file}")
    
    if show_plot:
        try:
            plt.show()
        except Exception:
            pass
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare theoretical values to w_and_pi data and create separate plots.")
    parser.add_argument("--data-dir", type=str, default="tmp_data", help="Directory containing *_plot.csv files (default: ./tmp_data)")
    parser.add_argument("--r-a-out", type=str, default="r_A_comparison.png", help="Output filename for r_A comparison plot")
    parser.add_argument("--pi-w-out", type=str, default="pi_w_comparison.png", help="Output filename for pi and W comparison plot")
    parser.add_argument("--no-show", action="store_true", help="Do not display the plot window")
    args = parser.parse_args()

    # Load w_and_pi data
    w_and_pi_df = load_w_and_pi_data(args.data_dir)
    
    # Extract data from CSV
    Delta = w_and_pi_df['delay'].values
    pi_A_data = w_and_pi_df['pi_A'].values
    pi_O_data = w_and_pi_df['pi_O'].values
    w_A_data = w_and_pi_df['w_A'].values
    w_O_data = w_and_pi_df['w_O'].values

    # Sort by Delta
    order = np.argsort(Delta)
    Delta_sorted = Delta[order]
    pi_A_data_sorted = pi_A_data[order]
    pi_O_data_sorted = pi_O_data[order]
    w_A_data_sorted = w_A_data[order]
    w_O_data_sorted = w_O_data[order]
    
    # Compute theoretical values with fixed alpha=0.5
    T_fixed = 600000
    alpha_fixed = 0.5
    
    # Theoretical calculations
    E = np.exp(- alpha_fixed * Delta_sorted / T_fixed)
    numerator = (
        alpha_fixed * E
        + Delta_sorted * alpha_fixed * alpha_fixed * E / T_fixed
        + 1 - E
        - Delta_sorted * alpha_fixed * E / T_fixed
    )
    denominator = 1 + Delta_sorted * alpha_fixed * alpha_fixed * E / T_fixed - Delta_sorted * alpha_fixed * E / T_fixed
    pi_A_theory = numerator / denominator
    pi_O_theory = 1 - pi_A_theory
    
    W_A_theory = np.ones_like(Delta_sorted)  # W_A = 1
    W_1 = Delta_sorted * alpha_fixed * E / T_fixed
    W_2 = 1 - E - Delta_sorted * alpha_fixed * E / T_fixed
    S = (alpha_fixed - alpha_fixed * W_2 + W_2) / (1 + alpha_fixed * W_1 - W_1)
    W_O_theory = W_1 * S + W_2

    # Compute r_A for comparison
    r_A_theory = pi_A_theory * W_A_theory + pi_O_theory * W_O_theory
    r_A_data = pi_A_data_sorted * w_A_data_sorted + pi_O_data_sorted * w_O_data_sorted

    # Print metrics
    mse, r2 = compute_metrics(r_A_data, r_A_theory)
    print(f"alpha (fixed): {alpha_fixed:.3f}")
    print(f"points: {len(Delta_sorted)}  MSE: {mse:.6g}  R^2: {r2:.6f}")

    # Create plots
    show_plot = not args.no_show
    
    # Plot 1: r_A comparison
    create_r_A_comparison_plot(Delta_sorted, T_fixed, r_A_data, r_A_theory, args.r_a_out, show_plot)
    
    # Plot 2: pi and W comparison
    create_pi_w_comparison_plot(Delta_sorted, T_fixed, 
                               pi_A_data_sorted, pi_O_data_sorted,
                               w_A_data_sorted, w_O_data_sorted,
                               pi_A_theory, pi_O_theory,
                               W_A_theory, W_O_theory,
                               args.pi_w_out, show_plot)


if __name__ == "__main__":
    main()

