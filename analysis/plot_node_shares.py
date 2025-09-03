import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import numpy as np
from pathlib import Path

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

def calculate_hashrate_ratios():
    """各ノードのハッシュレート割合を計算"""
    total_hashrate = sum(HASHRATES.values()) + OTHER_NODES_HASHRATE * (100 - len(HASHRATES))
    print("total_hashrate", total_hashrate)
    
    ratios = {}
    for node in range(9):
        ratios[node] = HASHRATES[node] / total_hashrate
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
    """各ノードの最終マイニングシェアをプロット"""
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
    
    # 色の設定
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']
    
    for node in range(9):
        plt.plot(delta_t_ratios, node_shares[node], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[node], label=f'Node {node}')
    
    plt.xlabel('Δ/T', fontsize=14)
    plt.ylabel('mining share (%)', fontsize=14)
    plt.title('各ノードのマイニングシェア', fontsize=16)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # 保存
    output_path = os.path.join(output_dir, "final_mining_shares.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Final mining shares plot saved to: {output_path}")
    plt.close()

def plot_share_vs_hashrate_ratio(node_data, output_dir="analysis"):
    """実際のマイニングシェアとハッシュレート割合の比率をプロット"""
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
                # mining power: 0-1の範囲（ハッシュレート割合）
                expected_share = hashrate_ratios[node]
                if expected_share > 0:
                    # 効率性 = (実際のシェア / 期待されるシェア) * 100
                    ratio = (actual_share / expected_share) * 100
                else:
                    ratio = 0
                node_ratios[node].append(ratio)
            else:
                node_ratios[node].append(0)
    
    # グラフを作成
    plt.figure(figsize=(12, 8))
    
    # 色の設定
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']
    
    for node in range(9):
        plt.plot(delta_t_ratios, node_ratios[node], 
                marker='o', linestyle='-', linewidth=2, markersize=6,
                color=colors[node], label=f'Node {node}')
    
    # 100%の基準線を追加
    plt.axhline(y=100, color='black', linestyle='--', alpha=0.5, label='100% (期待値)')
    
    plt.xlabel('Δ/T', fontsize=14)
    plt.ylabel('mining share / mining power (%)', fontsize=14)
    plt.title('各ノードのマイニング効率性', fontsize=16)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # 保存
    output_path = os.path.join(output_dir, "mining_share_efficiency.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Mining share efficiency plot saved to: {output_path}")
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
    
    # データを収集
    node_data = collect_node_data(latest_dir)
    
    if not node_data:
        print("No node data found!")
        return
    
    print(f"Found data for {len(node_data)} different delay values")
    
    # 出力ディレクトリを作成
    output_dir = "analysis"
    os.makedirs(output_dir, exist_ok=True)
    
    # グラフ1: 最終マイニングシェア
    plot_final_mining_shares(node_data, output_dir)
    
    # グラフ2: マイニングシェア効率
    plot_share_vs_hashrate_ratio(node_data, output_dir)
    
    # ハッシュレート割合を表示
    hashrate_ratios = calculate_hashrate_ratios()
    print("\nハッシュレート割合:")
    for node in range(9):
        print(f"Node {node}: {hashrate_ratios[node]:.4f} ({hashrate_ratios[node]*100:.2f}%)")

if __name__ == "__main__":
    main()
