import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (Full Qiskit System Throughput - Centralized)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# 縦軸: 各プロトコルのシステムスループット (Mbps)
throughput_2ghz = [3.8783, 2.5848, 1.9437, 1.5448, 1.2914, 1.1109, 0.9763, 0.8616, 0.7774, 0.7020, 0.6438]
throughput_3ghz = [0.5695, 0.3839, 0.2895, 0.2308, 0.1937, 0.1661, 0.1462, 0.1291, 0.1159, 0.1052, 0.0966]
throughput_4ghz = [0.0766, 0.0816, 0.0562, 0.0428, 0.0431, 0.0346, 0.0291, 0.0288, 0.0247, 0.0215, 0.0216]
throughput_5ghz = [0.0166, 0.0079, 0.0077, 0.0048, 0.0048, 0.0035, 0.0035, 0.0027, 0.0027, 0.0022, 0.0021]

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
# plt.ylabel('System Throughput (Mbps)', fontsize=14)
plt.title('Full Qiskit System Throughput vs Number of Users', fontsize=16)

# X軸の目盛りを明示的に設定 (5から25まで)
plt.xticks(users)

# グリッドの表示 (対数スケールに合わせ、細かいグリッドも表示)
plt.grid(True, which="both", ls="--", alpha=0.7)

# 凡例の表示
plt.legend(fontsize=12)

# --- 対数スケールの設定 ---
# スループットの値が広い範囲にまたがるため対数スケールを使用
plt.yscale('log')
plt.ylabel('System Throughput (Mbps) [Log Scale]', fontsize=14)

# グラフのレイアウト調整と表示
plt.tight_layout()
plt.show()