import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# --- 1. Full Qiskit System Throughput (Centralized / Default) ---
throughput_2ghz_cent = [3.8783, 2.5848, 1.9437, 1.5448, 1.2914, 1.1109, 0.9763, 0.8616, 0.7774, 0.7020, 0.6438]
throughput_3ghz_cent = [0.5695, 0.3839, 0.2895, 0.2308, 0.1937, 0.1661, 0.1462, 0.1291, 0.1159, 0.1052, 0.0966]
throughput_4ghz_cent = [0.0766, 0.0816, 0.0562, 0.0428, 0.0431, 0.0346, 0.0291, 0.0288, 0.0247, 0.0215, 0.0216]
throughput_5ghz_cent = [0.0166, 0.0079, 0.0077, 0.0048, 0.0048, 0.0035, 0.0035, 0.0027, 0.0027, 0.0022, 0.0021]

# --- 2. Full Qiskit System Throughput (Greedy Star Topology) ---
throughput_2ghz_greedy = [3.8975, 2.5933, 1.9513, 1.5624, 1.2921, 1.1126, 0.9775, 0.8659, 0.7782, 0.7028, 0.6427]
throughput_3ghz_greedy = [0.4258, 0.2534, 0.1754, 0.1331, 0.1077, 0.0900, 0.0774, 0.0668, 0.0599, 0.0534, 0.0482]
throughput_4ghz_greedy = [0.0769, 0.0452, 0.0351, 0.0295, 0.0157, 0.0188, 0.0140, 0.0089, 0.0129, 0.0086, 0.0060]
throughput_5ghz_greedy = [0.0167, 0.0081, 0.0049, 0.0049, 0.0023, 0.0035, 0.0014, 0.0024, 0.0010, 0.0016, 0.0007]


# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

# 線が多くなるため、横幅を広めに設定
plt.figure(figsize=(12, 7))

# --- プロット (Default: 実線 + 塗りつぶしマーカー) ---
# --- プロット (Greedy: 破線 + 白抜きマーカー) ---
plt.plot(users, throughput_2ghz_greedy, marker='o', linestyle='--', color='blue',   label='2-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz_greedy, marker='s', linestyle='--', color='orange',label='3-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz_greedy, marker='^', linestyle='--', color='green',  label='4-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz_greedy, marker='D', linestyle='--', color='red',   label='5-GHZ', linewidth=2, markersize=8)

plt.plot(users, throughput_2ghz_cent, marker='o', linestyle='-', color='blue',   markerfacecolor='white',label='2-GHZ (Optimized)', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz_cent, marker='s', linestyle='-', color='orange', markerfacecolor='white',label='3-GHZ (Optimized)', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz_cent, marker='^', linestyle='-', color='green',  markerfacecolor='white',label='4-GHZ (Optimized)', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz_cent, marker='D', linestyle='-', color='red',    markerfacecolor='white',label='5-GHZ (Optimized)', linewidth=2, markersize=8)


# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.ylabel('System Throughput (Mbps)', fontsize=14)
plt.title('Centralized', fontsize=16)

# X軸の目盛りを明示的に設定 (5から25まで)
plt.xticks(users)

# グリッドの表示 (対数スケールに合わせ、細かいグリッドも表示)
plt.grid(True, which="both", ls="--", alpha=0.7)

# 凡例の表示 (枠外に配置して見やすくする)
plt.legend(fontsize=11, loc='center left', bbox_to_anchor=(1, 0.5))

# --- 対数スケールの設定 ---
plt.yscale('log')

# グラフのレイアウト調整と表示
plt.tight_layout()
plt.show()