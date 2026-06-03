import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# --- 1. Chain Topology (Default) ---
throughput_2ghz_chain = [2.8530, 1.6929, 1.1814, 0.8821, 0.7150, 0.6020, 0.5139, 0.4509, 0.3956, 0.3536, 0.3280]
throughput_3ghz_chain = [0.3825, 0.2022, 0.1287, 0.0908, 0.0696, 0.0564, 0.0459, 0.0397, 0.0342, 0.0301, 0.0272]
throughput_4ghz_chain = [0.0557, 0.0405, 0.0213, 0.0130, 0.0115, 0.0082, 0.0062, 0.0058, 0.0046, 0.0038, 0.0037]
throughput_5ghz_chain = [0.0167, 0.0058, 0.0043, 0.0022, 0.0018, 0.0012, 0.0010, 0.0007, 0.0007, 0.0005, 0.0005]

# --- 2. Balanced Chain Topology ---
throughput_2ghz_bal = [3.4486, 2.3180, 1.7177, 1.3969, 1.1587, 0.9996, 0.8763, 0.7755, 0.6951, 0.6360, 0.5800]
throughput_3ghz_bal = [0.5175, 0.3693, 0.2560, 0.2247, 0.1730, 0.1493, 0.1308, 0.1254, 0.1032, 0.1031, 0.0839]
throughput_4ghz_bal = [0.0758, 0.0739, 0.0530, 0.0380, 0.0311, 0.0299, 0.0253, 0.0209, 0.0191, 0.0186, 0.0154]
throughput_5ghz_bal = [0.0164, 0.0111, 0.0091, 0.0069, 0.0062, 0.0045, 0.0042, 0.0037, 0.0035, 0.0029, 0.0028]


# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

# 線が多くなるため、横幅を広めに設定
plt.figure(figsize=(12, 7))

# --- プロット (Default Chain: 実線 + 塗りつぶしマーカー) ---
plt.plot(users, throughput_2ghz_chain, marker='o', linestyle='-', color='blue',   label='2-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz_chain, marker='s', linestyle='-', color='orange', label='3-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz_chain, marker='^', linestyle='-', color='green',  label='4-GHZ ', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz_chain, marker='D', linestyle='-', color='red',    label='5-GHZ', linewidth=2, markersize=8)

# --- プロット (Balanced Chain: 破線 + 白抜きマーカー) ---
plt.plot(users, throughput_2ghz_bal, marker='o', linestyle='--', color='blue',  markerfacecolor='white',label='2-GHZ (Optimized)', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz_bal, marker='s', linestyle='--', color='orange',  markerfacecolor='white',label='3-GHZ (Optimized)', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz_bal, marker='^', linestyle='--', color='green',  markerfacecolor='white',label='4-GHZ (Optimized)', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz_bal, marker='D', linestyle='--', color='red',     markerfacecolor='white',label='5-GHZ (Optimized)', linewidth=2, markersize=8)

# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.ylabel('End-to-End Throughput (Mbps)', fontsize=14)
plt.title('Chain', fontsize=16)

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