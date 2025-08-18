import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import numpy as np

def get_plot_data(file_list):
    """指定されたファイルリストからプロットデータを抽出する"""
    plot_data = []
    for file_path in file_list:
        try:
            filename = os.path.basename(file_path)
            # ファイル名からサフィックスを除去してベース名を取得
            if filename.endswith('_static_plot.csv'):
                base_filename = filename.removesuffix('_static_plot.csv')
            else:
                base_filename = filename.removesuffix('_plot.csv')
            
            parts = base_filename.split('_')
            delta = int(parts[0])
            T = int(parts[1])
            delta_t_ratio = delta / T

            df = pd.read_csv(file_path, header=None, names=['block_number', 'time', 'mining_share', 'difficulty'])

            if not df.empty:
                final_mining_share = df['mining_share'].iloc[-1]
                plot_data.append({'delta_t_ratio': delta_t_ratio, 'final_share': final_mining_share})

        except (ValueError, IndexError, FileNotFoundError) as e:
            print(f"Could not process file {file_path}: {e}")
    
    return sorted(plot_data, key=lambda x: x['delta_t_ratio'])

# --- メイン処理 ---

# グラフのスタイルとフォントサイズを設定
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 14

# CSVファイルを2種類に分類する
all_csv_files = glob.glob('*_plot.csv')
static_files = [f for f in all_csv_files if f.endswith('_static_plot.csv')]
dynamic_files = [f for f in all_csv_files if not f.endswith('_static_plot.csv')]

# データを取得
plot_data_dynamic = get_plot_data(dynamic_files)
plot_data_static = get_plot_data(static_files)

# グラフを作成
fig, ax = plt.subplots()

# 難易度調整ありのデータ（青）をプロット
if plot_data_dynamic:
    x_dynamic = [data['delta_t_ratio'] for data in plot_data_dynamic]
    y_dynamic = [data['final_share'] for data in plot_data_dynamic]
    ax.plot(x_dynamic, y_dynamic, marker='o', linestyle='None', color='blue', label='With Difficulty Adjustment')
    print(f"Plotted {len(x_dynamic)} data points with difficulty adjustment.")

# 難易度調整なしのデータ（赤）をプロット
if plot_data_static:
    x_static = [data['delta_t_ratio'] for data in plot_data_static]
    y_static = [data['final_share'] for data in plot_data_static]
    ax.plot(x_static, y_static, marker='x', linestyle='None', color='red', label='Without Difficulty Adjustment (Static)')
    print(f"Plotted {len(x_static)} data points without difficulty adjustment.")

# グラフの体裁を整える
ax.set_title('Final Mining Share vs. $\Delta/T$', fontsize=20)
ax.set_xlabel('$\Delta/T$', fontsize=16)
ax.set_ylabel("Final Mining Share", fontsize=16)
ax.grid(True)

# 凡例を表示して画像を保存
if plot_data_dynamic or plot_data_static:
    ax.legend(fontsize=12)
    output_filename = 'final_share_comparison.png'
    plt.savefig(output_filename, dpi=300)
    print(f"Graph has been saved as {output_filename}")
else:
    print("No data was found to plot.")

# # 必要に応じてグラフを表示
# plt.show()