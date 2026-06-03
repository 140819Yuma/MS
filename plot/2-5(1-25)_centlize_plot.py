import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users: 5から25まで1刻み)
users = list(range(5, 26))

# --- 1. Centralized Balanced (2-5_centlize_balance.py) ---
throughput_2ghz_bal = [3.8987, 3.1288, 2.6092, 2.1988, 1.9342, 1.7068, 1.5641, 1.4078, 1.2952, 1.1976, 1.1109, 1.0271, 0.9690, 0.9113, 0.8620, 0.8178, 0.7740, 0.7495, 0.7068, 0.6739, 0.6483]
throughput_3ghz_bal = [0.5697, 0.3852, 0.3872, 0.2858, 0.2897, 0.2287, 0.2339, 0.1930, 0.1940, 0.1659, 0.1663, 0.1442, 0.1452, 0.1287, 0.1293, 0.1163, 0.1157, 0.1071, 0.1061, 0.0965, 0.0970]
throughput_4ghz_bal = [0.0763, 0.0811, 0.0828, 0.0551, 0.0563, 0.0557, 0.0430, 0.0428, 0.0430, 0.0345, 0.0346, 0.0345, 0.0288, 0.0288, 0.0288, 0.0247, 0.0248, 0.0251, 0.0218, 0.0215, 0.0218]
throughput_5ghz_bal = [0.0166, 0.0082, 0.0082, 0.0078, 0.0077, 0.0048, 0.0049, 0.0048, 0.0047, 0.0035, 0.0035, 0.0034, 0.0034, 0.0027, 0.0027, 0.0027, 0.0027, 0.0023, 0.0022, 0.0022, 0.0022]

# --- 2. Centralized Greedy (2-5_centlize_greedy.py) ---
throughput_2ghz_greedy = [3.8967, 3.1082, 2.6146, 2.2303, 1.9412, 1.7217, 1.5553, 1.3982, 1.2923, 1.1924, 1.1148, 1.0404, 0.9725, 0.9221, 0.8620, 0.8203, 0.7781, 0.7455, 0.7010, 0.6745, 0.6504]
throughput_3ghz_greedy = [0.4234, 0.3824, 0.2562, 0.2896, 0.1752, 0.2158, 0.1340, 0.1626, 0.1076, 0.1294, 0.0899, 0.1076, 0.0769, 0.0914, 0.0674, 0.0787, 0.0594, 0.0693, 0.0529, 0.0610, 0.0487]
throughput_4ghz_greedy = [0.0770, 0.0588, 0.0459, 0.0533, 0.0352, 0.0239, 0.0298, 0.0243, 0.0156, 0.0194, 0.0189, 0.0115, 0.0139, 0.0152, 0.0089, 0.0107, 0.0127, 0.0073, 0.0086, 0.0109, 0.0061]
throughput_5ghz_greedy = [0.0164, 0.0103, 0.0080, 0.0062, 0.0048, 0.0055, 0.0049, 0.0032, 0.0023, 0.0028, 0.0036, 0.0022, 0.0014, 0.0017, 0.0024, 0.0016, 0.0010, 0.0012, 0.0016, 0.0012, 0.0007]


# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

# 線の数が多いため横幅を広めに設定
plt.figure(figsize=(12, 7))

# --- プロット (Greedy: 破線 + 白抜きマーカー) ---
plt.plot(users, throughput_2ghz_greedy, marker='o', linestyle='--', color='blue',  label='2-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_greedy, marker='s', linestyle='--', color='orange', label='3-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_greedy, marker='^', linestyle='--', color='green',  label='4-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_greedy, marker='D', linestyle='--', color='red',     label='5-GHZ ', linewidth=2, markersize=6)

# --- プロット (Balanced: 実線 + 塗りつぶしマーカー) ---
plt.plot(users, throughput_2ghz_bal, marker='o', linestyle='-', color='blue',  markerfacecolor='white', label='2-GHZ (Optimized)', linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_bal, marker='s', linestyle='-', color='orange', markerfacecolor='white',label='3-GHZ (Optimized)', linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_bal, marker='^', linestyle='-', color='green', markerfacecolor='white', label='4-GHZ (Optimized)', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_bal, marker='D', linestyle='-', color='red',   markerfacecolor='white', label='5-GHZ (Optimized)', linewidth=2, markersize=6)

# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.ylabel('System Throughput (Mbps)', fontsize=14)
plt.title('Centralized', fontsize=16)

# X軸の目盛りを設定 (データが細かいので2刻みなどで表示すると見やすいですが、今回は1刻みの全てを表示)
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
