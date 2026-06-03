import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (Balanced Chain Topology End-to-End Throughput)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# 縦軸: 各プロトコルのシステムスループット (Mbps)
throughput_2ghz = [3.4486, 2.3180, 1.7177, 1.3969, 1.1587, 0.9996, 0.8763, 0.7755, 0.6951, 0.6360, 0.5800]
throughput_3ghz = [0.5175, 0.3693, 0.2560, 0.2247, 0.1730, 0.1493, 0.1308, 0.1254, 0.1032, 0.1031, 0.0839]
throughput_4ghz = [0.0758, 0.0739, 0.0530, 0.0380, 0.0311, 0.0299, 0.0253, 0.0209, 0.0191, 0.0186, 0.0154]
throughput_5ghz = [0.0164, 0.0111, 0.0091, 0.0069, 0.0062, 0.0045, 0.0042, 0.0037, 0.0035, 0.0029, 0.0028]

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
plt.title('Balanced Chain Topology End-to-End Throughput vs Number of Users', fontsize=16)

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