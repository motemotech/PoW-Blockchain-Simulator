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

def get_avg_block_interval_by_delay(data_dir):
    """_w_pi.csvファイルから各delayに対応するavg_block_intervalを取得"""
    try:
        # _w_pi.csvファイルを検索
        pattern = os.path.join(data_dir, "*_w_pi.csv")
        files = glob.glob(pattern)
        
        if not files:
            print("No _w_pi.csv files found, using default avg_block_interval")
            return {}
        
        # 最初のファイルを読み込み
        w_pi_file = files[0]
        print(f"Reading avg_block_interval by delay from: {w_pi_file}")
        
        avg_block_intervals = {}
        
        with open(w_pi_file, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:  # ヘッダー行とデータ行があることを確認
                # ヘッダー行から列インデックスを取得
                header = lines[0].strip().split(',')
                try:
                    delay_idx = header.index('delay')
                    avg_block_interval_idx = header.index('avg_block_interval')
                    
                    # データ行を処理
                    for line in lines[1:]:
                        data_line = line.strip().split(',')
                        if len(data_line) > max(delay_idx, avg_block_interval_idx):
                            delay = int(data_line[delay_idx])
                            avg_block_interval = float(data_line[avg_block_interval_idx])
                            avg_block_intervals[delay] = avg_block_interval
                    
                    print(f"Found avg_block_interval for {len(avg_block_intervals)} delay values")
                    return avg_block_intervals
                    
                except (ValueError, IndexError):
                    print("Required columns not found, using default")
                    return {}
    except Exception as e:
        print(f"Error reading _w_pi.csv: {e}, using default")
        return {}

def get_avg_block_interval(data_dir):
    """_w_pi.csvファイルからavg_block_intervalを取得（後方互換性のため）"""
    avg_block_intervals = get_avg_block_interval_by_delay(data_dir)
    if avg_block_intervals:
        # 最初の値を返す（デフォルト値として使用）
        return list(avg_block_intervals.values())[0]
    return 600000  # デフォルト値

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

def plot_final_mining_shares(node_data, avg_block_intervals, output_dir="analysis"):
    """各マイナーの最終マイニングシェアをプロット（理論曲線付き）"""
    # データを整理
    delays = sorted(node_data.keys())
    print("avg_block_intervals", avg_block_intervals)
    delta_t_ratios = []
    for delay in delays:
        if delay in avg_block_intervals:
            delta_t_ratios.append(delay / avg_block_intervals[delay])
        else:
            # デフォルト値を使用
            delta_t_ratios.append(delay / 600000)
            print(f"Warning: No avg_block_interval found for delay {delay}, using default")
    
    # 各マイナーのデータを準備（上位9マイナーまで）
    miner_shares = {miner: [] for miner in range(10)}
    
    for delay in delays:
        for miner in range(10):
            if miner in node_data[delay]:
                miner_shares[miner].append(node_data[delay][miner])
            else:
                miner_shares[miner].append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # 色の設定（plot_hashrate_pie.pyと統一）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#17becf', '#bcbd22', '#ff9896']
    
    for miner in range(10):
        plt.plot(delta_t_ratios, miner_shares[miner], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[miner], label=f'miner {miner}')
    
    plt.xlabel('Δ/T', fontsize=18)
    plt.ylabel('$r_i$', fontsize=18)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=16)
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

def plot_final_mining_shares_delta(node_data, avg_block_intervals, output_dir="analysis"):
    """各マイナーの最終マイニングシェアをプロット（横軸：Δ）"""
    # データを整理
    delays = sorted(node_data.keys())
    
    # 各マイナーのデータを準備（上位9マイナーまで）
    miner_shares = {miner: [] for miner in range(10)}
    
    for delay in delays:
        for miner in range(10):
            if miner in node_data[delay]:
                miner_shares[miner].append(node_data[delay][miner])
            else:
                miner_shares[miner].append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # 色の設定（plot_hashrate_pie.pyと統一）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#17becf', '#bcbd22', '#ff9896']
    
    for miner in range(10):
        plt.plot(delays, miner_shares[miner], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[miner], label=f'miner {miner}')
    
    plt.xlabel('Δ', fontsize=18)
    plt.ylabel('$r_i$', fontsize=18)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=16)
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "final_mining_shares_delta.png")
    output_svg = os.path.join(output_dir, "final_mining_shares_delta.svg")
    output_pdf = os.path.join(output_dir, "final_mining_shares_delta.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Final mining shares plot (Δ axis) saved to: {output_png}")
    print(f"Final mining shares plot (Δ axis) saved to: {output_svg}")
    print(f"Final mining shares plot (Δ axis) saved to: {output_pdf}")
    plt.close()

