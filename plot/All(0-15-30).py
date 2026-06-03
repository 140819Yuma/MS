import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (Optimized / Balanced のみ抽出: Zenith 0, 15, 30)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users: 5から25まで1刻み)
users = list(range(5, 26))

# --- 1. Centralized (Optimized) ---
throughput_2ghz_cent = [7.8044, 6.2535, 5.2019, 4.4377, 3.8792, 3.4798, 3.1227, 2.8376, 2.5989, 2.3953, 2.2260, 2.0797, 1.9484, 1.8266, 1.7276, 1.6403, 1.5581, 1.4767, 1.4128, 1.3551, 1.2946]
throughput_3ghz_cent = [1.1664, 0.7632, 0.7799, 0.5842, 0.5683, 0.4693, 0.4669, 0.3820, 0.3897, 0.3323, 0.3259, 0.2917, 0.2917, 0.2528, 0.2589, 0.2335, 0.2292, 0.2114, 0.2115, 0.1900, 0.1938]
throughput_4ghz_cent = [0.1707, 0.1706, 0.1667, 0.1111, 0.1125, 0.1121, 0.0831, 0.0835, 0.0832, 0.0664, 0.0667, 0.0665, 0.0557, 0.0553, 0.0555, 0.0475, 0.0475, 0.0474, 0.0415, 0.0416, 0.0413]
throughput_5ghz_cent = [0.0501, 0.0231, 0.0236, 0.0235, 0.0233, 0.0156, 0.0157, 0.0154, 0.0156, 0.0116, 0.0118, 0.0117, 0.0118, 0.0091, 0.0093, 0.0094, 0.0093, 0.0078, 0.0078, 0.0077, 0.0078]

# --- 2. Chain (Optimized) ---
throughput_2ghz_chain = [7.7824, 6.1107, 5.1081, 4.3488, 3.7964, 3.0990, 2.7858, 2.7570, 2.3301, 2.1364, 2.1789, 1.8549, 1.7415, 1.7905, 1.5345, 1.4707, 1.5192, 1.3234, 1.2659, 1.3249, 1.1560]
throughput_3ghz_chain = [1.1403, 0.7583, 0.7617, 0.5690, 0.5552, 0.4571, 0.4455, 0.3693, 0.3725, 0.3188, 0.3166, 0.2778, 0.2775, 0.2470, 0.2475, 0.2219, 0.2216, 0.2022, 0.2026, 0.1852, 0.1850]
throughput_4ghz_chain = [0.1704, 0.1666, 0.1668, 0.1137, 0.1108, 0.1106, 0.0836, 0.0830, 0.0837, 0.0667, 0.0663, 0.0665, 0.0555, 0.0556, 0.0553, 0.0474, 0.0474, 0.0475, 0.0415, 0.0415, 0.0415]
throughput_5ghz_chain = [0.0500, 0.0250, 0.0250, 0.0248, 0.0230, 0.0168, 0.0166, 0.0155, 0.0155, 0.0124, 0.0115, 0.0115, 0.0115, 0.0092, 0.0093, 0.0092, 0.0092, 0.0076, 0.0076, 0.0076, 0.0076]

# --- 3. Hierarchical (Optimized) ---
throughput_2ghz_tree = [7.8332, 5.1861, 4.4520, 4.4633, 3.8847, 2.8388, 2.5898, 2.5904, 2.3972, 2.2302, 2.0778, 2.0735, 1.9476, 1.5540, 1.4794, 1.4846, 1.4134, 1.3563, 1.2961, 1.2954, 1.2446]
throughput_3ghz_tree = [0.7862, 0.7574, 0.5840, 0.5720, 0.5674, 0.3270, 0.3251, 0.3243, 0.2851, 0.2846, 0.2841, 0.2534, 0.2533, 0.2523, 0.2061, 0.2069, 0.2061, 0.1894, 0.1890, 0.1897, 0.1746]
throughput_4ghz_tree = [0.1152, 0.1127, 0.1136, 0.1118, 0.0849, 0.0856, 0.0834, 0.0786, 0.0680, 0.0667, 0.0629, 0.0628, 0.0418, 0.0388, 0.0390, 0.0390, 0.0347, 0.0353, 0.0349, 0.0349, 0.0315]
throughput_5ghz_tree = [0.0509, 0.0250, 0.0170, 0.0169, 0.0152, 0.0154, 0.0126, 0.0118, 0.0118, 0.0114, 0.0114, 0.0095, 0.0094, 0.0091, 0.0091, 0.0091, 0.0076, 0.0077, 0.0076, 0.0076, 0.0076]

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
fig.suptitle('Comparison of Optimized Topologies per GHZ State (Zenith: 0, 15, 30)', fontsize=18, y=0.98)

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
    
    # 密集を防ぐためX軸は5~25の2刻みに設定
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