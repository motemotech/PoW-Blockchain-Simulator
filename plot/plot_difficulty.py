
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- 設定 ---
CSV_FILE = '4500000_600000_100000_plot.csv'
OUTPUT_FILENAME = 'difficulty_vs_share_chart_4500000.svg'
# ------------

# グラフのスタイルとフォントサイズを設定
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (15, 8)
plt.rcParams['font.size'] = 14

# CSVファイルが存在するか確認
if not os.path.exists(CSV_FILE):
    print(f"エラー: ファイル '{CSV_FILE}' が見つかりません。")
    exit()

# CSVファイルを読み込み (ヘッダーなし)
column_names = ['block_number', 'time', 'mining_share', 'difficulty']
df = pd.read_csv(CSV_FILE, header=None, names=column_names)

# グラフ描画エリアを作成
fig, ax1 = plt.subplots()

# 1つ目のY軸（左側）：マイニング割合
color1 = '#000080'  # Navy
ax1.set_xlabel('Block Number', fontsize=16)
ax1.set_ylabel("Highest-Hashrate Node's Mining Share", color=color1, fontsize=16)
ax1.plot(df['block_number'], df['mining_share'], color=color1, linewidth=1.5, label='Mining Share')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.grid(True, which='both', linestyle='--', linewidth=0.5)

# 2つ目のY軸（右側）：難易度
ax2 = ax1.twinx()  # 1つ目のY軸とX軸を共有
color2 = '#D2691E'  # Burnt Orange
ax2.set_ylabel('Chain Difficulty', color=color2, fontsize=16)
ax2.plot(df['block_number'], df['difficulty'], color=color2, linewidth=1.5, linestyle='--', label='Difficulty')
ax2.tick_params(axis='y', labelcolor=color2)

# グラフのタイトルと凡例
plt.title('Mining Share and Chain Difficulty vs. Block Number', fontsize=20, pad=20)
fig.tight_layout()  # レイアウトを調整

# グラフをSVGファイルとして保存
plt.savefig(OUTPUT_FILENAME, format='svg')

print(f"グラフが '{OUTPUT_FILENAME}' として保存されました。")
