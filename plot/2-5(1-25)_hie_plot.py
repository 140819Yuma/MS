import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users: 5から25まで1刻み)
users = list(range(5, 26))

# --- 1. Balanced Cluster-Tree (2-5_hie_balance.py) ---
throughput_2ghz_bal = [3.8723, 3.1153, 2.6297, 2.2213, 1.9557, 1.7291, 1.5550, 1.4127, 1.2889, 1.1982, 1.1053, 1.0376, 0.9647, 0.9197, 0.8645, 0.8118, 0.7758, 0.7377, 0.7044, 0.6761, 0.6486]
throughput_3ghz_bal = [0.5191, 0.3264, 0.3512, 0.2497, 0.2423, 0.2019, 0.1954, 0.1770, 0.1642, 0.1568, 0.1343, 0.1226, 0.1195, 0.1101, 0.1078, 0.0951, 0.0933, 0.0874, 0.0973, 0.0778, 0.0803]
throughput_4ghz_bal = [0.0767, 0.0718, 0.0465, 0.0431, 0.0482, 0.0351, 0.0338, 0.0347, 0.0277, 0.0296, 0.0265, 0.0254, 0.0226, 0.0236, 0.0188, 0.0179, 0.0192, 0.0167, 0.0177, 0.0156, 0.0147]
throughput_5ghz_bal = [0.0166, 0.0101, 0.0099, 0.0095, 0.0087, 0.0054, 0.0067, 0.0070, 0.0059, 0.0045, 0.0039, 0.0047, 0.0044, 0.0036, 0.0033, 0.0032, 0.0036, 0.0030, 0.0032, 0.0027, 0.0026]

# --- 2. Sequential Cluster-Tree [Greedy] (2-5_hie_greedy.py) ---
throughput_2ghz_seq = [3.8818, 2.1052, 2.6110, 1.3742, 1.9151, 1.0016, 1.3579, 0.7950, 1.0462, 0.6569, 0.8433, 0.5558, 0.6973, 0.4801, 0.5892, 0.4178, 0.5123, 0.3711, 0.4563, 0.3391, 0.4029]
throughput_3ghz_seq = [0.4236, 0.2201, 0.2908, 0.1802, 0.1274, 0.1710, 0.1324, 0.0727, 0.0985, 0.0915, 0.0562, 0.0730, 0.0773, 0.0409, 0.0517, 0.0594, 0.0312, 0.0386, 0.0489, 0.0271, 0.0338]
throughput_4ghz_seq = [0.0759, 0.0588, 0.0460, 0.0233, 0.0315, 0.0251, 0.0169, 0.0121, 0.0163, 0.0191, 0.0119, 0.0078, 0.0103, 0.0141, 0.0089, 0.0047, 0.0062, 0.0084, 0.0062, 0.0038, 0.0048]
throughput_5ghz_seq = [0.0169, 0.0100, 0.0081, 0.0062, 0.0047, 0.0025, 0.0033, 0.0036, 0.0024, 0.0017, 0.0012, 0.0016, 0.0022, 0.0016, 0.0010, 0.0007, 0.0009, 0.0012, 0.0012, 0.0007, 0.0005]


# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

# 線の数が多いため横幅を広めに設定
plt.figure(figsize=(12, 7))

plt.plot(users, throughput_2ghz_seq, marker='o', linestyle='--', color='blue',   label='2-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_seq, marker='s', linestyle='--', color='orange',  label='3-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_seq, marker='^', linestyle='--', color='green',   label='4-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_seq, marker='D', linestyle='--', color='red',   label='5-GHZ ', linewidth=2, markersize=6)

# --- プロット (Balanced: 実線 + 塗りつぶしマーカー) ---
plt.plot(users, throughput_2ghz_bal, marker='o', linestyle='-', color='blue',   label='2-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_bal, marker='s', linestyle='-', color='orange', label='3-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_bal, marker='^', linestyle='-', color='green',  label='4-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_bal, marker='D', linestyle='-', color='red',    label='5-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)

# --- プロット (Sequential/Greedy: 破線 + 白抜きマーカー) ---

# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.ylabel('End-to-End Throughput (Mbps)', fontsize=14)
plt.title('Hierarchical', fontsize=16)

# X軸の目盛りを設定 (1刻みの全てを表示)
plt.xticks(users, fontsize=10)

# グリッドの表示 (対数スケールに合わせ、細かいグリッドも表示)
plt.grid(True, which="both", ls="--", alpha=0.7)

# 凡例の表示 (枠外に配置)
plt.legend(fontsize=11, loc='center left', bbox_to_anchor=(1, 0.5))

# --- 対数スケールの設定 ---
plt.yscale('log')

# グラフのレイアウト調整と表示
plt.tight_layout()
plt.show()