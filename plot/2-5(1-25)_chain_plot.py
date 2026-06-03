import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users: 5から25まで1刻み)
users = list(range(5, 26))

# --- 1. Balanced Chain (2-5_chain_balance.py) ---
throughput_2ghz_bal = [3.4579, 2.8867, 2.3028, 2.0636, 1.7377, 1.5803, 1.3942, 1.4046, 1.1638, 1.0941, 0.9874, 0.9498, 0.8724, 0.8188, 0.7728, 0.7403, 0.6881, 0.6646, 0.6263, 0.6081, 0.5773]
throughput_3ghz_bal = [0.5206, 0.3602, 0.3661, 0.2713, 0.2595, 0.2130, 0.2232, 0.1683, 0.1742, 0.1528, 0.1475, 0.1426, 0.1303, 0.1162, 0.1258, 0.1127, 0.1023, 0.0910, 0.1016, 0.0942, 0.0832]
throughput_4ghz_bal = [0.0765, 0.0800, 0.0733, 0.0523, 0.0535, 0.0423, 0.0374, 0.0358, 0.0314, 0.0309, 0.0294, 0.0253, 0.0251, 0.0244, 0.0206, 0.0223, 0.0188, 0.0177, 0.0187, 0.0166, 0.0154]
throughput_5ghz_bal = [0.0166, 0.0100, 0.0111, 0.0101, 0.0092, 0.0063, 0.0068, 0.0063, 0.0062, 0.0051, 0.0044, 0.0048, 0.0043, 0.0036, 0.0037, 0.0034, 0.0034, 0.0031, 0.0029, 0.0030, 0.0028]

# --- 2. Greedy Chain (2-5_chain_greedy.py) ---
throughput_2ghz_greedy = [2.8374, 2.1225, 1.6907, 1.3869, 1.1682, 1.0150, 0.8943, 0.7924, 0.7233, 0.6596, 0.5931, 0.5517, 0.5150, 0.4765, 0.4491, 0.4184, 0.3951, 0.3757, 0.3563, 0.3388, 0.3237]
throughput_3ghz_greedy = [0.3807, 0.2225, 0.2029, 0.1387, 0.1289, 0.0965, 0.0912, 0.0723, 0.0704, 0.0585, 0.0556, 0.0478, 0.0464, 0.0402, 0.0395, 0.0348, 0.0341, 0.0304, 0.0299, 0.0273, 0.0272]
throughput_4ghz_greedy = [0.0555, 0.0468, 0.0408, 0.0238, 0.0212, 0.0193, 0.0132, 0.0122, 0.0116, 0.0087, 0.0081, 0.0078, 0.0062, 0.0059, 0.0057, 0.0047, 0.0046, 0.0045, 0.0039, 0.0038, 0.0037]
throughput_5ghz_greedy = [0.0166, 0.0068, 0.0058, 0.0050, 0.0044, 0.0024, 0.0022, 0.0020, 0.0019, 0.0013, 0.0012, 0.0011, 0.0010, 0.0008, 0.0007, 0.0007, 0.0007, 0.0005, 0.0005, 0.0005, 0.0005]


# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

# 線の数が多いため横幅を広めに設定
plt.figure(figsize=(12, 7))

# --- プロット (Greedy: 破線 + 白抜きマーカー) ---
plt.plot(users, throughput_2ghz_greedy, marker='o', linestyle='--', color='blue',    label='2-GHZ', linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_greedy, marker='s', linestyle='--', color='orange', label='3-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_greedy, marker='^', linestyle='--', color='green',  label='4-GHZ ', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_greedy, marker='D', linestyle='--', color='red',    label='5-GHZ ', linewidth=2, markersize=6)

# --- プロット (Balanced: 実線 + 塗りつぶしマーカー) ---
plt.plot(users, throughput_2ghz_bal, marker='o', linestyle='-', color='blue',   label='2-GHZ (Optimized)', markerfacecolor='white',linewidth=2, markersize=6)
plt.plot(users, throughput_3ghz_bal, marker='s', linestyle='-', color='orange', label='3-GHZ (Optimized)', markerfacecolor='white',linewidth=2, markersize=6)
plt.plot(users, throughput_4ghz_bal, marker='^', linestyle='-', color='green',  label='4-GHZ (Optimized)',markerfacecolor='white', linewidth=2, markersize=6)
plt.plot(users, throughput_5ghz_bal, marker='D', linestyle='-', color='red',    label='5-GHZ (Optimized)', markerfacecolor='white',linewidth=2, markersize=6)


# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.ylabel('End-to-End Throughput (Mbps) [Log Scale]', fontsize=14)
plt.title('Comparison: Chain Balanced vs Chain Greedy Topology', fontsize=16)

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