import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (New Zenith Angles: 0, 15, 30)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users: 5から25まで1刻み)
users = list(range(5, 26))

# --- 1. Centralized Balanced (2-5_centlize_balance.py) ---
throughput_2ghz_bal = [7.8044, 6.2535, 5.2019, 4.4377, 3.8792, 3.4798, 3.1227, 2.8376, 2.5989, 2.3953, 2.2260, 2.0797, 1.9484, 1.8266, 1.7276, 1.6403, 1.5581, 1.4767, 1.4128, 1.3551, 1.2946]
throughput_3ghz_bal = [1.1664, 0.7632, 0.7799, 0.5842, 0.5683, 0.4693, 0.4669, 0.3820, 0.3897, 0.3323, 0.3259, 0.2917, 0.2917, 0.2528, 0.2589, 0.2335, 0.2292, 0.2114, 0.2115, 0.1900, 0.1938]
throughput_4ghz_bal = [0.1707, 0.1706, 0.1667, 0.1111, 0.1125, 0.1121, 0.0831, 0.0835, 0.0832, 0.0664, 0.0667, 0.0665, 0.0557, 0.0553, 0.0555, 0.0475, 0.0475, 0.0474, 0.0415, 0.0416, 0.0413]
throughput_5ghz_bal = [0.0501, 0.0231, 0.0236, 0.0235, 0.0233, 0.0156, 0.0157, 0.0154, 0.0156, 0.0116, 0.0118, 0.0117, 0.0118, 0.0091, 0.0093, 0.0094, 0.0093, 0.0078, 0.0078, 0.0077, 0.0078]

# --- 2. Centralized Greedy (2-5_centlize_greedy.py) ---
throughput_2ghz_greedy = [7.8333, 6.2558, 5.1850, 4.4686, 3.9093, 3.4523, 3.1249, 2.8347, 2.5963, 2.4080, 2.2259, 2.0779, 1.9365, 1.8222, 1.7261, 1.6396, 1.5553, 1.4834, 1.4138, 1.3463, 1.2982]
throughput_3ghz_greedy = [1.1461, 0.7630, 0.6937, 0.5698, 0.5233, 0.4198, 0.4185, 0.3483, 0.3481, 0.2999, 0.2967, 0.2609, 0.2605, 0.2299, 0.2322, 0.2089, 0.2080, 0.1899, 0.1890, 0.1734, 0.1735]
throughput_4ghz_greedy = [0.1720, 0.1575, 0.1522, 0.1114, 0.1049, 0.0935, 0.0764, 0.0766, 0.0698, 0.0566, 0.0558, 0.0561, 0.0464, 0.0460, 0.0466, 0.0401, 0.0397, 0.0401, 0.0351, 0.0345, 0.0350]
throughput_5ghz_greedy = [0.0501, 0.0251, 0.0234, 0.0232, 0.0204, 0.0150, 0.0157, 0.0140, 0.0125, 0.0102, 0.0101, 0.0106, 0.0093, 0.0075, 0.0075, 0.0082, 0.0074, 0.0062, 0.0063, 0.0062, 0.0063]


# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

# 線の数が多いため横幅を広めに設定
plt.figure(figsize=(12, 7))

# --- プロット (Greedy: 破線 + 白抜きマーカー) ---
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
plt.ylabel('System Throughput (Mbps)', fontsize=14)
plt.title('Centralized(Zenith angle: 0, 15, 30)', fontsize=16)

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