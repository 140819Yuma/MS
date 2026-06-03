import matplotlib.pyplot as plt

# 1. シミュレーション結果のデータ入力
# 人数
users = [5, 7, 9, 11, 13, 15]

# Oldバージョン (ghz_oldmulti.py) のSKR結果 (Mbps -> Kbpsに変換)
old_skr_kbps = [
    0.1488 * 1000, 
    0.0894 * 1000, 
    0.0630 * 1000, 
    0.0479 * 1000, 
    0.0380 * 1000, 
    0.0317 * 1000
]

# 最新バージョン (ghz_multi.py) のSKR結果 (Mbps -> Kbpsに変換)
latest_skr_kbps = [
    0.2024 * 1000, 
    0.1343 * 1000, 
    0.1021 * 1000, 
    0.0822 * 1000, 
    0.0680 * 1000, 
    0.0577 * 1000
]

# 2. グラフのプロット設定
plt.figure(figsize=(10, 6))

# Oldバージョンのプロット (青色・実線)
plt.plot(users, old_skr_kbps, marker='o', linestyle='-', color='b', label='Sequential Grouping')

# 最新バージョンのプロット (赤色・破線)
plt.plot(users, latest_skr_kbps, marker='s', linestyle='--', color='r', label='Balanced Mixing')

# 3. 軸ラベルとタイトルの設定
plt.xlabel('Number of Users', fontsize=12)
plt.ylabel('System SKR (Kbps)', fontsize=12)
plt.title('Comparison of System SKR', fontsize=14)

# 4. グラフの装飾
plt.grid(True, linestyle='--', alpha=0.6) # 補助線の表示
plt.xticks(users) # X軸のメモリを人数に合わせる
plt.legend() # 凡例の表示

# 5. グラフの表示
plt.show()