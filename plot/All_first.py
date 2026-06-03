import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# --- 1. Centralized Topology ---
throughput_2ghz_cent = [3.8783, 2.5848, 1.9437, 1.5448, 1.2914, 1.1109, 0.9763, 0.8616, 0.7774, 0.7020, 0.6438]
throughput_3ghz_cent = [0.5695, 0.3839, 0.2895, 0.2308, 0.1937, 0.1661, 0.1462, 0.1291, 0.1159, 0.1052, 0.0966]
throughput_4ghz_cent = [0.0766, 0.0816, 0.0562, 0.0428, 0.0431, 0.0346, 0.0291, 0.0288, 0.0247, 0.0215, 0.0216]
throughput_5ghz_cent = [0.0166, 0.0079, 0.0077, 0.0048, 0.0048, 0.0035, 0.0035, 0.0027, 0.0027, 0.0022, 0.0021]

# --- 2. Balanced Chain Topology ---
throughput_2ghz_chain = [3.4486, 2.3180, 1.7177, 1.3969, 1.1587, 0.9996, 0.8763, 0.7755, 0.6951, 0.6360, 0.5800]
throughput_3ghz_chain = [0.5175, 0.3693, 0.2560, 0.2247, 0.1730, 0.1493, 0.1308, 0.1254, 0.1032, 0.1031, 0.0839]
throughput_4ghz_chain = [0.0758, 0.0739, 0.0530, 0.0380, 0.0311, 0.0299, 0.0253, 0.0209, 0.0191, 0.0186, 0.0154]
throughput_5ghz_chain = [0.0164, 0.0111, 0.0091, 0.0069, 0.0062, 0.0045, 0.0042, 0.0037, 0.0035, 0.0029, 0.0028]

# --- 3. Balanced Cluster-Tree Topology (Hierarchical) ---
throughput_2ghz_tree = [3.9005, 2.5872, 1.9230, 1.5590, 1.2957, 1.1129, 0.9699, 0.8708, 0.7780, 0.7046, 0.6443]
throughput_3ghz_tree = [0.5221, 0.3472, 0.2382, 0.1956, 0.1652, 0.1350, 0.1199, 0.1087, 0.0942, 0.0976, 0.0794]
throughput_4ghz_tree = [0.0763, 0.0457, 0.0473, 0.0335, 0.0278, 0.0265, 0.0226, 0.0190, 0.0192, 0.0178, 0.0147]
throughput_5ghz_tree = [0.0169, 0.0098, 0.0086, 0.0066, 0.0059, 0.0040, 0.0045, 0.0034, 0.0036, 0.0031, 0.0026]

# --- データをまとめる ---
data_2ghz = [throughput_2ghz_cent, throughput_2ghz_chain, throughput_2ghz_tree]
data_3ghz = [throughput_3ghz_cent, throughput_3ghz_chain, throughput_3ghz_tree]
data_4ghz = [throughput_4ghz_cent, throughput_4ghz_chain, throughput_4ghz_tree]
data_5ghz = [throughput_5ghz_cent, throughput_5ghz_chain, throughput_5ghz_tree]

datasets = [data_2ghz, data_3ghz, data_4ghz, data_5ghz]
titles = ['2-GHZ System Throughput', '3-GHZ System Throughput', '4-GHZ System Throughput', '5-GHZ System Throughput']

# トポロジごとの見た目設定
topologies = ['Centralized', 'Chain', 'Hierarchical']
colors = ['blue', 'orange', 'green']
markers = ['o', 's', '^']
linestyles = ['-', '--', '-.']

# ---------------------------------------------------------
# グラフの描画 (2x2 のサブプロット)
# ---------------------------------------------------------
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

fig, axs = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Comparison of Topologies per GHZ State', fontsize=18, y=0.98)

# axsを1次元配列にしてループ処理しやすくする
axs = axs.flatten()

for i in range(4):
    ax = axs[i]
    
    # 各トポロジのプロット
    for j in range(3):
        # Chain等のマーカーを白抜きにしたい場合は markerfacecolor='white' などを追加
        marker_face = 'white' if j > 0 else colors[j]
        ax.plot(users, datasets[i][j], 
                marker=markers[j], linestyle=linestyles[j], color=colors[j], markerfacecolor=marker_face,
                label=topologies[j], linewidth=2, markersize=7)

    # 軸ラベル・タイトル等の設定
    ax.set_title(titles[i], fontsize=14)
    ax.set_xlabel('Number of Users', fontsize=12)
    ax.set_ylabel('System Throughput (Mbps)', fontsize=12)
    ax.set_xticks(users)
    
    # グリッド・対数スケール・凡例
    ax.grid(True, which="both", ls="--", alpha=0.7)
    ax.set_yscale('log')
    ax.legend(fontsize=10, loc='best')

# サブプロット間の隙間を自動調整
plt.tight_layout()
# 全体タイトルのためのスペースを少し確保
plt.subplots_adjust(top=0.92)

plt.show()