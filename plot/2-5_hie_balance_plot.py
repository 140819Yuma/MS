import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (Balanced Cluster-Tree End-to-End Throughput)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# 縦軸: 各プロトコルのシステムスループット (Mbps)
throughput_2ghz = [3.9005, 2.5872, 1.9230, 1.5590, 1.2957, 1.1129, 0.9699, 0.8708, 0.7780, 0.7046, 0.6443]
throughput_3ghz = [0.5221, 0.3472, 0.2382, 0.1956, 0.1652, 0.1350, 0.1199, 0.1087, 0.0942, 0.0976, 0.0794]
throughput_4ghz = [0.0763, 0.0457, 0.0473, 0.0335, 0.0278, 0.0265, 0.0226, 0.0190, 0.0192, 0.0178, 0.0147]
throughput_5ghz = [0.0169, 0.0098, 0.0086, 0.0066, 0.0059, 0.0040, 0.0045, 0.0034, 0.0036, 0.0031, 0.0026]

# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

plt.figure(figsize=(10, 6))

# 各プロトコルの折れ線グラフをプロット
plt.plot(users, throughput_2ghz, marker='o', color='blue',   label='2-GHZ Bal-Clst', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz, marker='s', color='orange', label='3-GHZ Bal-Clst', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz, marker='^', color='green',  label='4-GHZ Bal-Clst', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz, marker='D', color='red',    label='5-GHZ Bal-Clst', linewidth=2, markersize=8)

# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.title('Balanced Cluster-Tree End-to-End Throughput vs Number of Users', fontsize=16)

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