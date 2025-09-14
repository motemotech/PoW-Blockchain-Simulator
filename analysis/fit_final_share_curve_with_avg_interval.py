import glob
import os
from datetime import datetime
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 画像出力用データディレクトリを指定する変数（Noneの場合は最新ディレクトリを自動選択）
DATA_DIR_OVERRIDE: Optional[str] = "data/theory-alpha-0.1-1000-ver2"

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


def detect_blockchain_type(data_dir: str) -> str:
    """ディレクトリ内のファイル名からブロックチェーンタイプ（BTC/ETH）を自動判別"""
    # w_piファイルをチェック
    w_pi_files = glob.glob(os.path.join(data_dir, "*_w_pi.csv"))
    for file in w_pi_files:
        filename = os.path.basename(file)
        if filename.startswith("BTC_"):
            return "BTC"
        elif filename.startswith("ETH_"):
            return "ETH"
    
    # shareファイルをチェック
    share_files = glob.glob(os.path.join(data_dir, "*_share.csv"))
    for file in share_files:
        filename = os.path.basename(file)
        if filename.startswith("BTC_"):
            return "BTC"
        elif filename.startswith("ETH_"):
            return "ETH"
    
    # デフォルトはBTC（後方互換性のため）
    print("Warning: Could not determine blockchain type from file names, defaulting to BTC")
    return "BTC"


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


def load_w_and_pi_data_with_avg_interval(data_dir: str, blockchain_type: str, difficulty_type: str) -> Tuple[pd.DataFrame, int]:
    """blockchain_typeとdifficulty_typeに基づいてw_piファイルを読み込み、avg_block_intervalも含めて返す"""
    pattern = os.path.join(data_dir, f"{blockchain_type}_*_{difficulty_type}_w_pi.csv")
    files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError(f"w_and_pi file not found with pattern: {pattern}")
    
    # 複数ファイルがある場合は最初のものを使用
    w_and_pi_file = files[0]
    df = pd.read_csv(w_and_pi_file)
    
    # avg_block_interval列が存在するかチェック
    if 'avg_block_interval' not in df.columns:
        raise ValueError(f"avg_block_interval column not found in {w_and_pi_file}")
    
    # ファイル名からノード数を取得
    # フォーマット: {blockchain_type}_[ノード数]_[endround数]_{difficulty_type}_w_pi.csv
    base = os.path.basename(w_and_pi_file)
    core = base.replace(f"_{difficulty_type}_w_pi.csv", "").replace(f"{blockchain_type}_", "")
    try:
        parts = core.split("_")
        if len(parts) >= 1:
            node_count = int(parts[0])  # 最初の部分がノード数
        else:
            raise ValueError("Could not parse node count from filename")
    except Exception:
        raise RuntimeError(f"Could not determine node count from w_pi file name: {w_and_pi_file}")
    
    return df, node_count


def load_final_share_points_with_avg_interval(data_dir: str, blockchain_type: str, difficulty_type: str, w_and_pi_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """avg_block_intervalを使用してfinal shareポイントを読み込む"""
    pattern = os.path.join(data_dir, f"{blockchain_type}_*_{difficulty_type}_share.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matched: {pattern}")

    deltas: List[float] = []
    Ts: List[float] = []
    ys: List[float] = []
    node_count = None

    # w_and_pi_dfからdelay->avg_block_intervalのマッピングを作成
    delay_to_avg_interval = dict(zip(w_and_pi_df['delay'], w_and_pi_df['avg_block_interval']))

    for fp in files:
        base = os.path.basename(fp)
        # filename: {blockchain_type}_{delta}_{nodeCount}_{endround}_{difficulty_type}_share.csv
        # Remove the prefix and suffix to get the core part
        core = base.replace(f"_{difficulty_type}_share.csv", "").replace(f"{blockchain_type}_", "")
        try:
            parts = core.split("_")
            delay = float(parts[0])  # 最初の部分がdelta
            if len(parts) >= 2:
                current_node_count = int(parts[1])  # 2番目の部分がノード数
                if node_count is None:
                    node_count = current_node_count
                elif node_count != current_node_count:
                    print(f"Warning: Inconsistent node count found: {node_count} vs {current_node_count}")
            
            # w_and_pi_dfからこのdelayに対応するavg_block_intervalを取得
            if delay in delay_to_avg_interval:
                T = delay_to_avg_interval[delay]
            else:
                print(f"Warning: No avg_block_interval found for delay {delay}, skipping")
                continue
                
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
    
    if node_count is None:
        raise RuntimeError("Could not determine node count from file names.")

    return np.array(deltas, dtype=float), np.array(Ts, dtype=float), np.array(ys, dtype=float), node_count


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float, float]:
    """Return (MSE, R^2, RMSE)."""
    mse = float(np.mean((y_true - y_pred) ** 2))
    rmse = float(np.sqrt(mse))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot != 0.0 else 1.0
    return mse, r2, rmse


