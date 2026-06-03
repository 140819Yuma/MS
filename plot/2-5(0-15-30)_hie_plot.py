import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (New Zenith Angles: 0, 15, 30)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users: 5から25まで1刻み)
users = list(range(5, 26))

# --- 1. Balanced Cluster-Tree (2-5_hie_balance.py) ---
throughput_2ghz_bal = [7.8332, 5.1861, 4.4520, 4.4633, 3.8847, 2.8388, 2.5898, 2.5904, 2.3972, 2.2302, 2.0778, 2.0735, 1.9476, 1.5540, 1.4794, 1.4846, 1.4134, 1.3563, 1.2961, 1.2954, 1.2446]
throughput_3ghz_bal = [0.7862, 0.7574, 0.5840, 0.5720, 0.5674, 0.3270, 0.3251, 0.3243, 0.2851, 0.2846, 0.2841, 0.2534, 0.2533, 0.2523, 0.2061, 0.2069, 0.2061, 0.1894, 0.1890, 0.1897, 0.1746]
throughput_4ghz_bal = [0.1152, 0.1127, 0.1136, 0.1118, 0.0849, 0.0856, 0.0834, 0.0786, 0.0680, 0.0667, 0.0629, 0.0628, 0.0418, 0.0388, 0.0390, 0.0390, 0.0347, 0.0353, 0.0349, 0.0349, 0.0315]
throughput_5ghz_bal = [0.0509, 0.0250, 0.0170, 0.0169, 0.0152, 0.0154, 0.0126, 0.0118, 0.0118, 0.0114, 0.0114, 0.0095, 0.0094, 0.0091, 0.0091, 0.0091, 0.0076, 0.0077, 0.0076, 0.0076, 0.0076]

# --- 2. Sequential Cluster-Tree (2-5_hie_greedy.py) ---
throughput_2ghz_seq = [7.8177, 5.5593, 5.0991, 3.9738, 3.4901, 3.0884, 2.8009, 2.5270, 2.3152, 2.1415, 1.9883, 1.8614, 1.7401, 1.6423, 1.5484, 1.4630, 1.3897, 1.3253, 1.2625, 1.2096, 1.1626]
throughput_3ghz_seq = [1.1425, 0.6758, 0.5586, 0.5202, 0.4642, 0.4058, 0.4181, 0.3103, 0.2656, 0.2906, 0.2661, 0.2340, 0.2340, 0.2081, 0.1877, 0.1880, 0.1698, 0.1555, 0.1560, 0.1556, 0.1442]
throughput_4ghz_seq = [0.1702, 0.1558, 0.1526, 0.0995, 0.0743, 0.0780, 0.0701, 0.0624, 0.0543, 0.0596, 0.0559, 0.0503, 0.0417, 0.0420, 0.0456, 0.0357, 0.0314, 0.0313, 0.0311, 0.0311, 0.0279]
throughput_5ghz_seq = [0.0498, 0.0249, 0.0233, 0.0229, 0.0204, 0.0133, 0.0109, 0.0108, 0.0106, 0.0094, 0.0083, 0.0073, 0.0080, 0.0081, 0.0075, 0.0068, 0.0056, 0.0056, 0.0061, 0.0062, 0.0056]


# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

# 線の数が多いため横幅を広めに設定
plt.figure(figsize=(12, 7))

# --- プロット (Sequential/Greedy: 破線 + 白抜きマーカー) ---
plt.plot(users, throughput_2ghz_seq, marker='o', linestyle='--', color='blue',   label='2-GHZ (Sequential)', linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_seq, marker='s', linestyle='--', color='orange',  label='3-GHZ (Sequential)', linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_seq, marker='^', linestyle='--', color='green',   label='4-GHZ (Sequential)', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_seq, marker='D', linestyle='--', color='red',     label='5-GHZ (Sequential)', linewidth=2, markersize=6)

# --- プロット (Balanced: 実線 + 塗りつぶしマーカー) ---
plt.plot(users, throughput_2ghz_bal, marker='o', linestyle='-', color='blue',   label='2-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_bal, marker='s', linestyle='-', color='orange', label='3-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_bal, marker='^', linestyle='-', color='green',  label='4-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_bal, marker='D', linestyle='-', color='red',    label='5-GHZ (Optimized)', markerfacecolor='white', linewidth=2, markersize=6)


# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.ylabel('End-to-End Throughput (Mbps)', fontsize=14)
plt.title('Hierarchical(Zenith: 0, 15, 30)', fontsize=16)

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