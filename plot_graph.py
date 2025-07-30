import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import numpy as np

# グラフのスタイルとフォントサイズを設定
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.size'] = 14

# CSVファイルの一覧を取得
csv_files = glob.glob('*_plot.csv')

# ファイル情報を格納するリスト
file_data = []

# 各ファイルからdelta/Tを計算
for file_path in csv_files:
    try:
        filename = os.path.basename(file_path)
        parts = filename.split('_')
        delta = int(parts[0])
        T = int(parts[1])
        ratio = delta / T
        file_data.append({'path': file_path, 'ratio': ratio, 'delta': delta, 'T': T})
    except (ValueError, IndexError) as e:
        print(f"Could not parse file {file_path}: {e}")

# delta/Tの比率が大きい順にソート
file_data_sorted = sorted(file_data, key=lambda x: x['ratio'], reverse=True)

# カラーマップを設定
colors = plt.cm.viridis(np.linspace(0, 1, len(file_data_sorted)))

# ソートされた順にプロット
for i, data in enumerate(file_data_sorted):
    try:
        file_path = data['path']
        # 凡例に実際の割り算の値を表示
        label = f'$\Delta/T = {data["ratio"]:.2f}$'

        # CSVファイルを読み込み
        df = pd.read_csv(file_path, header=None, names=['block_number', 'time', 'ratio', 'difficulty'])

        # データをプロット
        plt.plot(df['block_number'], df['ratio'], marker='o', linestyle='-',
                 linewidth=1.0, markersize=2, color=colors[i], label=label)

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred while plotting {file_path}: {e}")


# グラフの体裁を整える
plt.title('Proportion of Blocks Mined by Highest-Hashrate Node', fontsize=20)
plt.xlabel('Block Number', fontsize=16)
plt.ylabel("Mining Share", fontsize=16)
plt.legend(title='Conditions ($\Delta/T$)', fontsize=12)
plt.grid(True)

# グラフを画像ファイルとして保存
plt.savefig('mining_proportion_chart.png', dpi=300)

print("Graph has been saved as mining_proportion_chart.png")

# # 必要に応じてグラフを表示
# plt.show()