def plot_miner0_with_theory(node_data, avg_block_intervals, output_dir="analysis"):
    """Miner 0の最終マイニングシェアと理論値を比較プロット"""
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = []
    for delay in delays:
        if delay in avg_block_intervals:
            delta_t_ratios.append(delay / avg_block_intervals[delay])
        else:
            # デフォルト値を使用
            delta_t_ratios.append(delay / 600000)
            print(f"Warning: No avg_block_interval found for delay {delay}, using default")
    
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
            color='#1f77b4', label='Experimental Value for miner 0')
    
    # 理論曲線用の滑らかなデータ点を生成
    if delays:
        delta_min = min(delays)
        delta_max = max(delays)
        delta_smooth = np.linspace(delta_min, delta_max, 200)
        delta_t_smooth = []
        for delta in delta_smooth:
            if delta in avg_block_intervals:
                delta_t_smooth.append(delta / avg_block_intervals[delta])
            else:
                # デフォルト値を使用
                delta_t_smooth.append(delta / 600000)
        
        # Miner 0のハッシュレート割合を計算
        hashrate_ratios = calculate_hashrate_ratios()
        miner0_hashrate_ratio = hashrate_ratios[0]
        
        # Miner 0の理論曲線を計算（αはMiner 0のハッシュレート割合を使用）
        alpha_miner0 = miner0_hashrate_ratio  # Miner 0のハッシュレート割合をαとして使用
        
        # 理論曲線を計算
        theory_shares = []
        for delta in delta_smooth:
            if delta in avg_block_intervals:
                r_A, _, _, _, _ = compute_theoretical_values(alpha_miner0, avg_block_intervals[delta], delta)
            else:
                r_A, _, _, _, _ = compute_theoretical_values(alpha_miner0, 600000, delta)
            # r_A自体がMiner 0（攻撃者）のマイニングシェア
            theory_shares.append(r_A)
        
        # 理論曲線をプロット（破線で表示）
        plt.plot(delta_t_smooth, theory_shares, 
                linestyle='--', linewidth=2.5, alpha=0.8,
                color='red', label=f'Theoretical Value for miner 0')
    
    plt.xlabel('Δ/T', fontsize=18)
    plt.ylabel('$r_0$', fontsize=18)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=16)
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

def plot_miner0_with_theory_delta(node_data, avg_block_intervals, output_dir="analysis"):
    """Miner 0の最終マイニングシェアと理論値を比較プロット（横軸：Δ）"""
    # データを整理
    delays = sorted(node_data.keys())
    
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
    plt.plot(delays, miner0_shares, 
            marker='o', linestyle='-', linewidth=2, markersize=8,
            color='#1f77b4', label='Miner 0 Experimental Value')
    
    # 理論曲線用の滑らかなデータ点を生成
    if delays:
        delta_min = min(delays)
        delta_max = max(delays)
        delta_smooth = np.linspace(delta_min, delta_max, 200)
        
        # Miner 0のハッシュレート割合を計算
        hashrate_ratios = calculate_hashrate_ratios()
        miner0_hashrate_ratio = hashrate_ratios[0]
        
        # Miner 0の理論曲線を計算（αはMiner 0のハッシュレート割合を使用）
        alpha_miner0 = miner0_hashrate_ratio  # Miner 0のハッシュレート割合をαとして使用
        
        # 理論曲線を計算
        theory_shares = []
        for delta in delta_smooth:
            if delta in avg_block_intervals:
                r_A, _, _, _, _ = compute_theoretical_values(alpha_miner0, avg_block_intervals[delta], delta)
            else:
                r_A, _, _, _, _ = compute_theoretical_values(alpha_miner0, 600000, delta)
            # r_A自体がMiner 0（攻撃者）のマイニングシェア
            theory_shares.append(r_A)
        
        # 理論曲線をプロット（破線で表示）
        plt.plot(delta_smooth, theory_shares, 
                linestyle='--', linewidth=2.5, alpha=0.8,
                color='red', label=f'Theoretical Value for α₀={alpha_miner0:.5f}')
    
    plt.xlabel('Δ', fontsize=18)
    plt.ylabel('$r_0$', fontsize=18)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=16)
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "miner0_with_theory_delta.png")
    output_svg = os.path.join(output_dir, "miner0_with_theory_delta.svg")
    output_pdf = os.path.join(output_dir, "miner0_with_theory_delta.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Miner 0 with theory plot (Δ axis) saved to: {output_png}")
    print(f"Miner 0 with theory plot (Δ axis) saved to: {output_svg}")
    print(f"Miner 0 with theory plot (Δ axis) saved to: {output_pdf}")
    plt.close()

