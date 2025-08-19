import glob
import os
from datetime import datetime
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 画像出力用データディレクトリを指定する変数（Noneの場合は最新ディレクトリを自動選択）
DATA_DIR_OVERRIDE: Optional[str] = None

def compute_theoretical_values(alpha_a: float, T: float, Delta: float) -> Tuple[float, float, float, float, float]:
    E = np.exp(- alpha_a * Delta / T)
    numerator = (
        alpha_a * E
        + Delta * alpha_a * alpha_a * E / T
        + 1 - E
        - Delta * alpha_a * E / T
    )
    denominator = 1 + Delta * alpha_a * alpha_a * E / T - Delta * alpha_a * E / T
    pi_A = numerator / denominator
    pi_O = 1 - pi_A
    W_A = 1.0
    W_1 = Delta * alpha_a * E / T
    W_2 = 1 - E - Delta * alpha_a * E / T
    S = (alpha_a - alpha_a * W_2 + W_2) / (1 + alpha_a * W_1 - W_1)
    W_O = W_1 * S + W_2
    r_A = pi_A * W_A + (1 - pi_A) * W_O
    return r_A, pi_A, pi_O, W_A, W_O


def get_latest_data_directory() -> str:
    """data/ディレクトリから最新のタイムスタンプディレクトリを取得"""
    data_dirs = glob.glob("data/????????_??????")
    if not data_dirs:
        raise FileNotFoundError("No timestamp directories found in data/")
    return max(data_dirs)  # 最新のディレクトリを返す


def detect_difficulty_type(data_dir: str) -> str:
    """ディレクトリ内のファイル名からdynamic/staticを自動判別"""
    # w_piファイルをチェック
    w_pi_files = glob.glob(os.path.join(data_dir, "*_w_pi.csv"))
    for file in w_pi_files:
        filename = os.path.basename(file)
        if "_dynamic_w_pi.csv" in filename:
            return "dynamic"
        elif "_static_w_pi.csv" in filename:
            return "static"
    
    # shareファイルをチェック
    share_files = glob.glob(os.path.join(data_dir, "*_share.csv"))
    for file in share_files:
        filename = os.path.basename(file)
        if "_dynamic_share.csv" in filename:
            return "dynamic"
        elif "_static_share.csv" in filename:
            return "static"
    
    raise FileNotFoundError("Could not determine difficulty type from file names")


def load_w_and_pi_data(data_dir: str, difficulty_type: str) -> pd.DataFrame:
    """difficulty_typeに基づいてw_piファイルを読み込み"""
    pattern = os.path.join(data_dir, f"*_{difficulty_type}_w_pi.csv")
    files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError(f"w_and_pi file not found with pattern: {pattern}")
    
    # 複数ファイルがある場合は最初のものを使用
    w_and_pi_file = files[0]
    df = pd.read_csv(w_and_pi_file)
    return df


