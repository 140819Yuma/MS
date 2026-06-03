import matplotlib.pyplot as plt
import numpy as np

# 1. パラメータの設定
# nの値のリスト (0, 1, 2, 3)
n_values = [0, 1, 2, 3]

# ラムダの値 (0から3まで0.1刻み)
# arangeは終端を含まないため、3.0を含めるために3.1としています
lambda_values = np.arange(0, 3.1, 0.1)

# 2. 数式 P(n) の定義
def calculate_P(n, lam):
    # 数式: ((n + 1) * lambda^n) / (1 + lambda)^(n + 2)
    numerator = (n + 1) * (lam ** n)
    denominator = (1 + lam) ** (n + 2)
    return numerator / denominator

# 3. グラフの描画設定
plt.figure(figsize=(10, 6))  # グラフのサイズ指定

# 各nについてプロットを作成
for n in n_values:
    # 対応するP(n)の値を計算
    p_values = calculate_P(n, lambda_values)
    
    # プロット (線とマーカーを表示)
    plt.plot(lambda_values, p_values, label=f'n = {n}', marker='.', markersize=5)

# 4. ラベルとタイトルの設定
plt.title(r'Graph of $P(n) = \frac{(n+1)\lambda^n}{(1+\lambda)^{n+2}}$')
plt.xlabel(r'$\lambda$ (lambda)')
plt.ylabel(r'$P(n)$')
plt.legend()       # 凡例を表示
plt.grid(True)     # グリッドを表示

# グラフの表示
plt.show()