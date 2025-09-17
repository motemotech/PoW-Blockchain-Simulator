import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple

# ハッシュレート設定（blockchain-simulator.cppの設定Dと同じ値）
HASHRATES = {
    0: 27.9383,
    1: 15.3179,
    2: 12.4277,
    3: 10.9827,
    4: 8.47784,
    5: 4.62428,
    6: 4.04624,
    7: 3.85356,
    8: 2.40848,
    9: 1.92678
}

# 10番目以降のマイナーのハッシュレート
OTHER_MINERS_HASHRATE = 0.6

def compute_theoretical_values(alpha_a: float, T: float, Delta: float) -> Tuple[float, float, float, float, float]:
    """理論式による値を計算"""
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

def calculate_hashrate_ratios():
    """各マイナーのハッシュレート割合を計算"""
    total_hashrate = sum(HASHRATES.values()) + OTHER_MINERS_HASHRATE * (100 - len(HASHRATES))
    print("total_hashrate", total_hashrate)
    
    ratios = {}
    for miner in range(10):  # 上位10マイナー（0-9番）を扱う
        ratios[miner] = HASHRATES[miner] / 100
        print("miner", miner, "ratio", ratios[miner])
    
    return ratios

def parse_filename(filename):
    """ファイル名からパラメータを抽出"""
    # 例: node_0_BTC_6000000_100_100000_first_seen_dynamic_share.csv
    parts = filename.split('_')
    
    if len(parts) < 8:
        return None
    
    try:
        node_id = int(parts[1])
        blockchain_type = parts[2]
        delay = int(parts[3])
        node_count = int(parts[4])
        end_round = int(parts[5])
        rule = parts[6]
        difficulty = parts[7]
        
        return {
            'node_id': node_id,
            'blockchain_type': blockchain_type,
            'delay': delay,
            'node_count': node_count,
            'end_round': end_round,
            'rule': rule,
            'difficulty': difficulty
        }
    except (ValueError, IndexError):
        return None

def get_final_share_from_file(filepath):
    """ファイルから最終マイニングシェアを取得"""
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            if lines:
                # 最後の行から最終値を取得
                last_line = lines[-1].strip()
                if ':' in last_line:
                    share_str = last_line.split(':')[1].strip()
                    return float(share_str)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
    
    return None

def collect_node_data(data_dir):
    """指定されたディレクトリから各ノードのデータを収集"""
    node_files = {}
    
    # データディレクトリ内のすべてのnode_*ファイルを検索
    pattern = os.path.join(data_dir, "miner_*_BTC_*_dynamic_share.csv")
    files = glob.glob(pattern)
    
    for filepath in files:
        filename = os.path.basename(filepath)
        params = parse_filename(filename)
        
        if params is None:
            continue
            
        node_id = params['node_id']
        delay = params['delay']
        
        # 最終マイニングシェアを取得
        final_share = get_final_share_from_file(filepath)
        
        if final_share is not None:
            if delay not in node_files:
                node_files[delay] = {}
            node_files[delay][node_id] = final_share
    
    return node_files