def load_final_share_points(data_dir: str, difficulty_type: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    pattern = os.path.join(data_dir, f"*_{difficulty_type}_share.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matched: {pattern}")

    deltas: List[float] = []
    Ts: List[float] = []
    ys: List[float] = []

    for fp in files:
        base = os.path.basename(fp)
        # filename: {delay}_{nodeCount}_{endRound}_{difficulty_type}_share.csv
        # Remove the suffix to get the core part
        core = base.replace(f"_{difficulty_type}_share.csv", "")
        try:
            parts = core.split("_")
            delay = float(parts[0])
            if len(parts) >= 3:
                T = 600000  # Fixed generation time
            else:
                T = 600000  # Default value
        except Exception:
            # Skip unexpected names
            continue

        df = pd.read_csv(fp, header=None)  # noqa: PD901
        if df.empty:
            continue
        
        # CSVファイルの最後の行から最終的なマイニングシェアを取得
        # フォーマット: "block_number: final_share"
        last_line = df.iloc[-1, 0]
        try:
            final_share = float(last_line.split(": ")[1])
        except (IndexError, ValueError):
            continue

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


def create_individual_comparison_plot(variable_name: str, Delta_sorted: np.ndarray, T_fixed: float, 
                                    data_values: np.ndarray, theory_values: np.ndarray,
                                    mse: float, r2: float, output_file: str, show_plot: bool) -> None:
    """Create individual comparison plot with difference subplot."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    x_vals = Delta_sorted / T_fixed
    
    # Top subplot: Comparison
    ax1.scatter(x_vals, data_values, s=40, alpha=0.8, label="Experimental Data", color="blue")
    ax1.plot(x_vals, theory_values, color="crimson", lw=2.5, label="Theory (α=0.5)", marker='o', markersize=4)
    
    ax1.set_xlabel(r"$\Delta/T$", fontsize=12)
    ax1.set_ylabel(f"${variable_name}$", fontsize=12)
    ax1.set_title(f"Comparison: Theoretical vs. Experimental ${variable_name}$", fontsize=14)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Add metrics text
    textstr = f'MSE: {mse:.2e}\nR²: {r2:.4f}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    # Bottom subplot: Difference (Theory - Data)
    difference = theory_values - data_values
    ax2.plot(x_vals, difference, color="darkgreen", lw=2, marker='s', markersize=3, label="Theory - Data")
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    ax2.set_xlabel(r"$\Delta/T$", fontsize=12)
    ax2.set_ylabel(f"Difference (${variable_name}$)", fontsize=12)
    ax2.set_title(f"Difference: Theory - Experimental Data", fontsize=14)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    fig.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved {variable_name} comparison figure to: {output_file}")
    
    if show_plot:
        try:
            plt.show()
        except Exception:
            pass
    plt.close()


def main() -> None:
    # データディレクトリの決定
    if DATA_DIR_OVERRIDE:
        data_dir = DATA_DIR_OVERRIDE
        print(f"Using specified data directory: {data_dir}")
    else:
        data_dir = get_latest_data_directory()
        print(f"Using latest data directory: {data_dir}")
    
    # 難易度タイプの自動判別
    difficulty_type = detect_difficulty_type(data_dir)
    print(f"Detected difficulty type: {difficulty_type}")
    
    # Load experimental data
    w_and_pi_df = load_w_and_pi_data(data_dir, difficulty_type)
    
    # Extract pi and W data from CSV
    Delta_pi_w = w_and_pi_df['delay'].values
    pi_A_data = w_and_pi_df['pi_A'].values
    pi_O_data = w_and_pi_df['pi_O'].values
    w_A_data = w_and_pi_df['w_A'].values
    w_O_data = w_and_pi_df['w_O'].values

    # Load final share points (r_A data from simulation)
    Delta_final, T_final, r_A_data_raw = load_final_share_points(data_dir, difficulty_type)

    # Sort experimental data by Delta
    pi_w_order = np.argsort(Delta_pi_w)
    Delta_pi_w_sorted = Delta_pi_w[pi_w_order]
    pi_A_data_sorted = pi_A_data[pi_w_order]
    pi_O_data_sorted = pi_O_data[pi_w_order]
    w_A_data_sorted = w_A_data[pi_w_order]
    w_O_data_sorted = w_O_data[pi_w_order]
    
    # Sort final share data by Delta
    final_order = np.argsort(Delta_final)
    Delta_final_sorted = Delta_final[final_order]
    r_A_data_sorted = r_A_data_raw[final_order]
    
    # Compute theoretical values using compute_theoretical_values
    T_fixed = 600000
    alpha_fixed = 0.5
    
    # Calculate theoretical values for pi/W data points
    r_A_theory_list = []
    pi_A_theory_list = []
    pi_O_theory_list = []
    W_A_theory_list = []
    W_O_theory_list = []
    
    for delta in Delta_pi_w_sorted:
        r_A_th, pi_A_th, pi_O_th, W_A_th, W_O_th = compute_theoretical_values(alpha_fixed, T_fixed, delta)
        r_A_theory_list.append(r_A_th)
        pi_A_theory_list.append(pi_A_th)
        pi_O_theory_list.append(pi_O_th)
        W_A_theory_list.append(W_A_th)
        W_O_theory_list.append(W_O_th)
    
    r_A_theory_pi_w = np.array(r_A_theory_list)
    pi_A_theory = np.array(pi_A_theory_list)
    pi_O_theory = np.array(pi_O_theory_list)
    W_A_theory = np.array(W_A_theory_list)
    W_O_theory = np.array(W_O_theory_list)
    
    # Calculate theoretical values for final share data points
    r_A_theory_final_list = []
    for delta in Delta_final_sorted:
        r_A_th, _, _, _, _ = compute_theoretical_values(alpha_fixed, T_fixed, delta)
        r_A_theory_final_list.append(r_A_th)
    
    r_A_theory_final = np.array(r_A_theory_final_list)

    # Print metrics for each comparison
    print(f"alpha (fixed): {alpha_fixed:.3f}")
    print(f"Comparison metrics:")
    
    # r_A comparison
    mse_r_A, r2_r_A = compute_metrics(r_A_data_sorted, r_A_theory_final)
    print(f"r_A: points={len(r_A_data_sorted)}, MSE={mse_r_A:.6g}, R²={r2_r_A:.6f}")
    
    # pi_A comparison
    mse_pi_A, r2_pi_A = compute_metrics(pi_A_data_sorted, pi_A_theory)
    print(f"pi_A: points={len(pi_A_data_sorted)}, MSE={mse_pi_A:.6g}, R²={r2_pi_A:.6f}")
    
    # pi_O comparison
    mse_pi_O, r2_pi_O = compute_metrics(pi_O_data_sorted, pi_O_theory)
    print(f"pi_O: points={len(pi_O_data_sorted)}, MSE={mse_pi_O:.6g}, R²={r2_pi_O:.6f}")
    
    # W_A comparison
    mse_W_A, r2_W_A = compute_metrics(w_A_data_sorted, W_A_theory)
    print(f"W_A: points={len(w_A_data_sorted)}, MSE={mse_W_A:.6g}, R²={r2_W_A:.6f}")
    
    # W_O comparison
    mse_W_O, r2_W_O = compute_metrics(w_O_data_sorted, W_O_theory)
    print(f"W_O: points={len(w_O_data_sorted)}, MSE={mse_W_O:.6g}, R²={r2_W_O:.6f}")

    # Create individual plots
    show_plot = False  # デフォルトでプロット表示なし
    
    # Generate timestamp and create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"./image/{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filenames with difficulty type prefix
    data_suffix = difficulty_type
    
    create_individual_comparison_plot("r_A", Delta_final_sorted, T_fixed, r_A_data_sorted, r_A_theory_final, 
                                    mse_r_A, r2_r_A, f"{output_dir}/r_A_{data_suffix}.png", show_plot)
    create_individual_comparison_plot("pi_A", Delta_pi_w_sorted, T_fixed, pi_A_data_sorted, pi_A_theory, 
                                    mse_pi_A, r2_pi_A, f"{output_dir}/pi_A_{data_suffix}.png", show_plot)
    create_individual_comparison_plot("pi_O", Delta_pi_w_sorted, T_fixed, pi_O_data_sorted, pi_O_theory, 
                                    mse_pi_O, r2_pi_O, f"{output_dir}/pi_O_{data_suffix}.png", show_plot)
    create_individual_comparison_plot("W_A", Delta_pi_w_sorted, T_fixed, w_A_data_sorted, W_A_theory, 
                                    mse_W_A, r2_W_A, f"{output_dir}/W_A_{data_suffix}.png", show_plot)
    create_individual_comparison_plot("W_O", Delta_pi_w_sorted, T_fixed, w_O_data_sorted, W_O_theory, 
                                    mse_W_O, r2_W_O, f"{output_dir}/W_O_{data_suffix}.png", show_plot)
    
    print(f"\nAll plots saved to directory: {output_dir}")


if __name__ == "__main__":
    main()