def plot_share_vs_hashrate_ratio(node_data, avg_block_intervals, output_dir="analysis"):
    """実際のマイニングシェアとハッシュレート割合の比率をプロット（理論曲線付き）"""
    # ハッシュレート割合を計算（0-1の範囲）
    hashrate_ratios = calculate_hashrate_ratios()
    
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = []
    for delay in delays:
        if delay in avg_block_intervals:
            delta_t_ratios.append(delay / avg_block_intervals[delay])
        else:
            # デフォルト値を使用
            delta_t_ratios.append(delay / 600000)
            print(f"Warning: No avg_block_interval found for delay {delay}, using default")
    
    # 各マイナーのデータを準備（上位9マイナーまで）
    miner_ratios = {miner: [] for miner in range(10)}
    
    for delay in delays:
        for miner in range(10):
            if miner in node_data[delay]:
                # mining share: 0-1の範囲（例：0.85 = 85%）
                actual_share = node_data[delay][miner]
                # print("miner", miner, "actual_share", actual_share)
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
    
    # 色の設定（plot_hashrate_pie.pyと統一）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#17becf', '#bcbd22', '#ff9896']
    
    for miner in range(10):
        plt.plot(delta_t_ratios, miner_ratios[miner], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[miner], label=f'miner {miner}')
    
    # 1の基準線を追加（凡例には含めない）
    plt.axhline(y=1, color='black', linestyle='--', alpha=0.5)
    
    plt.xlabel('Δ/T', fontsize=18)
    plt.ylabel('$mf_i$', fontsize=18)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=16)
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

def plot_share_vs_hashrate_ratio_delta(node_data, avg_block_intervals, output_dir="analysis"):
    """実際のマイニングシェアとハッシュレート割合の比率をプロット（横軸：Δ）"""
    # ハッシュレート割合を計算（0-1の範囲）
    hashrate_ratios = calculate_hashrate_ratios()
    
    # データを整理
    delays = sorted(node_data.keys())
    
    # 各マイナーのデータを準備（上位9マイナーまで）
    miner_ratios = {miner: [] for miner in range(10)}

    for delay in delays:
        for miner in range(10):
            if miner in node_data[delay]:
                # mining share: 0-1の範囲（例：0.85 = 85%）
                actual_share = node_data[delay][miner]
                # print("miner", miner, "actual_share", actual_share)
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
    
    # 色の設定（plot_hashrate_pie.pyと統一）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#17becf', '#bcbd22', '#ff9896']
    
    for miner in range(10):
        plt.plot(delays, miner_ratios[miner], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[miner], label=f'miner {miner}')
    
    # 1の基準線を追加（凡例には含めない）
    plt.axhline(y=1, color='black', linestyle='--', alpha=0.5)
    
    plt.xlabel('Δ', fontsize=18)
    plt.ylabel('$mf_i$', fontsize=18)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=16)
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "mining_share_efficiency_delta.png")
    output_svg = os.path.join(output_dir, "mining_share_efficiency_delta.svg")
    output_pdf = os.path.join(output_dir, "mining_share_efficiency_delta.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Mining share efficiency plot (Δ axis) saved to: {output_png}")
    print(f"Mining share efficiency plot (Δ axis) saved to: {output_svg}")
    print(f"Mining share efficiency plot (Δ axis) saved to: {output_pdf}")
    plt.close()

def output_miner0_comparison_json(node_data, avg_block_intervals, output_dir="analysis"):
    """Miner 0の理論値と実験値の比較データをJSONで出力"""
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = []
    for delay in delays:
        if delay in avg_block_intervals:
            delta_t_ratios.append(delay / avg_block_intervals[delay])
        else:
            # デフォルト値を使用
            delta_t_ratios.append(delay / 600000)
            print(f"Warning: No avg_block_interval found for delay {delay}, using default")
    
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
            "avg_block_intervals": avg_block_intervals,
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
        if delay in avg_block_intervals:
            r_A, pi_A, pi_O, W_A, W_O = compute_theoretical_values(alpha_miner0, avg_block_intervals[delay], delay)
        else:
            r_A, pi_A, pi_O, W_A, W_O = compute_theoretical_values(alpha_miner0, 600000, delay)
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

