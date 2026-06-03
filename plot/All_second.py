import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (Optimized / Balanced のみ抽出)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users: 5から25まで1刻み)
users = list(range(5, 26))

# --- 1. Centralized (Optimized) ---
throughput_2ghz_cent = [3.8987, 3.1288, 2.6092, 2.1988, 1.9342, 1.7068, 1.5641, 1.4078, 1.2952, 1.1976, 1.1109, 1.0271, 0.9690, 0.9113, 0.8620, 0.8178, 0.7740, 0.7495, 0.7068, 0.6739, 0.6483]
throughput_3ghz_cent = [0.5697, 0.3852, 0.3872, 0.2858, 0.2897, 0.2287, 0.2339, 0.1930, 0.1940, 0.1659, 0.1663, 0.1442, 0.1452, 0.1287, 0.1293, 0.1163, 0.1157, 0.1071, 0.1061, 0.0965, 0.0970]
throughput_4ghz_cent = [0.0763, 0.0811, 0.0828, 0.0551, 0.0563, 0.0557, 0.0430, 0.0428, 0.0430, 0.0345, 0.0346, 0.0345, 0.0288, 0.0288, 0.0288, 0.0247, 0.0248, 0.0251, 0.0218, 0.0215, 0.0218]
throughput_5ghz_cent = [0.0166, 0.0082, 0.0082, 0.0078, 0.0077, 0.0048, 0.0049, 0.0048, 0.0047, 0.0035, 0.0035, 0.0034, 0.0034, 0.0027, 0.0027, 0.0027, 0.0027, 0.0023, 0.0022, 0.0022, 0.0022]

# --- 2. Chain (Optimized) ---
throughput_2ghz_chain = [3.4579, 2.8867, 2.3028, 2.0636, 1.7377, 1.5803, 1.3942, 1.4046, 1.1638, 1.0941, 0.9874, 0.9498, 0.8724, 0.8188, 0.7728, 0.7403, 0.6881, 0.6646, 0.6263, 0.6081, 0.5773]
throughput_3ghz_chain = [0.5206, 0.3602, 0.3661, 0.2713, 0.2595, 0.2130, 0.2232, 0.1683, 0.1742, 0.1528, 0.1475, 0.1426, 0.1303, 0.1162, 0.1258, 0.1127, 0.1023, 0.0910, 0.1016, 0.0942, 0.0832]
throughput_4ghz_chain = [0.0765, 0.0800, 0.0733, 0.0523, 0.0535, 0.0423, 0.0374, 0.0358, 0.0314, 0.0309, 0.0294, 0.0253, 0.0251, 0.0244, 0.0206, 0.0223, 0.0188, 0.0177, 0.0187, 0.0166, 0.0154]
throughput_5ghz_chain = [0.0166, 0.0100, 0.0111, 0.0101, 0.0092, 0.0063, 0.0068, 0.0063, 0.0062, 0.0051, 0.0044, 0.0048, 0.0043, 0.0036, 0.0037, 0.0034, 0.0034, 0.0031, 0.0029, 0.0030, 0.0028]

# --- 3. Hierarchical (Optimized) ---
throughput_2ghz_tree = [3.8723, 3.1153, 2.6297, 2.2213, 1.9557, 1.7291, 1.5550, 1.4127, 1.2889, 1.1982, 1.1053, 1.0376, 0.9647, 0.9197, 0.8645, 0.8118, 0.7758, 0.7377, 0.7044, 0.6761, 0.6486]
throughput_3ghz_tree = [0.5191, 0.3264, 0.3512, 0.2497, 0.2423, 0.2019, 0.1954, 0.1770, 0.1642, 0.1568, 0.1343, 0.1226, 0.1195, 0.1101, 0.1078, 0.0951, 0.0933, 0.0874, 0.0973, 0.0778, 0.0803]
throughput_4ghz_tree = [0.0767, 0.0718, 0.0465, 0.0431, 0.0482, 0.0351, 0.0338, 0.0347, 0.0277, 0.0296, 0.0265, 0.0254, 0.0226, 0.0236, 0.0188, 0.0179, 0.0192, 0.0167, 0.0177, 0.0156, 0.0147]
throughput_5ghz_tree = [0.0166, 0.0101, 0.0099, 0.0095, 0.0087, 0.0054, 0.0067, 0.0070, 0.0059, 0.0045, 0.0039, 0.0047, 0.0044, 0.0036, 0.0033, 0.0032, 0.0036, 0.0030, 0.0032, 0.0027, 0.0026]

# --- データをまとめる ---
data_2ghz = [throughput_2ghz_cent, throughput_2ghz_chain, throughput_2ghz_tree]
data_3ghz = [throughput_3ghz_cent, throughput_3ghz_chain, throughput_3ghz_tree]
data_4ghz = [throughput_4ghz_cent, throughput_4ghz_chain, throughput_4ghz_tree]
data_5ghz = [throughput_5ghz_cent, throughput_5ghz_chain, throughput_5ghz_tree]

datasets = [data_2ghz, data_3ghz, data_4ghz, data_5ghz]
titles = ['2-GHZ System Throughput (Optimized)', 
          '3-GHZ System Throughput (Optimized)', 
          '4-GHZ System Throughput (Optimized)', 
          '5-GHZ System Throughput (Optimized)']

# トポロジごとの見た目設定
topologies = ['Centralized', 'Chain', 'Hierarchical']
colors = ['blue', 'orange', 'green']
markers = ['o', 's', '^']

# ---------------------------------------------------------
# グラフの描画 (2x2 のサブプロット)
# ---------------------------------------------------------
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

fig, axs = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Comparison of Optimized Topologies per GHZ State', fontsize=18, y=0.98)

# axsを1次元配列にしてループ処理しやすくする
axs = axs.flatten()

for i in range(4):
    ax = axs[i]
    
    # 各トポロジのプロット
    for j in range(3):
        ax.plot(users, datasets[i][j], 
                marker=markers[j], linestyle='-', color=colors[j], markerfacecolor='white',
                label=topologies[j], linewidth=2, markersize=7)

    # 軸ラベル・タイトル等の設定
    ax.set_title(titles[i], fontsize=14)
    ax.set_xlabel('Number of Users', fontsize=12)
    ax.set_ylabel('End-to-End Throughput (Mbps)', fontsize=12)
    
    # メモリが細かすぎる場合は、2刻みや5刻みに調整（今回は見やすさ重視で5~25の2刻み）
    ax.set_xticks(range(5, 26, 2))
    
    # グリッド・対数スケール・凡例
    ax.grid(True, which="both", ls="--", alpha=0.7)
    ax.set_yscale('log')
    ax.legend(fontsize=10, loc='best')

# サブプロット間の隙間を自動調整
plt.tight_layout()
# 全体タイトルのためのスペースを少し確保
plt.subplots_adjust(top=0.92)

plt.show()