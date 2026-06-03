import matplotlib.pyplot as plt

# データの準備
altitudes = [18, 20, 22, 24, 26, 28, 30]
throughput = [0.4774, 0.4624, 0.4481, 0.4300, 0.4048, 0.3898, 0.3674]

# グラフの設定
plt.figure(figsize=(8, 5))
plt.plot(altitudes, throughput, marker='o', linestyle='-', color='b')

# タイトルと軸ラベルの設定
plt.xlabel('HAP Altitude [km]', fontsize=12)
plt.ylabel('SKR [Mbps]', fontsize=12)

# グリッドとレイアウトの調整
plt.grid(True, linestyle='--', alpha=0.7)
plt.xticks(altitudes)
plt.ylim(0.3, 0.5) # 変化を見やすくするために範囲を調整



plt.legend()
plt.tight_layout()

# 表示
plt.show()