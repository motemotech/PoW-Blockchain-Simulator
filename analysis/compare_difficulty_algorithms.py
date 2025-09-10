import glob
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 画像出力用データディレクトリを指定する変数（Noneの場合は最新ディレクトリを自動選択）
DATA_DIRS: Dict[str, Optional[str]] = {
    "no_adjustment": "data/theory-alpha-0.5-1000",  # 難易度調整なし
    "btc_adjustment": "data/btc_2016",  # BTCの難易度調整
    "eth_adjustment": "data/20250910_113213",  # ETHの難易度調整
}

# プロット用の色とラベル設定
PLOT_CONFIG = {
    "no_adjustment": {"color": "blue", "label": "No Difficulty Adjustment", "marker": "o"},
    "btc_adjustment": {"color": "orange", "label": "BTC Difficulty Adjustment", "marker": "o"},
    "eth_adjustment": {"color": "green", "label": "ETH Difficulty Adjustment", "marker": "o"},
}


def compute_theoretical_values(alpha_a: float, T: float, Delta: float) -> Tuple[float, float, float, float, float]:
    """理論値を計算する関数（fit_final_share_curve.pyから移植）"""
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


def get_target_generation_time(blockchain_type: str) -> float:
    """ブロックチェーンタイプに応じたターゲット生成時間を返す"""
    if blockchain_type == "BTC":
        return 600000.0  # Bitcoin: 10分
    elif blockchain_type == "ETH":
        return 15000.0  # Ethereum: 15秒
    else:
        raise ValueError(f"Unknown blockchain type: {blockchain_type}")


def load_w_and_pi_data(data_dir: str, blockchain_type: str, difficulty_type: str) -> Tuple[pd.DataFrame, int]:
    """blockchain_typeとdifficulty_typeに基づいてw_piファイルを読み込み、ノード数も返す"""
    pattern = os.path.join(data_dir, f"{blockchain_type}_*_{difficulty_type}_w_pi.csv")
    files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError(f"w_and_pi file not found with pattern: {pattern}")
    
    # 複数ファイルがある場合は最初のものを使用
    w_and_pi_file = files[0]
    df = pd.read_csv(w_and_pi_file)
    
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


