import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (Sequential Cluster-Tree End-to-End Throughput)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# 縦軸: 各プロトコルのシステムスループット (Mbps)
throughput_2ghz = [3.8151, 2.6064, 1.9203, 1.3749, 1.0508, 0.8428, 0.6877, 0.5970, 0.5132, 0.4498, 0.4036]
throughput_3ghz = [0.4173, 0.2897, 0.1276, 0.1343, 0.0986, 0.0563, 0.0758, 0.0526, 0.0311, 0.0487, 0.0335]
throughput_4ghz = [0.0750, 0.0458, 0.0316, 0.0172, 0.0165, 0.0118, 0.0101, 0.0090, 0.0062, 0.0062, 0.0047]
throughput_5ghz = [0.0163, 0.0080, 0.0048, 0.0033, 0.0023, 0.0012, 0.0021, 0.0011, 0.0009, 0.0012, 0.0005]

# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

plt.figure(figsize=(10, 6))

# 各プロトコルの折れ線グラフをプロット
plt.plot(users, throughput_2ghz, marker='o', color='blue',   label='2-GHZ Clst', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz, marker='s', color='orange', label='3-GHZ Clst', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz, marker='^', color='green',  label='4-GHZ Clst', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz, marker='D', color='red',    label='5-GHZ Clst', linewidth=2, markersize=8)

# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.title('Sequential Cluster-Tree End-to-End Throughput vs Number of Users', fontsize=16)

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