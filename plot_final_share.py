import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import numpy as np

# グラフのスタイルとフォントサイズを設定
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 14

# CSVファイルの一覧を取得
csv_files = glob.glob('*_plot.csv')

# プロットデータを格納するリスト
plot_data = []

# 各ファイルからデータを抽出
for file_path in csv_files:
    try:
        filename = os.path.basename(file_path)
        parts = filename.split('_')
        delta = int(parts[0])
        T = int(parts[1])
        delta_t_ratio = delta / T

        # CSVファイルを読み込み
        df = pd.read_csv(file_path, header=None, names=['block_number', 'time', 'mining_share', 'difficulty'])

        # 最後のブロックの採掘シェアを取得
        if not df.empty:
            final_mining_share = df['mining_share'].iloc[-1]
            plot_data.append({'delta_t_ratio': delta_t_ratio, 'final_share': final_mining_share})

    except (ValueError, IndexError) as e:
        print(f"Could not parse file {file_path}: {e}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred while processing {file_path}: {e}")

# データが抽出できた場合のみプロットを実行
if plot_data:
    # delta/Tの比率でデータをソート
    plot_data_sorted = sorted(plot_data, key=lambda x: x['delta_t_ratio'])

    # x軸とy軸のデータを抽出
    x_values = [data['delta_t_ratio'] for data in plot_data_sorted]
    y_values = [data['final_share'] for data in plot_data_sorted]

    # データをプロット
    plt.plot(x_values, y_values, marker='o', linestyle='-')

    # グラフの体裁を整える
    plt.title('Final Mining Share vs. $\Delta/T$', fontsize=20)
    plt.xlabel('$\Delta/T$', fontsize=16)
    plt.ylabel("Final Mining Share", fontsize=16)
    plt.grid(True)

    # グラフを画像ファイルとして保存
    output_filename = 'final_share_vs_delta_t.png'
    plt.savefig(output_filename, dpi=300)

    print(f"Graph has been saved as {output_filename}")

else:
    print("No data was found to plot.")

# # 必要に応じてグラフを表示
# plt.show()