def load_final_share_points(data_dir: str, blockchain_type: str, difficulty_type: str, target_generation_time: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """最終マイニングシェアデータを読み込む"""
    pattern = os.path.join(data_dir, f"{blockchain_type}_*_{difficulty_type}_share.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matched: {pattern}")

    deltas: List[float] = []
    Ts: List[float] = []
    ys: List[float] = []
    node_count = None

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
            T = target_generation_time  # ブロックチェーンタイプに応じた生成時間を使用
        except Exception:
            # Skip unexpected names
            continue

        df = pd.read_csv(fp, header=None)
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


def load_algorithm_data(data_dir: str) -> Dict[str, Dict]:
    """指定されたディレクトリから各変数のデータを読み込む"""
    blockchain_type = detect_blockchain_type(data_dir)
    difficulty_type = detect_difficulty_type(data_dir)
    target_generation_time = get_target_generation_time(blockchain_type)
    
    # w_piデータの読み込み
    w_and_pi_df, node_count_w_pi = load_w_and_pi_data(data_dir, blockchain_type, difficulty_type)
    
    # 最終シェアデータの読み込み
    Delta_final, T_final, r_A_data_raw, node_count_share = load_final_share_points(
        data_dir, blockchain_type, difficulty_type, target_generation_time)
    
    # データの整理
    Delta_pi_w = w_and_pi_df['delay'].values
    pi_A_data = w_and_pi_df['pi_A'].values
    pi_O_data = w_and_pi_df['pi_O'].values
    w_A_data = w_and_pi_df['w_A'].values
    w_O_data = w_and_pi_df['w_O'].values
    
    # ソート
    pi_w_order = np.argsort(Delta_pi_w)
    final_order = np.argsort(Delta_final)
    
    return {
        "blockchain_type": blockchain_type,
        "difficulty_type": difficulty_type,
        "target_generation_time": target_generation_time,
        "node_count": node_count_w_pi,
        "Delta_pi_w": Delta_pi_w[pi_w_order],
        "pi_A_data": pi_A_data[pi_w_order],
        "pi_O_data": pi_O_data[pi_w_order],
        "w_A_data": w_A_data[pi_w_order],
        "w_O_data": w_O_data[pi_w_order],
        "Delta_final": Delta_final[final_order],
        "r_A_data": r_A_data_raw[final_order],
    }


def create_comparison_plot(variable_name: str, all_data: Dict[str, Dict], 
                          output_file_base: str, show_plot: bool, alpha_fixed: float = 0.5) -> None:
    """三つのアルゴリズムの比較プロットを作成"""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # 理論曲線用の滑らかなデルタ値を作成
    all_deltas = []
    all_T = None
    
    for alg_name, data in all_data.items():
        if variable_name == "r_A":
            all_deltas.extend(data["Delta_final"])
        else:
            all_deltas.extend(data["Delta_pi_w"])
        if all_T is None:
            all_T = data["target_generation_time"]
    
    delta_min = min(all_deltas)
    delta_max = max(all_deltas)
    delta_smooth = np.linspace(delta_min, delta_max, 200)
    
    # 理論曲線を計算してプロット
    theory_smooth = []
    for delta in delta_smooth:
        if variable_name == "r_A":
            r_A_th, _, _, _, _ = compute_theoretical_values(alpha_fixed, all_T, delta)
            theory_smooth.append(r_A_th)
        elif variable_name == "pi_A":
            _, pi_A_th, _, _, _ = compute_theoretical_values(alpha_fixed, all_T, delta)
            theory_smooth.append(pi_A_th)
        elif variable_name == "pi_O":
            _, _, pi_O_th, _, _ = compute_theoretical_values(alpha_fixed, all_T, delta)
            theory_smooth.append(pi_O_th)
        elif variable_name == "W_A":
            _, _, _, W_A_th, _ = compute_theoretical_values(alpha_fixed, all_T, delta)
            theory_smooth.append(W_A_th)
        elif variable_name == "W_O":
            _, _, _, _, W_O_th = compute_theoretical_values(alpha_fixed, all_T, delta)
            theory_smooth.append(W_O_th)
    
    theory_smooth = np.array(theory_smooth)
    x_smooth = delta_smooth / all_T
    
    # 理論曲線をプロット
    ax.plot(x_smooth, theory_smooth, color="crimson", lw=3, 
           label=f"Theory (α={alpha_fixed})", zorder=10)
    
    # 各アルゴリズムのデータをプロット
    for alg_name, data in all_data.items():
        config = PLOT_CONFIG[alg_name]
        
        if variable_name == "r_A":
            x_vals = data["Delta_final"] / data["target_generation_time"]
            y_vals = data["r_A_data"]
        elif variable_name == "pi_A":
            x_vals = data["Delta_pi_w"] / data["target_generation_time"]
            y_vals = data["pi_A_data"]
        elif variable_name == "pi_O":
            x_vals = data["Delta_pi_w"] / data["target_generation_time"]
            y_vals = data["pi_O_data"]
        elif variable_name == "W_A":
            x_vals = data["Delta_pi_w"] / data["target_generation_time"]
            y_vals = data["w_A_data"]
        elif variable_name == "W_O":
            x_vals = data["Delta_pi_w"] / data["target_generation_time"]
            y_vals = data["w_O_data"]
        
        ax.scatter(x_vals, y_vals, s=50, alpha=0.8, 
                  color=config["color"], label=config["label"], 
                  marker=config["marker"], edgecolors='black', linewidth=0.5)
    
    # 軸とラベルの設定
    ax.set_xlabel(r"$\Delta/T$", fontsize=14)
    
    if variable_name == "r_A":
        ax.set_ylabel("r_A (mining share)", fontsize=14)
    else:
        ax.set_ylabel(f"${variable_name}$", fontsize=14)
    
    ax.legend(fontsize=12, loc='best')
    ax.grid(True, alpha=0.3)
    
    # タイトルは学術論文では不要なので削除
    
    fig.tight_layout()
    
    # 複数フォーマットで保存
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
    """メイン処理"""
    print("Loading data from three difficulty adjustment algorithms...")
    
    # データディレクトリの決定
    all_data = {}
    
    for alg_name, data_dir_override in DATA_DIRS.items():
        print(f"\nProcessing {alg_name}...")
        
        if data_dir_override:
            data_dir = data_dir_override
            print(f"Using specified data directory: {data_dir}")
        else:
            # 自動的に最新ディレクトリを選択（実際の使用時は手動で指定することを推奨）
            data_dir = get_latest_data_directory()
            print(f"Using latest data directory: {data_dir}")
            print("WARNING: Using latest directory for all algorithms. Please specify directories manually in DATA_DIRS.")
        
        try:
            all_data[alg_name] = load_algorithm_data(data_dir)
            print(f"Successfully loaded {alg_name} data:")
            print(f"  Blockchain type: {all_data[alg_name]['blockchain_type']}")
            print(f"  Difficulty type: {all_data[alg_name]['difficulty_type']}")
            print(f"  Node count: {all_data[alg_name]['node_count']}")
            print(f"  Target generation time: {all_data[alg_name]['target_generation_time']} ms")
        except Exception as e:
            print(f"Error loading data for {alg_name}: {e}")
            return
    
    # アルファ値の設定
    alpha_fixed = 0.5
    
    # 出力ディレクトリの作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"./analysis/comparison_plots_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    # プロット表示設定
    show_plot = False
    
    # 各変数の比較プロットを作成
    variables = ["r_A", "pi_A", "pi_O", "W_A", "W_O"]
    
    for var in variables:
        print(f"\nCreating comparison plot for {var}...")
        create_comparison_plot(var, all_data, f"{output_dir}/{var}_comparison", 
                             show_plot, alpha_fixed)
    
    print(f"\nAll comparison plots saved to directory: {output_dir}")
    print("\nTo use this script properly, please update the DATA_DIRS dictionary")
    print("at the top of the file with the actual paths to your three data directories:")
    print("- no_adjustment: path to directory with no difficulty adjustment data")
    print("- btc_adjustment: path to directory with BTC difficulty adjustment data")
    print("- eth_adjustment: path to directory with ETH difficulty adjustment data")


if __name__ == "__main__":
    main()
