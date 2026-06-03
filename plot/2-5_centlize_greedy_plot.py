import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (Full Qiskit System Throughput - Greedy Star Topology)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# 縦軸: 各プロトコルのシステムスループット (Mbps)
throughput_2ghz = [3.8975, 2.5933, 1.9513, 1.5624, 1.2921, 1.1126, 0.9775, 0.8659, 0.7782, 0.7028, 0.6427]
throughput_3ghz = [0.4258, 0.2534, 0.1754, 0.1331, 0.1077, 0.0900, 0.0774, 0.0668, 0.0599, 0.0534, 0.0482]
throughput_4ghz = [0.0769, 0.0452, 0.0351, 0.0295, 0.0157, 0.0188, 0.0140, 0.0089, 0.0129, 0.0086, 0.0060]
throughput_5ghz = [0.0167, 0.0081, 0.0049, 0.0049, 0.0023, 0.0035, 0.0014, 0.0024, 0.0010, 0.0016, 0.0007]

# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

plt.figure(figsize=(10, 6))

# 各プロトコルの折れ線グラフをプロット
plt.plot(users, throughput_2ghz, marker='o', color='blue',   label='2-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz, marker='s', color='orange', label='3-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz, marker='^', color='green',  label='4-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz, marker='D', color='red',    label='5-GHZ', linewidth=2, markersize=8)

# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.title('Full Qiskit System Throughput (Greedy) vs Number of Users', fontsize=16)

# X軸の目盛りを明示的に設定 (5から25まで)
plt.xticks(users)

# グリッドの表示 (対数スケールに合わせ、細かいグリッドも表示)
plt.grid(True, which="both", ls="--", alpha=0.7)

# 凡例の表示
plt.legend(fontsize=12)

# --- 対数スケールの設定 ---
plt.yscale('log')
plt.ylabel('System Throughput (Mbps) [Log Scale]', fontsize=14)

# グラフのレイアウト調整と表示
plt.tight_layout()
plt.show()