def create_individual_comparison_plot_with_variable_T(variable_name: str, Delta_sorted: np.ndarray, T_sorted: np.ndarray, 
                                                    data_values: np.ndarray, theory_values: np.ndarray,
                                                    mse: float, r2: float, rmse: float, output_file_base: str, show_plot: bool,
                                                    alpha_fixed: float = 0.5) -> None:
    """Create individual comparison plot with variable T values."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    x_vals = Delta_sorted / T_sorted
    
    # Create smooth theory curve for plotting
    delta_min = Delta_sorted.min()
    delta_max = Delta_sorted.max()
    T_min = T_sorted.min()
    T_max = T_sorted.max()
    
    # 滑らかな曲線のため、Delta/Tの範囲を使用
    delta_over_T_min = (Delta_sorted / T_sorted).min()
    delta_over_T_max = (Delta_sorted / T_sorted).max()
    delta_over_T_smooth = np.linspace(delta_over_T_min, delta_over_T_max, 200)
    
    # 理論曲線のために平均的なT値を使用
    T_avg = T_sorted.mean()
    delta_smooth = delta_over_T_smooth * T_avg
    
    # Calculate smooth theory values
    theory_smooth = []
    for delta in delta_smooth:
        if variable_name == "r_A":
            r_A_th, _, _, _, _ = compute_theoretical_values(alpha_fixed, T_avg, delta)
            theory_smooth.append(r_A_th)
        elif variable_name == "pi_A":
            _, pi_A_th, _, _, _ = compute_theoretical_values(alpha_fixed, T_avg, delta)
            theory_smooth.append(pi_A_th)
        elif variable_name == "pi_O":
            _, _, pi_O_th, _, _ = compute_theoretical_values(alpha_fixed, T_avg, delta)
            theory_smooth.append(pi_O_th)
        elif variable_name == "W_A":
            _, _, _, W_A_th, _ = compute_theoretical_values(alpha_fixed, T_avg, delta)
            theory_smooth.append(W_A_th)
        elif variable_name == "W_O":
            _, _, _, _, W_O_th = compute_theoretical_values(alpha_fixed, T_avg, delta)
            theory_smooth.append(W_O_th)
    
    theory_smooth = np.array(theory_smooth)
    
    # Comparison plot
    ax.scatter(x_vals, data_values, s=40, alpha=0.8, label="Experimental Data", color="blue")
    ax.plot(delta_over_T_smooth, theory_smooth, color="crimson", lw=2.5, label=f"Theory (α={alpha_fixed})")
    
    ax.set_xlabel(r"$\Delta/T$", fontsize=12)
    
    # Set y-axis label based on variable
    if variable_name == "r_A":
        ax.set_ylabel("r_A (mining share)", fontsize=12)
    else:
        ax.set_ylabel(f"${variable_name}$", fontsize=12)
    
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Add metrics text with RMSE
    textstr = f'R²: {r2:.4f}\nRMSE: {rmse:.4f}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props)
    
    fig.tight_layout()
    
    # Save in multiple formats
    output_png = f"{output_file_base}.png"
    output_svg = f"{output_file_base}.svg"
    output_pdf = f"{output_file_base}.pdf"
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Saved {variable_name} comparison figure to: {output_png}")
    print(f"Saved {variable_name} comparison figure to: {output_svg}")
    print(f"Saved {variable_name} comparison figure to: {output_pdf}")
    
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
    
    # ブロックチェーンタイプの自動判別
    blockchain_type = detect_blockchain_type(data_dir)
    print(f"Detected blockchain type: {blockchain_type}")
    
    # 難易度タイプの自動判別
    difficulty_type = detect_difficulty_type(data_dir)
    print(f"Detected difficulty type: {difficulty_type}")
    
    # Load experimental data with avg_block_interval
    w_and_pi_df, node_count_w_pi = load_w_and_pi_data_with_avg_interval(data_dir, blockchain_type, difficulty_type)
    
    # Extract pi and W data from CSV (including avg_block_interval as T values)
    Delta_pi_w = w_and_pi_df['delay'].values
    T_pi_w = w_and_pi_df['avg_block_interval'].values  # avg_block_intervalをT値として使用
    pi_A_data = w_and_pi_df['pi_A'].values
    pi_O_data = w_and_pi_df['pi_O'].values
    w_A_data = w_and_pi_df['w_A'].values
    w_O_data = w_and_pi_df['w_O'].values

    print(f"Using avg_block_interval as T values: min={T_pi_w.min():.0f}, max={T_pi_w.max():.0f}, mean={T_pi_w.mean():.0f} ms")

    # Load final share points (r_A data from simulation) with avg_block_interval
    Delta_final, T_final, r_A_data_raw, node_count_share = load_final_share_points_with_avg_interval(data_dir, blockchain_type, difficulty_type, w_and_pi_df)
    
    # Verify node counts are consistent
    if node_count_w_pi != node_count_share:
        print(f"Warning: Node count mismatch between w_pi ({node_count_w_pi}) and share ({node_count_share}) files")
    
    node_count = node_count_w_pi  # Use w_pi node count as primary

    # Sort experimental data by Delta
    pi_w_order = np.argsort(Delta_pi_w)
    Delta_pi_w_sorted = Delta_pi_w[pi_w_order]
    T_pi_w_sorted = T_pi_w[pi_w_order]
    pi_A_data_sorted = pi_A_data[pi_w_order]
    pi_O_data_sorted = pi_O_data[pi_w_order]
    w_A_data_sorted = w_A_data[pi_w_order]
    w_O_data_sorted = w_O_data[pi_w_order]
    
    # Sort final share data by Delta
    final_order = np.argsort(Delta_final)
    Delta_final_sorted = Delta_final[final_order]
    T_final_sorted = T_final[final_order]
    r_A_data_sorted = r_A_data_raw[final_order]
    
    # アルファ値の設定（ブロックチェーンタイプに応じて調整可能）
    if blockchain_type == "BTC":
        alpha_fixed = 0.1  # 新しいデータに合わせて調整
    elif blockchain_type == "ETH":
        alpha_fixed = 0.1
    else:
        alpha_fixed = 0.1  # デフォルト値

    # Calculate theoretical values for pi/W data points (using variable T values)
    r_A_theory_list = []
    pi_A_theory_list = []
    pi_O_theory_list = []
    W_A_theory_list = []
    W_O_theory_list = []
    
    for delta, T in zip(Delta_pi_w_sorted, T_pi_w_sorted):
        r_A_th, pi_A_th, pi_O_th, W_A_th, W_O_th = compute_theoretical_values(alpha_fixed, T, delta)
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
    
    # Calculate theoretical values for final share data points (using variable T values)
    r_A_theory_final_list = []
    for delta, T in zip(Delta_final_sorted, T_final_sorted):
        r_A_th, _, _, _, _ = compute_theoretical_values(alpha_fixed, T, delta)
        r_A_theory_final_list.append(r_A_th)
    
    r_A_theory_final = np.array(r_A_theory_final_list)

    # Print metrics for each comparison
    print(f"alpha (fixed): {alpha_fixed:.3f}")
    print(f"Comparison metrics (using variable T from avg_block_interval):")
    
    # r_A comparison
    mse_r_A, r2_r_A, rmse_r_A = compute_metrics(r_A_data_sorted, r_A_theory_final)
    print(f"r_A: points={len(r_A_data_sorted)}, MSE={mse_r_A:.6g}, R²={r2_r_A:.6f}, RMSE={rmse_r_A:.6f}")
    
    # pi_A comparison
    mse_pi_A, r2_pi_A, rmse_pi_A = compute_metrics(pi_A_data_sorted, pi_A_theory)
    print(f"pi_A: points={len(pi_A_data_sorted)}, MSE={mse_pi_A:.6g}, R²={r2_pi_A:.6f}, RMSE={rmse_pi_A:.6f}")
    
    # pi_O comparison
    mse_pi_O, r2_pi_O, rmse_pi_O = compute_metrics(pi_O_data_sorted, pi_O_theory)
    print(f"pi_O: points={len(pi_O_data_sorted)}, MSE={mse_pi_O:.6g}, R²={r2_pi_O:.6f}, RMSE={rmse_pi_O:.6f}")
    
    # W_A comparison
    mse_W_A, r2_W_A, rmse_W_A = compute_metrics(w_A_data_sorted, W_A_theory)
    print(f"W_A: points={len(w_A_data_sorted)}, MSE={mse_W_A:.6g}, R²={r2_W_A:.6f}, RMSE={rmse_W_A:.6f}")
    
    # W_O comparison
    mse_W_O, r2_W_O, rmse_W_O = compute_metrics(w_O_data_sorted, W_O_theory)
    print(f"W_O: points={len(w_O_data_sorted)}, MSE={mse_W_O:.6g}, R²={r2_W_O:.6f}, RMSE={rmse_W_O:.6f}")

    # Create individual plots
    show_plot = False  # デフォルトでプロット表示なし
    
    # Generate timestamp and create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"./image/{timestamp}_with_avg_interval"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filenames with blockchain type, node count and difficulty type
    data_suffix = f"{blockchain_type}_{node_count}_{difficulty_type}_avg_interval"
    
    create_individual_comparison_plot_with_variable_T("r_A", Delta_final_sorted, T_final_sorted, r_A_data_sorted, r_A_theory_final, 
                                                    mse_r_A, r2_r_A, rmse_r_A, f"{output_dir}/r_A_{data_suffix}", show_plot, alpha_fixed)
    create_individual_comparison_plot_with_variable_T("pi_A", Delta_pi_w_sorted, T_pi_w_sorted, pi_A_data_sorted, pi_A_theory, 
                                                    mse_pi_A, r2_pi_A, rmse_pi_A, f"{output_dir}/pi_A_{data_suffix}", show_plot, alpha_fixed)
    create_individual_comparison_plot_with_variable_T("pi_O", Delta_pi_w_sorted, T_pi_w_sorted, pi_O_data_sorted, pi_O_theory, 
                                                    mse_pi_O, r2_pi_O, rmse_pi_O, f"{output_dir}/pi_O_{data_suffix}", show_plot, alpha_fixed)
    create_individual_comparison_plot_with_variable_T("W_A", Delta_pi_w_sorted, T_pi_w_sorted, w_A_data_sorted, W_A_theory, 
                                                    mse_W_A, r2_W_A, rmse_W_A, f"{output_dir}/W_A_{data_suffix}", show_plot, alpha_fixed)
    create_individual_comparison_plot_with_variable_T("W_O", Delta_pi_w_sorted, T_pi_w_sorted, w_O_data_sorted, W_O_theory, 
                                                    mse_W_O, r2_W_O, rmse_W_O, f"{output_dir}/W_O_{data_suffix}", show_plot, alpha_fixed)
    
    print(f"\nAll plots saved to directory: {output_dir}")


if __name__ == "__main__":
    main()
