import matplotlib.pyplot as plt

# ---------------------------------------------------------
# データ定義 (Full Qiskit System Throughput)
# ---------------------------------------------------------
# 横軸: ユーザー数 (Number of Users)
users = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]

# 縦軸: 各プロトコルのシステムスループット (Mbps)
throughput_2ghz = [3.6412, 2.4311, 1.8045, 1.4625, 1.2059, 1.0320, 0.9047, 0.8040, 0.7246, 0.6555, 0.6054]
throughput_3ghz = [0.5321, 0.3603, 0.2687, 0.2186, 0.1798, 0.1543, 0.1354, 0.1210, 0.1085, 0.0983, 0.0907]
throughput_4ghz = [0.0711, 0.0775, 0.0523, 0.0405, 0.0402, 0.0322, 0.0269, 0.0271, 0.0231, 0.0203, 0.0204]
throughput_5ghz = [0.0157, 0.0074, 0.0070, 0.0046, 0.0044, 0.0032, 0.0032, 0.0026, 0.0025, 0.0020, 0.0020]

# ---------------------------------------------------------
# グラフの描画
# ---------------------------------------------------------
# フォントやスタイルの設定
plt.style.use('default')
plt.rcParams["font.family"] = "Times New Roman"

plt.figure(figsize=(10, 6))

# 各プロトコルの折れ線グラフをプロット
plt.plot(users, throughput_2ghz, marker='o', color='blue',   label='2-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_3ghz, marker='s', color='orange', label='3-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_4ghz, marker='^', color='green',  label='4-GHZ', linewidth=2, markersize=8)
plt.plot(users, throughput_5ghz, marker='D', color='red',    label='5-GHZ', linewidth=2, markersize=8)

# 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=14)
plt.ylabel('System Throughput (Mbps)', fontsize=14)
plt.title('Full Qiskit System Throughput vs Number of Users', fontsize=16)

# X軸の目盛りを明示的に設定 (5から25まで)
plt.xticks(users)

# グリッドの表示 (対数スケールに合わせ、細かいグリッドも表示)
plt.grid(True, which="both", ls="--", alpha=0.7)

# 凡例の表示
plt.legend(fontsize=12)

# --- 対数スケールの設定 ---
# スループットの値が広い範囲(3.6〜0.002)にまたがるため対数スケールを使用
plt.yscale('log')
plt.ylabel('System Throughput (Mbps) [Log Scale]', fontsize=14)

# グラフのレイアウト調整と表示
plt.tight_layout()
plt.show()