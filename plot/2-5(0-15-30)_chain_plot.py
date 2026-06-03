import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (New Zenith Angles: 0, 15, 30)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users: 5から25まで1刻み)
users = list(range(5, 26))

# --- 1. Balanced Chain (2-5_chain_balance.py) ---
throughput_2ghz_bal = [7.7824, 6.1107, 5.1081, 4.3488, 3.7964, 3.0990, 2.7858, 2.7570, 2.3301, 2.1364, 2.1789, 1.8549, 1.7415, 1.7905, 1.5345, 1.4707, 1.5192, 1.3234, 1.2659, 1.3249, 1.1560]
throughput_3ghz_bal = [1.1403, 0.7583, 0.7617, 0.5690, 0.5552, 0.4571, 0.4455, 0.3693, 0.3725, 0.3188, 0.3166, 0.2778, 0.2775, 0.2470, 0.2475, 0.2219, 0.2216, 0.2022, 0.2026, 0.1852, 0.1850]
throughput_4ghz_bal = [0.1704, 0.1666, 0.1668, 0.1137, 0.1108, 0.1106, 0.0836, 0.0830, 0.0837, 0.0667, 0.0663, 0.0665, 0.0555, 0.0556, 0.0553, 0.0474, 0.0474, 0.0475, 0.0415, 0.0415, 0.0415]
throughput_5ghz_bal = [0.0500, 0.0250, 0.0250, 0.0248, 0.0230, 0.0168, 0.0166, 0.0155, 0.0155, 0.0124, 0.0115, 0.0115, 0.0115, 0.0092, 0.0093, 0.0092, 0.0092, 0.0076, 0.0076, 0.0076, 0.0076]

# --- 2. Greedy Chain (2-5_chain_greedy.py) ---
throughput_2ghz_greedy = [7.5895, 5.5880, 4.6499, 3.9947, 3.4866, 3.1000, 2.7861, 2.5340, 2.3046, 2.1362, 1.9904, 1.8488, 1.7365, 1.6306, 1.5501, 1.4648, 1.3910, 1.3239, 1.2670, 1.2078, 1.1585]
throughput_3ghz_greedy = [1.1066, 0.6799, 0.6797, 0.5106, 0.4674, 0.3732, 0.3733, 0.3104, 0.3095, 0.2659, 0.2674, 0.2312, 0.2335, 0.2060, 0.2089, 0.1868, 0.1862, 0.1692, 0.1702, 0.1550, 0.1555]
throughput_4ghz_greedy = [0.1653, 0.1494, 0.1490, 0.0992, 0.0911, 0.0906, 0.0683, 0.0625, 0.0623, 0.0499, 0.0502, 0.0497, 0.0416, 0.0413, 0.0421, 0.0357, 0.0356, 0.0357, 0.0314, 0.0311, 0.0311]
throughput_5ghz_greedy = [0.0498, 0.0223, 0.0226, 0.0218, 0.0201, 0.0133, 0.0133, 0.0122, 0.0122, 0.0092, 0.0085, 0.0083, 0.0083, 0.0066, 0.0068, 0.0067, 0.0067, 0.0056, 0.0056, 0.0055, 0.0056]


# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

# 線の数が多いため横幅を広めに設定
plt.figure(figsize=(12, 7))

plt.plot(users, throughput_2ghz_greedy, marker='o', linestyle='--', color='blue',   label='2-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_greedy, marker='s', linestyle='--', color='orange',  label='3-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_greedy, marker='^', linestyle='--', color='green',   label='4-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_greedy, marker='D', linestyle='--', color='red',    label='5-GHZ ', linewidth=2, markersize=6)

# --- プロット (Balanced: 実線 + 塗りつぶしマーカー) ---
plt.plot(users, throughput_2ghz_bal, marker='o', linestyle='-', color='blue',   label='2-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_bal, marker='s', linestyle='-', color='orange', label='3-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_bal, marker='^', linestyle='-', color='green',  label='4-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_bal, marker='D', linestyle='-', color='red',    label='5-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)

# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.ylabel('End-to-End Throughput (Mbps)', fontsize=14)
plt.title('Chain(Zenith: 0, 15, 30)', fontsize=16)

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