def output_miners_data_json(node_data, avg_block_intervals, output_dir="analysis"):
    """マイナー0、1、9のΔ/T、r_i、mf_iをJSONで出力"""
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = []
    for delay in delays:
        if delay in avg_block_intervals:
            delta_t_ratios.append(delay / avg_block_intervals[delay])
        else:
            # デフォルト値を使用
            delta_t_ratios.append(delay / 600000)
            print(f"Warning: No avg_block_interval found for delay {delay}, using default")
    
    # ハッシュレート割合を計算
    hashrate_ratios = calculate_hashrate_ratios()
    
    # 対象マイナー
    target_miners = [0, 1, 9]
    
    # データを準備
    miners_data = {
        "metadata": {
            "avg_block_intervals": avg_block_intervals,
            "target_miners": target_miners,
            "timestamp": datetime.now().isoformat()
        },
        "miners": {}
    }
    
    for miner_id in target_miners:
        miner_data = {
            "miner_id": miner_id,
            "hashrate_ratio": hashrate_ratios[miner_id],
            "data_points": []
        }
        
        for i, delay in enumerate(delays):
            delta_t_ratio = delta_t_ratios[i]
            
            # 実験値を取得
            experimental_share = 0
            if miner_id in node_data[delay]:
                experimental_share = node_data[delay][miner_id]
            
            # mf_iを計算（実際のシェア / 期待されるシェア）
            expected_share = hashrate_ratios[miner_id]
            mf_i = 0
            if expected_share > 0:
                mf_i = experimental_share / expected_share
            
            data_point = {
                "delay": delay,
                "delta_t_ratio": delta_t_ratio,
                "r_i": experimental_share,
                "mf_i": mf_i
            }
            
            miner_data["data_points"].append(data_point)
        
        miners_data["miners"][f"miner_{miner_id}"] = miner_data
    
    # JSONファイルに保存
    output_json = os.path.join(output_dir, "miners_0_1_9_data.json")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(miners_data, f, ensure_ascii=False, indent=2)
    
    print(f"Miners 0, 1, 9 data saved to: {output_json}")
    
    # 統計情報を表示
    for miner_id in target_miners:
        miner_key = f"miner_{miner_id}"
        if miner_key in miners_data["miners"]:
            data_points = miners_data["miners"][miner_key]["data_points"]
            r_i_values = [dp["r_i"] for dp in data_points]
            mf_i_values = [dp["mf_i"] for dp in data_points]
            
            print(f"\nMiner {miner_id} Statistics:")
            print(f"  r_i range: {min(r_i_values):.6f} - {max(r_i_values):.6f}")
            print(f"  mf_i range: {min(mf_i_values):.6f} - {max(mf_i_values):.6f}")
            print(f"  avg mf_i: {np.mean(mf_i_values):.6f}")
    
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
    latest_dir = "data/real-hashrate-dist-ver2-with-dynamic-T"
    
    # avg_block_intervalを取得（delayごと）
    avg_block_intervals = get_avg_block_interval_by_delay(latest_dir)
    
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
    
    # グラフ1: 最終マイニングシェア（Δ/T軸）
    plot_final_mining_shares(node_data, avg_block_intervals, output_dir)
    
    # グラフ1b: 最終マイニングシェア（Δ軸）
    plot_final_mining_shares_delta(node_data, avg_block_intervals, output_dir)
    
    # グラフ2: Miner 0と理論値の比較（Δ/T軸）
    plot_miner0_with_theory(node_data, avg_block_intervals, output_dir)
    
    # グラフ2b: Miner 0と理論値の比較（Δ軸）
    plot_miner0_with_theory_delta(node_data, avg_block_intervals, output_dir)
    
    # グラフ3: マイニングシェア効率（Δ/T軸）
    plot_share_vs_hashrate_ratio(node_data, avg_block_intervals, output_dir)
    
    # グラフ3b: マイニングシェア効率（Δ軸）
    plot_share_vs_hashrate_ratio_delta(node_data, avg_block_intervals, output_dir)
    
    # JSON出力: Miner 0の理論値と実験値の比較
    json_output_path = output_miner0_comparison_json(node_data, avg_block_intervals, output_dir)
    
    # JSON出力: マイナー0、1、9のΔ/T、r_i、mf_iデータ
    miners_json_output_path = output_miners_data_json(node_data, avg_block_intervals, output_dir)
    
    # ハッシュレート割合を表示
    hashrate_ratios = calculate_hashrate_ratios()
    print("\nハッシュレート割合:")
    for miner in range(10):  # 上位10マイナー（0-9番）を表示
        print(f"Miner {miner}: {hashrate_ratios[miner]:.4f} ({hashrate_ratios[miner]*100:.2f}%)")
    
    print(f"\nAll plots saved to directory: {output_dir}")
    print(f"Miner 0 comparison data saved to: {json_output_path}")
    print(f"Miners 0, 1, 9 data saved to: {miners_json_output_path}")

if __name__ == "__main__":
    main()
