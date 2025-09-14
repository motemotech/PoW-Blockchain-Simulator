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

def load_w_pi_data(csv_file_path):
    """w_piデータファイルからデータを読み込み"""
    try:
        df = pd.read_csv(csv_file_path)
        return df
    except Exception as e:
        print(f"Error loading w_pi data from {csv_file_path}: {e}")
        return None

def parse_filename(filename):
    """ファイル名からパラメータを抽出"""
    # 例: miner_0_BTC_6000000_100_100000_first_seen_dynamic_share.csv
    parts = filename.split('_')
    
    if len(parts) < 8:
        return None
    
    try:
        miner_id = int(parts[1])
        blockchain_type = parts[2]
        delay = int(parts[3])
        miner_count = int(parts[4])
        end_round = int(parts[5])
        rule = parts[6]
        difficulty = parts[7]
        
        return {
            'miner_id': miner_id,
            'blockchain_type': blockchain_type,
            'delay': delay,
            'miner_count': miner_count,
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

def collect_miner_data(data_dir):
    """指定されたディレクトリから各マイナーのデータを収集"""
    miner_files = {}
    
    # データディレクトリ内のすべてのminer_*ファイルを検索
    pattern = os.path.join(data_dir, "miner_*_BTC_*_dynamic_share.csv")
    files = glob.glob(pattern)
    
    for filepath in files:
        filename = os.path.basename(filepath)
        params = parse_filename(filename)
        
        if params is None:
            continue
            
        miner_id = params['miner_id']
        delay = params['delay']
        
        # 最終マイニングシェアを取得
        final_share = get_final_share_from_file(filepath)
        
        if final_share is not None:
            if delay not in miner_files:
                miner_files[delay] = {}
            miner_files[delay][miner_id] = final_share
    
    return miner_files

def plot_final_mining_shares_dynamic_t(miner_data, w_pi_data, output_dir="analysis"):
    """各マイナーの最終マイニングシェアをプロット（動的T値使用）"""
    
    # w_piデータから遅延とavg_block_intervalの対応を作成
    delay_to_avg_interval = {}
    for _, row in w_pi_data.iterrows():
        delay = int(row['delay'])
        avg_interval = float(row['avg_block_interval'])
        delay_to_avg_interval[delay] = avg_interval
    
    # データを整理
    delays = sorted(miner_data.keys())
    delta_t_ratios = []
    
    for delay in delays:
        if delay in delay_to_avg_interval:
            avg_interval = delay_to_avg_interval[delay]
            delta_t_ratio = delay / avg_interval
            delta_t_ratios.append(delta_t_ratio)
        else:
            print(f"Warning: No avg_block_interval found for delay {delay}")
            delta_t_ratios.append(0)
    
    # 各マイナーのデータを準備（上位9マイナーまで）
    miner_shares = {miner: [] for miner in range(9)}
    
    for delay in delays:
        for miner in range(9):
            if miner in miner_data[delay]:
                miner_shares[miner].append(miner_data[delay][miner])
            else:
                miner_shares[miner].append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # 色の設定（より識別しやすいカラーパレット）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#17becf', '#bcbd22']
    
    for miner in range(9):
        plt.plot(delta_t_ratios, miner_shares[miner], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[miner], label=f'miner {miner}')
    
    plt.xlabel('Δ/T', fontsize=14)
    plt.ylabel('rᵢ', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "final_mining_shares_dynamic_t.png")
    output_svg = os.path.join(output_dir, "final_mining_shares_dynamic_t.svg")
    output_pdf = os.path.join(output_dir, "final_mining_shares_dynamic_t.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Final mining shares (dynamic T) plot saved to: {output_png}")
    print(f"Final mining shares (dynamic T) plot saved to: {output_svg}")
    print(f"Final mining shares (dynamic T) plot saved to: {output_pdf}")
    plt.close()

def plot_miner0_with_theory_dynamic_t(miner_data, w_pi_data, output_dir="analysis"):
    """Miner 0の最終マイニングシェアと理論値を比較プロット（動的T値使用）"""
    
    # w_piデータから遅延とavg_block_intervalの対応を作成
    delay_to_avg_interval = {}
    for _, row in w_pi_data.iterrows():
        delay = int(row['delay'])
        avg_interval = float(row['avg_block_interval'])
        delay_to_avg_interval[delay] = avg_interval
    
    # データを整理
    delays = sorted(miner_data.keys())
    delta_t_ratios = []
    
    for delay in delays:
        if delay in delay_to_avg_interval:
            avg_interval = delay_to_avg_interval[delay]
            delta_t_ratio = delay / avg_interval
            delta_t_ratios.append(delta_t_ratio)
        else:
            print(f"Warning: No avg_block_interval found for delay {delay}")
            delta_t_ratios.append(0)
    
    # Miner 0のデータを準備
    miner0_shares = []
    for delay in delays:
        if 0 in miner_data[delay]:
            miner0_shares.append(miner_data[delay][0])
        else:
            miner0_shares.append(0)
    
    # Miner 0のハッシュレート割合を取得
    hashrate_ratios = calculate_hashrate_ratios()
    miner0_hashrate_ratio = hashrate_ratios[0]
    
    # JSONデータを作成（Miner 0の詳細データ）
    miner0_data = []
    for i, (delta_t_ratio, r_0) in enumerate(zip(delta_t_ratios, miner0_shares)):
        r_0_over_alpha_0 = r_0 / miner0_hashrate_ratio if miner0_hashrate_ratio > 0 else 0
        miner0_data.append({
            "delta_t_ratio": float(delta_t_ratio),
            "r_0": float(r_0),
            "r_0_over_alpha_0": float(r_0_over_alpha_0),
            "alpha_0": float(miner0_hashrate_ratio),
            "delay": int(delays[i]) if i < len(delays) else 0
        })
    
    # JSONファイルに保存
    json_output_path = os.path.join(output_dir, "miner0_data.json")
    with open(json_output_path, 'w') as f:
        json.dump(miner0_data, f, indent=2, ensure_ascii=False)
    print(f"Miner 0 data saved to: {json_output_path}")
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # Miner 0の実験データをプロット
    plt.plot(delta_t_ratios, miner0_shares, 
            marker='o', linestyle='-', linewidth=2, markersize=8,
            color='#1f77b4', label='miner 0 Experimental Value')
    
    # 理論曲線用の滑らかなデータ点を生成
    if delays and delta_t_ratios:
        delta_t_min = min(delta_t_ratios)
        delta_t_max = max(delta_t_ratios)
        delta_t_smooth = np.linspace(delta_t_min, delta_t_max, 200)
        
        # Miner 0のハッシュレート割合を計算
        hashrate_ratios = calculate_hashrate_ratios()
        miner0_hashrate_ratio = hashrate_ratios[0]
        
        # 理論曲線を計算（動的T値を使用）
        theory_shares = []
        for delta_t_ratio in delta_t_smooth:
            # 任意のT値（例：平均値）を使用してΔを計算
            avg_t = np.mean([delay_to_avg_interval[d] for d in delays if d in delay_to_avg_interval])
            delta = delta_t_ratio * avg_t
            r_A, _, _, _, _ = compute_theoretical_values(miner0_hashrate_ratio, avg_t, delta)
            theory_shares.append(r_A)
        
        # 理論曲線をプロット（破線で表示）
        plt.plot(delta_t_smooth, theory_shares, 
                linestyle='--', linewidth=2.5, alpha=0.8,
                color='red', label=f'Theoretical Value for α₀={miner0_hashrate_ratio:.5f}')
    
    plt.xlabel('Δ/T', fontsize=14)
    plt.ylabel('r₀', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "miner0_with_theory_dynamic_t.png")
    output_svg = os.path.join(output_dir, "miner0_with_theory_dynamic_t.svg")
    output_pdf = os.path.join(output_dir, "miner0_with_theory_dynamic_t.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Miner 0 with theory (dynamic T) plot saved to: {output_png}")
    print(f"Miner 0 with theory (dynamic T) plot saved to: {output_svg}")
    print(f"Miner 0 with theory (dynamic T) plot saved to: {output_pdf}")
    plt.close()

def plot_share_vs_hashrate_ratio_dynamic_t(miner_data, w_pi_data, output_dir="analysis"):
    """実際のマイニングシェアとハッシュレート割合の比率をプロット（動的T値使用）"""
    
    # w_piデータから遅延とavg_block_intervalの対応を作成
    delay_to_avg_interval = {}
    for _, row in w_pi_data.iterrows():
        delay = int(row['delay'])
        avg_interval = float(row['avg_block_interval'])
        delay_to_avg_interval[delay] = avg_interval
    
    # ハッシュレート割合を計算（0-1の範囲）
    hashrate_ratios = calculate_hashrate_ratios()
    
    # データを整理
    delays = sorted(miner_data.keys())
    delta_t_ratios = []
    
    for delay in delays:
        if delay in delay_to_avg_interval:
            avg_interval = delay_to_avg_interval[delay]
            delta_t_ratio = delay / avg_interval
            delta_t_ratios.append(delta_t_ratio)
        else:
            print(f"Warning: No avg_block_interval found for delay {delay}")
            delta_t_ratios.append(0)
    
    # 各マイナーのデータを準備（上位9マイナーまで）
    miner_ratios = {miner: [] for miner in range(9)}
    
    for delay in delays:
        for miner in range(9):
            if miner in miner_data[delay]:
                # mining share: 0-1の範囲（例：0.85 = 85%）
                actual_share = miner_data[delay][miner]
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
              '#8c564b', '#e377c2', '#17becf', '#bcbd22']
    
    for miner in range(9):
        plt.plot(delta_t_ratios, miner_ratios[miner], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[miner], label=f'miner {miner}')
    
    # 1の基準線を追加（凡例には含めない）
    plt.axhline(y=1, color='black', linestyle='--', alpha=0.5)
    
    plt.xlabel('Δ/T', fontsize=14)
    plt.ylabel('MPRᵢ', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "mining_share_efficiency_dynamic_t.png")
    output_svg = os.path.join(output_dir, "mining_share_efficiency_dynamic_t.svg")
    output_pdf = os.path.join(output_dir, "mining_share_efficiency_dynamic_t.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Mining share efficiency (dynamic T) plot saved to: {output_png}")
    print(f"Mining share efficiency (dynamic T) plot saved to: {output_svg}")
    print(f"Mining share efficiency (dynamic T) plot saved to: {output_pdf}")
    plt.close()

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
    latest_dir = "data/real-hashrate-dist-ver2-with-dynamic-T"
    
    # w_piデータを読み込み
    w_pi_file = os.path.join(latest_dir, "BTC_1000_100000_first_seen_dynamic_w_pi.csv")
    w_pi_data = load_w_pi_data(w_pi_file)
    
    if w_pi_data is None:
        print("Failed to load w_pi data!")
        return
    
    print(f"Loaded w_pi data with {len(w_pi_data)} entries")
    
    # マイナーデータを収集
    miner_data = collect_miner_data(latest_dir)
    
    if not miner_data:
        print("No miner data found!")
        return
    
    print(f"Found data for {len(miner_data)} different delay values")
    
    # 出力ディレクトリを作成（タイムスタンプ付き）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"analysis/miner_shares_dynamic_t_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # グラフ1: 最終マイニングシェア（動的T値使用）
    plot_final_mining_shares_dynamic_t(miner_data, w_pi_data, output_dir)
    
    # グラフ2: Miner 0と理論値の比較（動的T値使用）
    plot_miner0_with_theory_dynamic_t(miner_data, w_pi_data, output_dir)
    
    # グラフ3: マイニングシェア効率（動的T値使用）
    plot_share_vs_hashrate_ratio_dynamic_t(miner_data, w_pi_data, output_dir)
    
    # ハッシュレート割合を表示
    hashrate_ratios = calculate_hashrate_ratios()
    print("\nハッシュレート割合:")
    for miner in range(10):  # 上位10マイナー（0-9番）を表示
        print(f"miner {miner}: {hashrate_ratios[miner]:.4f} ({hashrate_ratios[miner]*100:.2f}%)")
    
    print(f"\nAll plots saved to directory: {output_dir}")

if __name__ == "__main__":
    main()
