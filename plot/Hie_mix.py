import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# --- 1. Sequential Cluster-Tree Topology (hie_greedy) ---
throughput_2ghz_seq = [3.8151, 2.6064, 1.9203, 1.3749, 1.0508, 0.8428, 0.6877, 0.5970, 0.5132, 0.4498, 0.4036]
throughput_3ghz_seq = [0.4173, 0.2897, 0.1276, 0.1343, 0.0986, 0.0563, 0.0758, 0.0526, 0.0311, 0.0487, 0.0335]
throughput_4ghz_seq = [0.0750, 0.0458, 0.0316, 0.0172, 0.0165, 0.0118, 0.0101, 0.0090, 0.0062, 0.0062, 0.0047]
throughput_5ghz_seq = [0.0163, 0.0080, 0.0048, 0.0033, 0.0023, 0.0012, 0.0021, 0.0011, 0.0009, 0.0012, 0.0005]

# --- 2. Balanced Cluster-Tree Topology (hie_balance) ---
throughput_2ghz_bal = [3.9005, 2.5872, 1.9230, 1.5590, 1.2957, 1.1129, 0.9699, 0.8708, 0.7780, 0.7046, 0.6443]
throughput_3ghz_bal = [0.5221, 0.3472, 0.2382, 0.1956, 0.1652, 0.1350, 0.1199, 0.1087, 0.0942, 0.0976, 0.0794]
throughput_4ghz_bal = [0.0763, 0.0457, 0.0473, 0.0335, 0.0278, 0.0265, 0.0226, 0.0190, 0.0192, 0.0178, 0.0147]
throughput_5ghz_bal = [0.0169, 0.0098, 0.0086, 0.0066, 0.0059, 0.0040, 0.0045, 0.0034, 0.0036, 0.0031, 0.0026]


# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

# 線と凡例が多くなるため、横幅を広めに設定
plt.figure(figsize=(12, 7))

# --- プロット (Sequential Cluster: 実線 + 塗りつぶしマーカー) ---
plt.plot(users, throughput_2ghz_seq, marker='o', linestyle='-', color='blue',   label='2-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz_seq, marker='s', linestyle='-', color='orange', label='3-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz_seq, marker='^', linestyle='-', color='green',  label='4-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz_seq, marker='D', linestyle='-', color='red',    label='5-GHZ', linewidth=2, markersize=8)

# --- プロット (Balanced Cluster: 破線 + 白抜きマーカー) ---
plt.plot(users, throughput_2ghz_bal, marker='o', linestyle='--', color='blue',   markerfacecolor='white', label='2-GHZ (Optimized)', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz_bal, marker='s', linestyle='--', color='orange', markerfacecolor='white', label='3-GHZ (Optimized)', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz_bal, marker='^', linestyle='--', color='green',  markerfacecolor='white', label='4-GHZ (Optimized)', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz_bal, marker='D', linestyle='--', color='red',    markerfacecolor='white', label='5-GHZ (Optimized)', linewidth=2, markersize=8)

# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.ylabel('End-to-End Throughput (Mbps)', fontsize=14)
plt.title('Hierarchical', fontsize=16)

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