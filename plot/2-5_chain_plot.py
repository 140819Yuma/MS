import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (Full Qiskit System Throughput - Chain Topology)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# 縦軸: 各プロトコルのシステムスループット (Mbps)
throughput_2ghz = [2.8530, 1.6929, 1.1814, 0.8821, 0.7150, 0.6020, 0.5139, 0.4509, 0.3956, 0.3536, 0.3280]
throughput_3ghz = [0.3825, 0.2022, 0.1287, 0.0908, 0.0696, 0.0564, 0.0459, 0.0397, 0.0342, 0.0301, 0.0272]
throughput_4ghz = [0.0557, 0.0405, 0.0213, 0.0130, 0.0115, 0.0082, 0.0062, 0.0058, 0.0046, 0.0038, 0.0037]
throughput_5ghz = [0.0167, 0.0058, 0.0043, 0.0022, 0.0018, 0.0012, 0.0010, 0.0007, 0.0007, 0.0005, 0.0005]

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
plt.title('Chain Topology End-to-End Throughput vs Number of Users', fontsize=16)

# X軸の目盛りを明示的に設定 (5から25まで)
plt.xticks(users)

# グリッドの表示 (対数スケールに合わせ、細かいグリッドも表示)
plt.grid(True, which="both", ls="--", alpha=0.7)

# 凡例の表示
plt.legend(fontsize=12)

# --- 対数スケールの設定 ---
plt.yscale('log')
plt.ylabel('End-to-End Throughput (Mbps) [Log Scale]', fontsize=14)

# グラフのレイアウト調整と表示
plt.tight_layout()
plt.show()