import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Tuple

# ハッシュレート設定（washiblock.cppと同じ値）
HASHRATES = {
    0: 16.534,
    1: 12.56,
    2: 11.288,
    3: 2.226,
    4: 1.272,
    5: 0.636,
    6: 0.318,
    7: 0.318,
    8: 0.159
}

# 9番目以降のノードのハッシュレート
OTHER_NODES_HASHRATE = 0.6

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
    """各ノードのハッシュレート割合を計算"""
    total_hashrate = sum(HASHRATES.values()) + OTHER_NODES_HASHRATE * (100 - len(HASHRATES))
    print("total_hashrate", total_hashrate)
    
    ratios = {}
    for node in range(9):
        ratios[node] = HASHRATES[node] / 100
        print("node", node, "ratio", ratios[node])
    
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
    pattern = os.path.join(data_dir, "node_*_BTC_*_dynamic_share.csv")
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
    """各ノードの最終マイニングシェアをプロット（理論曲線付き）"""
    # BTC_TARGET_GENERATION_TIME = 600000 (config.hより)
    BTC_TARGET_GENERATION_TIME = 600000
    
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = [delay / BTC_TARGET_GENERATION_TIME for delay in delays]
    
    # 各ノードのデータを準備
    node_shares = {node: [] for node in range(9)}
    
    for delay in delays:
        for node in range(9):
            if node in node_data[delay]:
                node_shares[node].append(node_data[delay][node])
            else:
                node_shares[node].append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # 色の設定（より識別しやすいカラーパレット）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#17becf', '#bcbd22']  # Node 7を水色に変更
    
    for node in range(9):
        plt.plot(delta_t_ratios, node_shares[node], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[node], label=f'Node {node}')
    
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

def plot_node0_with_theory(node_data, output_dir="analysis"):
    """Node 0の最終マイニングシェアと理論値を比較プロット"""
    # BTC_TARGET_GENERATION_TIME = 600000 (config.hより)
    BTC_TARGET_GENERATION_TIME = 600000
    
    # データを整理
    delays = sorted(node_data.keys())
    delta_t_ratios = [delay / BTC_TARGET_GENERATION_TIME for delay in delays]
    
    # Node 0のデータを準備
    node0_shares = []
    for delay in delays:
        if 0 in node_data[delay]:
            node0_shares.append(node_data[delay][0])
        else:
            node0_shares.append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # Node 0の実験データをプロット
    plt.plot(delta_t_ratios, node0_shares, 
            marker='o', linestyle='-', linewidth=2, markersize=8,
            color='#1f77b4', label='Node 0 Experimental Value')
    
    # 理論曲線用の滑らかなデータ点を生成
    if delays:
        delta_min = min(delays)
        delta_max = max(delays)
        delta_smooth = np.linspace(delta_min, delta_max, 200)
        delta_t_smooth = [delta / BTC_TARGET_GENERATION_TIME for delta in delta_smooth]
        
        # Node 0のハッシュレート割合を計算
        hashrate_ratios = calculate_hashrate_ratios()
        node0_hashrate_ratio = hashrate_ratios[0]
        
        # Node 0の理論曲線を計算（αはNode 0のハッシュレート割合を使用）
        alpha_node0 = node0_hashrate_ratio  # Node 0のハッシュレート割合をαとして使用
        
        # 理論曲線を計算
        theory_shares = []
        for delta in delta_smooth:
            r_A, _, _, _, _ = compute_theoretical_values(alpha_node0, BTC_TARGET_GENERATION_TIME, delta)
            # r_A自体がNode 0（攻撃者）のマイニングシェア
            theory_shares.append(r_A)
        
        # 理論曲線をプロット（破線で表示）
        plt.plot(delta_t_smooth, theory_shares, 
                linestyle='--', linewidth=2.5, alpha=0.8,
                color='red', label=f'Theoretical Value for α₀={alpha_node0:.5f}')
    
    plt.xlabel('Δ/T', fontsize=14)
    plt.ylabel('r₀ (mining share)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    plt.tight_layout()
    
    # 保存（PNG、SVG、PDF形式）
    output_png = os.path.join(output_dir, "node0_with_theory.png")
    output_svg = os.path.join(output_dir, "node0_with_theory.svg")
    output_pdf = os.path.join(output_dir, "node0_with_theory.pdf")
    
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.savefig(output_svg, format='svg', bbox_inches='tight')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    
    print(f"Node 0 with theory plot saved to: {output_png}")
    print(f"Node 0 with theory plot saved to: {output_svg}")
    print(f"Node 0 with theory plot saved to: {output_pdf}")
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
    
    # 各ノードのデータを準備
    node_ratios = {node: [] for node in range(9)}
    
    for delay in delays:
        for node in range(9):
            if node in node_data[delay]:
                # mining share: 0-1の範囲（例：0.85 = 85%）
                actual_share = node_data[delay][node]
                print("node", node, "actual_share", actual_share)
                # hashrate ratio: 0-1の範囲（ハッシュレート割合）
                expected_share = hashrate_ratios[node]
                if expected_share > 0:
                    # 効率性 = (実際のシェア / 期待されるシェア)
                    ratio = actual_share / expected_share
                else:
                    ratio = 0
                node_ratios[node].append(ratio)
            else:
                node_ratios[node].append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # 色の設定（より識別しやすいカラーパレット）
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#17becf', '#bcbd22']  # Node 7を水色に変更
    
    for node in range(9):
        plt.plot(delta_t_ratios, node_ratios[node], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[node], label=f'Node {node}')
    
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
    latest_dir = "data/real-hashrate-dist"
    
    # データを収集
    node_data = collect_node_data(latest_dir)
    
    if not node_data:
        print("No node data found!")
        return
    
    print(f"Found data for {len(node_data)} different delay values")
    
    # 出力ディレクトリを作成（タイムスタンプ付き）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"analysis/node_shares_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # グラフ1: 最終マイニングシェア
    plot_final_mining_shares(node_data, output_dir)
    
    # グラフ2: Node 0と理論値の比較
    plot_node0_with_theory(node_data, output_dir)
    
    # グラフ3: マイニングシェア効率
    plot_share_vs_hashrate_ratio(node_data, output_dir)
    
    # ハッシュレート割合を表示
    hashrate_ratios = calculate_hashrate_ratios()
    print("\nハッシュレート割合:")
    for node in range(9):
        print(f"Node {node}: {hashrate_ratios[node]:.4f} ({hashrate_ratios[node]*100:.2f}%)")
    
    print(f"\nAll plots saved to directory: {output_dir}")

if __name__ == "__main__":
    main()