def plot_final_mining_shares(node_data, output_dir="analysis"):
    """各マイナーの最終マイニングシェアをプロット（理論曲線付き）"""
    # BTC_TARGET_GENERATION_TIME = 600000 (config.hより)
    BTC_TARGET_GENERATION_TIME = 600000
    
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = [delay / BTC_TARGET_GENERATION_TIME for delay in delays]
    
    # 各マイナーのデータを準備（上位9マイナーまで）
    miner_shares = {miner: [] for miner in range(9)}
    
    for delay in delays:
        for miner in range(9):
            if miner in node_data[delay]:
                miner_shares[miner].append(node_data[delay][miner])
            else:
                miner_shares[miner].append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # 色の設定（より識別しやすいカラーパレット）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#17becf', '#bcbd22']  # Miner 7を水色に変更
    
    for miner in range(9):
        plt.plot(delta_t_ratios, miner_shares[miner], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[miner], label=f'Miner {miner}')
    
    plt.xlabel('Δ/T', fontsize=14)
    plt.ylabel('rᵢ (mining share)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "final_mining_shares.png")
    output_svg = os.path.join(output_dir, "final_mining_shares.svg")
    output_pdf = os.path.join(output_dir, "final_mining_shares.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Final mining shares plot saved to: {output_png}")
    print(f"Final mining shares plot saved to: {output_svg}")
    print(f"Final mining shares plot saved to: {output_pdf}")
    plt.close()

def plot_miner0_with_theory(node_data, output_dir="analysis"):
    """Miner 0の最終マイニングシェアと理論値を比較プロット"""
    # BTC_TARGET_GENERATION_TIME = 600000 (config.hより)
    BTC_TARGET_GENERATION_TIME = 600000
    
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = [delay / BTC_TARGET_GENERATION_TIME for delay in delays]
    
    # Miner 0のデータを準備
    miner0_shares = []
    for delay in delays:
        if 0 in node_data[delay]:
            miner0_shares.append(node_data[delay][0])
        else:
            miner0_shares.append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # Miner 0の実験データをプロット
    plt.plot(delta_t_ratios, miner0_shares, 
            marker='o', linestyle='-', linewidth=2, markersize=8,
            color='#1f77b4', label='Miner 0 Experimental Value')
    
    # 理論曲線用の滑らかなデータ点を生成
    if delays:
        delta_min = min(delays)
        delta_max = max(delays)
        delta_smooth = np.linspace(delta_min, delta_max, 200)
        delta_t_smooth = [delta / BTC_TARGET_GENERATION_TIME for delta in delta_smooth]
        
        # Miner 0のハッシュレート割合を計算
        hashrate_ratios = calculate_hashrate_ratios()
        miner0_hashrate_ratio = hashrate_ratios[0]
        
        # Miner 0の理論曲線を計算（αはMiner 0のハッシュレート割合を使用）
        alpha_miner0 = miner0_hashrate_ratio  # Miner 0のハッシュレート割合をαとして使用
        
        # 理論曲線を計算
        theory_shares = []
        for delta in delta_smooth:
            r_A, _, _, _, _ = compute_theoretical_values(alpha_miner0, BTC_TARGET_GENERATION_TIME, delta)
            # r_A自体がMiner 0（攻撃者）のマイニングシェア
            theory_shares.append(r_A)
        
        # 理論曲線をプロット（破線で表示）
        plt.plot(delta_t_smooth, theory_shares, 
                linestyle='--', linewidth=2.5, alpha=0.8,
                color='red', label=f'Theoretical Value for α₀={alpha_miner0:.5f}')
    
    plt.xlabel('Δ/T', fontsize=14)
    plt.ylabel('r₀ (mining share)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "miner0_with_theory.png")
    output_svg = os.path.join(output_dir, "miner0_with_theory.svg")
    output_pdf = os.path.join(output_dir, "miner0_with_theory.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Miner 0 with theory plot saved to: {output_png}")
    print(f"Miner 0 with theory plot saved to: {output_svg}")
    print(f"Miner 0 with theory plot saved to: {output_pdf}")
    plt.close()

def plot_share_vs_hashrate_ratio(node_data, output_dir="analysis"):
    """実際のマイニングシェアとハッシュレート割合の比率をプロット（理論曲線付き）"""
    # BTC_TARGET_GENERATION_TIME = 600000 (config.hより)
    BTC_TARGET_GENERATION_TIME = 600000
    
    # ハッシュレート割合を計算（0-1の範囲）
    hashrate_ratios = calculate_hashrate_ratios()
    
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = [delay / BTC_TARGET_GENERATION_TIME for delay in delays]
    
    # 各マイナーのデータを準備（上位9マイナーまで）
    miner_ratios = {miner: [] for miner in range(9)}
    
    for delay in delays:
        for miner in range(9):
            if miner in node_data[delay]:
                # mining share: 0-1の範囲（例：0.85 = 85%）
                actual_share = node_data[delay][miner]
                print("miner", miner, "actual_share", actual_share)
                # hashrate ratio: 0-1の範囲（ハッシュレート割合）
                expected_share = hashrate_ratios[miner]
                if expected_share > 0:
                    # 効率性 = (実際のシェア / 期待されるシェア)
                    ratio = actual_share / expected_share
                else:
                    ratio = 0
                miner_ratios[miner].append(ratio)
            else:
                miner_ratios[miner].append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # 色の設定（より識別しやすいカラーパレット）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#17becf', '#bcbd22']  # Miner 7を水色に変更
    
    for miner in range(9):
        plt.plot(delta_t_ratios, miner_ratios[miner], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[miner], label=f'Miner {miner}')
    
    # 1の基準線を追加（凡例には含めない）
    plt.axhline(y=1, color='black', linestyle='--', alpha=0.5)
    
    plt.xlabel('Δ/T', fontsize=14)
    plt.ylabel('rᵢ (mining share) / αᵢ (hashrate ratio)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "mining_share_efficiency.png")
    output_svg = os.path.join(output_dir, "mining_share_efficiency.svg")
    output_pdf = os.path.join(output_dir, "mining_share_efficiency.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Mining share efficiency plot saved to: {output_png}")
    print(f"Mining share efficiency plot saved to: {output_svg}")
    print(f"Mining share efficiency plot saved to: {output_pdf}")
    plt.close()

def output_miner0_comparison_json(node_data, output_dir="analysis"):
    """Miner 0の理論値と実験値の比較データをJSONで出力"""
    # BTC_TARGET_GENERATION_TIME = 600000 (config.hより)
    BTC_TARGET_GENERATION_TIME = 600000
    
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = [delay / BTC_TARGET_GENERATION_TIME for delay in delays]
    
    # Miner 0のハッシュレート割合を計算
    hashrate_ratios = calculate_hashrate_ratios()
    miner0_hashrate_ratio = hashrate_ratios[0]
    alpha_miner0 = miner0_hashrate_ratio
    
    # 比較データを準備
    comparison_data = {
        "metadata": {
            "miner_id": 0,
            "hashrate_ratio": miner0_hashrate_ratio,
            "alpha": alpha_miner0,
            "btc_target_generation_time": BTC_TARGET_GENERATION_TIME,
            "timestamp": datetime.now().isoformat()
        },
        "data_points": []
    }
    
    for i, delay in enumerate(delays):
        delta_t_ratio = delta_t_ratios[i]
        
        # 実験値を取得
        experimental_value = 0
        if 0 in node_data[delay]:
            experimental_value = node_data[delay][0]
        
        # 理論値を計算
        r_A, pi_A, pi_O, W_A, W_O = compute_theoretical_values(alpha_miner0, BTC_TARGET_GENERATION_TIME, delay)
        theoretical_value = r_A
        
        # 差分と相対誤差を計算
        difference = experimental_value - theoretical_value
        relative_error = 0
        if theoretical_value != 0:
            relative_error = (difference / theoretical_value) * 100
        
        data_point = {
            "delay": delay,
            "delta_t_ratio": delta_t_ratio,
            "experimental_value": experimental_value,
            "theoretical_value": theoretical_value,
            "difference": difference,
            "relative_error_percent": relative_error,
            "theoretical_components": {
                "r_A": r_A,
                "pi_A": pi_A,
                "pi_O": pi_O,
                "W_A": W_A,
                "W_O": W_O
            }
        }
        
        comparison_data["data_points"].append(data_point)
    
    # JSONファイルに保存
    output_json = os.path.join(output_dir, "miner0_data.json")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, ensure_ascii=False, indent=2)
    
    print(f"Miner 0 comparison data saved to: {output_json}")
    
    # 統計情報を表示
    if comparison_data["data_points"]:
        differences = [dp["difference"] for dp in comparison_data["data_points"]]
        relative_errors = [dp["relative_error_percent"] for dp in comparison_data["data_points"]]
        
        print(f"\nMiner 0 Comparison Statistics:")
        print(f"  Mean absolute difference: {np.mean(np.abs(differences)):.6f}")
        print(f"  Max absolute difference: {np.max(np.abs(differences)):.6f}")
        print(f"  Mean relative error: {np.mean(np.abs(relative_errors)):.2f}%")
        print(f"  Max relative error: {np.max(np.abs(relative_errors)):.2f}%")
    
    return output_json

def main():
    """メイン処理"""
    # 最新のデータディレクトリを自動検出
    data_dirs = glob.glob("data/*")
    if not data_dirs:
        print("No data directories found!")
        return
    
    # 最新のディレクトリを選択
    latest_dir = max(data_dirs, key=os.path.getctime)
    print(f"Using data directory: {latest_dir}")
    latest_dir = "data/20250915_184343"
    
    # データを収集
    node_data = collect_node_data(latest_dir)
    
    if not node_data:
        print("No miner data found!")
        return
    
    print(f"Found data for {len(node_data)} different delay values")
    
    # 出力ディレクトリを作成（タイムスタンプ付き）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"analysis/miner_shares_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # グラフ1: 最終マイニングシェア
    plot_final_mining_shares(node_data, output_dir)
    
    # グラフ2: Miner 0と理論値の比較
    plot_miner0_with_theory(node_data, output_dir)
    
    # グラフ3: マイニングシェア効率
    plot_share_vs_hashrate_ratio(node_data, output_dir)
    
    # JSON出力: Miner 0の理論値と実験値の比較
    json_output_path = output_miner0_comparison_json(node_data, output_dir)
    
    # ハッシュレート割合を表示
    hashrate_ratios = calculate_hashrate_ratios()
    print("\nハッシュレート割合:")
    for miner in range(10):  # 上位10マイナー（0-9番）を表示
        print(f"Miner {miner}: {hashrate_ratios[miner]:.4f} ({hashrate_ratios[miner]*100:.2f}%)")
    
    print(f"\nAll plots saved to directory: {output_dir}")
    print(f"Miner 0 comparison data saved to: {json_output_path}")

if __name__ == "__main__":
    main()
